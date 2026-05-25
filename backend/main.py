"""
FastAPI Application Entry Point
--------------------------------
Registers all routers, middleware, and startup/shutdown events.
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.api.search import router as search_router
from backend.api.middleware import setup_middleware
from backend.config import settings
from backend.database.connection import init_db
from backend.monitoring.metrics import (
    setup_opentelemetry,
    prometheus_metrics_endpoint,
    metrics_middleware,
)

# ── Logging configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup/shutdown) ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    logger.info("Starting RAG Research Assistant...")

    # Initialize database tables
    await init_db()
    logger.info("Database initialized")

    # Setup OpenTelemetry
    setup_opentelemetry(app)
    logger.info("OpenTelemetry configured")

    # Warm up embedding model
    try:
        from backend.retrieval.embeddings import get_model
        get_model()
        logger.info("Embedding model loaded")
    except Exception as e:
        logger.warning(f"Embedding model warmup failed: {e}")

    logger.info(f"Application ready on {settings.app_host}:{settings.app_port}")
    yield

    # Shutdown
    logger.info("Shutting down RAG Research Assistant...")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Research Assistant",
    description="Production-grade AI research assistant with hybrid retrieval",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
setup_middleware(app)
app.middleware("http")(metrics_middleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(search_router)

# ── Prometheus metrics endpoint ───────────────────────────────────────────────
app.add_route("/metrics", prometheus_metrics_endpoint)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
    })


@app.get("/")
async def root():
    return {"message": "RAG Research Assistant API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        workers=1 if settings.app_debug else 4,
    )
