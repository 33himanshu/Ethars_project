"""
Prometheus Metrics + OpenTelemetry Instrumentation
----------------------------------------------------
Tracks:
- p95 retrieval latency (target < 500ms)
- p95 end-to-end response latency (target < 2000ms)
- Hallucination rate (target < 5%)
- Retrieval precision@5 (target > 0.80)
- Token usage per query
- Failed ingestion rate
"""
import time
import logging
from functools import wraps
from typing import Callable

from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY,
)
from fastapi import Request, Response
from fastapi.routing import APIRoute
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Prometheus Metrics ────────────────────────────────────────────────────────

# Latency histograms
RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_latency_seconds",
    "Time spent in retrieval pipeline",
    buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 2.0, 5.0],
)

E2E_LATENCY = Histogram(
    "rag_e2e_latency_seconds",
    "End-to-end response latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
)

EMBEDDING_LATENCY = Histogram(
    "rag_embedding_latency_seconds",
    "Time to generate embeddings",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Counters
QUERIES_TOTAL = Counter(
    "rag_queries_total",
    "Total number of queries processed",
    ["status"],  # success, refused, error
)

INGESTION_TOTAL = Counter(
    "rag_ingestion_total",
    "Total document ingestion attempts",
    ["status"],  # success, failed
)

HALLUCINATION_EVENTS = Counter(
    "rag_hallucination_events_total",
    "Number of detected hallucinated citations",
)

TOKEN_USAGE = Counter(
    "rag_token_usage_total",
    "Total tokens consumed",
    ["type"],  # prompt, completion
)

# Gauges
INDEXED_DOCUMENTS = Gauge(
    "rag_indexed_documents_total",
    "Total number of indexed documents",
)

INDEXED_CHUNKS = Gauge(
    "rag_indexed_chunks_total",
    "Total number of indexed chunks",
)

ACTIVE_SESSIONS = Gauge(
    "rag_active_sessions",
    "Number of active chat sessions",
)

# Summaries for percentile tracking
RETRIEVAL_PRECISION = Summary(
    "rag_retrieval_precision",
    "Retrieval precision@5 scores",
)

CONFIDENCE_SCORES = Summary(
    "rag_confidence_scores",
    "Response confidence scores",
)


# ── Metric recording helpers ──────────────────────────────────────────────────

def record_query(status: str, latency_s: float, confidence: float = 0.0):
    QUERIES_TOTAL.labels(status=status).inc()
    E2E_LATENCY.observe(latency_s)
    if confidence > 0:
        CONFIDENCE_SCORES.observe(confidence)


def record_retrieval(latency_s: float):
    RETRIEVAL_LATENCY.observe(latency_s)


def record_ingestion(success: bool):
    status = "success" if success else "failed"
    INGESTION_TOTAL.labels(status=status).inc()


def record_token_usage(prompt_tokens: int, completion_tokens: int):
    TOKEN_USAGE.labels(type="prompt").inc(prompt_tokens)
    TOKEN_USAGE.labels(type="completion").inc(completion_tokens)
    if prompt_tokens + completion_tokens > 4000:
        logger.warning(
            f"High token usage: {prompt_tokens + completion_tokens} tokens "
            f"(prompt={prompt_tokens}, completion={completion_tokens})"
        )


def record_hallucination(count: int = 1):
    HALLUCINATION_EVENTS.inc(count)


# ── FastAPI Middleware ────────────────────────────────────────────────────────

async def metrics_middleware(request: Request, call_next):
    """Track request latency for all API endpoints."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # Only track API endpoints
    if request.url.path.startswith("/api/"):
        E2E_LATENCY.observe(duration)

    return response


# ── Prometheus metrics endpoint ───────────────────────────────────────────────

async def prometheus_metrics_endpoint(request: Request):
    """Expose Prometheus metrics at /metrics."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


# ── OpenTelemetry Setup ───────────────────────────────────────────────────────

def setup_opentelemetry(app=None):
    """Initialize OpenTelemetry tracing with OTLP exporter."""
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "1.0.0",
        "deployment.environment": settings.app_env,
    })

    provider = TracerProvider(resource=resource)

    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured: {settings.otel_exporter_otlp_endpoint}")
    except Exception as e:
        logger.warning(f"OTLP exporter setup failed (continuing without): {e}")

    trace.set_tracer_provider(provider)

    if app:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OpenTelemetry instrumentation enabled")

    return trace.get_tracer(settings.otel_service_name)


# ── Tracer instance ───────────────────────────────────────────────────────────
tracer = trace.get_tracer(settings.otel_service_name)


def traced(span_name: str):
    """Decorator to add OpenTelemetry tracing to a function."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
