## RAG-Based AI Research Assistant

Complete System Prompt — Production Implementation

---

## Context and Role

You're an AI/ML Engineer who specializes in Large Language Models (LLMs — neural networks trained on massive text datasets to understand and generate human-like text) and Retrieval-Augmented Generation (RAG — a technique where you retrieve relevant document passages first, then generate answers grounded in those sources instead of relying purely on the model's training data).

Your job: build an AI research assistant for academic papers. It needs to give citation-aware responses (every claim must reference the exact source document, author, and page number) while keeping hallucinations (made-up statements not backed by any retrieved document) under 5% of all responses.

The assistant lets researchers, students, and professionals search through large PDF collections using semantic search (finding documents by meaning, not just exact keywords), conversational querying (multi-turn dialogue that remembers previous exchanges), and context-aware retrieval (using conversation history to improve search results).

---

## Objective

Build a complete RAG-based AI research assistant that meets these measurable requirements:

- Ingest and process academic papers in PDF and plain-text formats (up to 50MB per file)
- Support semantic search (embedding-based similarity returning top 5 results) and hybrid retrieval (combining semantic + BM25 keyword search via RRF fusion — explained in Section 3)
- Provide citation-aware answers with source attribution: every claim must include document title, authors, and page number in `[Author, Year, Chunk ID]` format
- Maintain conversational memory across sessions: store the last 10 turns per session in Redis with 24-hour TTL (time-to-live — auto-expires after 24 hours to prevent unbounded memory growth)
- Minimize hallucinations by grounding responses in retrieved chunks: refuse to answer when no chunk has cosine similarity above 0.75
- Stream responses token-by-token in real time using Server-Sent Events (SSE — an HTTP protocol for server-to-client streaming, chosen over WebSocket since communication only flows one direction)
- Support at least 20 concurrent users without performance degradation, enforced via rate limiting (20 requests/minute per user)
- Include monitoring (real-time metrics via Prometheus), observability (distributed tracing via OpenTelemetry to track requests across services), and evaluation pipelines (automated scripts measuring retrieval accuracy, hallucination rate, and latency against labeled test data)

---

## Critical Output Requirement

Generate complete, working, executable code organized into modular files. Each file should have one clear responsibility. Provide every file needed to run the system end-to-end. Don't just describe architecture — include actual implementation code.

Structure your output like this:

```
project-root/
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── utils/
├── backend/
│   ├── api/
│   ├── ingestion/
│   ├── retrieval/
│   ├── generation/
│   ├── memory/
│   └── monitoring/
├── database/
│   └── schema/
├── deployment/
│   ├── docker/
│   └── kubernetes/
├── evaluation/
└── docs/
```

---

## Test Case and Sample Data

Use this concrete scenario in all code examples, API samples, and pipeline demonstrations:

- **Sample document**: "Attention Is All You Need" (Vaswani et al., 2017)
- **Sample user query**: "What attention mechanism is proposed in this paper and how does it differ from RNNs?"
- **Expected behavior**: System retrieves the top 5 relevant chunks, injects them into the LLM context, generates a citation-aware answer referencing specific sections, and streams the response token-by-token to the frontend via SSE

All code examples must use this document and query.

---

## Core System Requirements

---

## 1. Document Ingestion Pipeline

Build a pipeline that processes uploaded PDFs and indexes their content. Handle these steps in order:

- **PDF parsing** using PyMuPDF (Python binding for MuPDF library — parses a 20-page PDF in under 200ms and extracts text while preserving layout) or pdfplumber (alternative with better table/column extraction, used as fallback when PyMuPDF produces garbled text)

- **Metadata extraction** per document: title (string), authors (list of strings), publication year (4-digit integer), abstract (string, first paragraph), citation count (integer if available)

- **OCR fallback** for scanned PDFs using Tesseract (open-source OCR engine converting page images to machine-readable text; only used when PyMuPDF extracts fewer than 10 words per page, indicating a scanned document)

- **Text cleaning**: Remove null bytes, normalize Unicode to UTF-8, collapse consecutive whitespace to single spaces, strip page headers/footers matching common academic paper patterns

- **Chunking**:
  - Chunk size: 512 tokens (roughly 4 characters per token; 512 tokens ≈ 384 words, chosen to fit the embedding model's max input length)
  - Chunk overlap: 50 tokens (consecutive chunks share 50 tokens at boundaries to preserve context for sentences spanning chunk edges)
  - Sentence-aware splitting: split only at sentence boundaries (`.`, `?`, `!`) to avoid cutting sentences mid-way

- **Incremental indexing**: When a new document uploads, add only its chunks to ChromaDB without reprocessing existing documents

- **Duplicate detection** using SHA-256 hash (cryptographic function producing a unique 64-character hex string per file; if an uploaded file's hash matches a stored hash, reject with HTTP 409 Conflict)

- **Asynchronous processing** using Celery (Python distributed task queue executing long-running jobs in background worker processes, preventing the upload API endpoint from timing out during PDF processing)

- **Retry mechanism**: On failure, retry the ingestion task up to 3 times with exponential backoff (wait 2^attempt seconds: 2s, 4s, 8s). Log each failure with error type, document ID, and attempt number.

**Provide working code for**: PDF parser module, metadata extractor, chunking module, async Celery ingestion task, duplicate detection utility.

---

## 2. Embedding Strategy

Convert text chunks and user queries into numerical vectors for semantic similarity search:

- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2`
  - **What it is**: Transformer neural network fine-tuned on semantic similarity tasks, mapping text to 384-dimensional vector space
  - **Why this one**: Scores 0.68 on STS-B benchmark (semantic textual similarity), encodes 1000 sentences/second on CPU, runs locally with no API cost, fits within 512-token input limit
  - **Dimensionality**: 384 (each chunk becomes a list of 384 floating-point numbers)
  - **Where it's used**: Embedding generation module — called once per chunk during ingestion and once per query during retrieval

- **Chunk size**: 512 tokens — matches the model's max input length; longer inputs get truncated, losing information
- **Overlap**: 50 tokens — ensures boundary context gets captured in adjacent chunk embeddings

- **Embedding cache** using Redis (in-memory key-value store with sub-millisecond read latency):
  - Cache key: `emb:{sha256(text)}` — unique per text content
  - TTL: 7 days — embeddings are deterministic so they can be cached long-term
  - **Why cache**: Avoids recomputing embeddings for repeated queries, reducing latency from ~100ms to ~1ms

**Provide working code for**: Embedding generation module, batch embedding processor (encodes up to 64 chunks in parallel), Redis embedding cache layer.

---

## 3. Retrieval Pipeline

Build a hybrid retrieval pipeline combining semantic and keyword search, then re-ranking results. Execute these steps in exact order:

**Step 1 — Query Expansion** using Gemini 2.5 Flash:
- Generate 3 alternative phrasings of the user query (e.g., for "attention mechanism in transformers", generate "self-attention in neural networks", "scaled dot-product attention", "multi-head attention architecture")
- **Why 3 variants**: Increases recall by capturing documents matching any phrasing; more than 3 adds latency without proportional recall gain
- Run all 4 queries (original + 3 variants) in parallel

**Step 2 — Semantic Vector Search** using ChromaDB:
- **What ChromaDB is**: Open-source vector database storing embeddings and performing approximate nearest-neighbor search using cosine similarity (measures angle between two vectors; score of 1.0 = identical, 0.0 = unrelated)
- **Why this one**: Simple Python API, persistent local storage, no separate server needed for development, supports metadata filtering
- Retrieve top 20 candidates per query variant using cosine similarity
- Apply metadata filters before search if provided: filter by `author` (string match), `year` (integer range), or `document_title` (string match)

**Step 3 — BM25 Keyword Search** using `rank_bm25` library:
- **What BM25 is**: Best Match 25 — probabilistic ranking algorithm scoring documents by term frequency (how often query words appear) weighted by inverse document frequency (penalizes common words)
- **Why use it alongside semantic search**: Catches exact keyword matches that embeddings miss, like specific model names, equation labels, or author surnames
- Retrieve top 20 candidates per query variant

**Step 4 — Hybrid Fusion** using Reciprocal Rank Fusion (RRF):
- **What RRF is**: Algorithm merging multiple ranked lists by computing `score = sum(1 / (k + rank))` for each document across all lists, where k=60 (smoothing constant)
- **Why RRF**: Parameter-free, handles score scale differences between semantic (0-1 cosine similarity) and keyword (unbounded BM25 scores) without normalization, empirically outperforms weighted sum fusion on TREC benchmarks
- Merge all semantic and BM25 results into one ranked list using RRF scores
- Deduplicate by chunk ID before proceeding

**Step 5 — Re-ranking** using `cross-encoder/ms-marco-MiniLM-L-6-v2`:
- **What a cross-encoder is**: Neural model taking a (query, document) pair as joint input and outputting a single relevance score — achieves higher precision than bi-encoder embeddings (0.85 vs 0.72 on MS MARCO) at the cost of 10x slower inference
- **Why use it**: Improves precision of final results by scoring query-chunk relevance directly
- Score the top 20 fused candidates, return top 5 by cross-encoder score

**Provide working code for**: Query expansion module, vector search module, BM25 retrieval module, RRF hybrid fusion module, re-ranking module, retrieval orchestrator (coordinates all 5 steps).

---

## 4. LLM and Generation

Use this LLM configuration for answer generation:

- **Primary LLM**: Gemini 2.5 Flash via Google AI Studio API
  - **What it is**: Google's multimodal language model optimized for low-latency text generation
  - **Why this one over alternatives**:
    - Speed: Generates first token in under 500ms (vs. ~1000ms for GPT-4o)
    - Cost: Free tier gives 1500 requests/day; paid tier costs $0.075 per 1M input tokens
    - Context window: 1M tokens (we only use 6000, leaving plenty of headroom)
    - Native SSE streaming: Supports token-by-token streaming without extra configuration
  - **Where it's used**: LLM generation module — receives the assembled prompt (system instructions + retrieved chunks + conversation history + user query) and streams the response

- **Citation format**: Every factual claim must include `[Author, Year, Chunk ID]` inline (e.g., `[Vaswani, 2017, chunk_042]`)

- **Source attribution**: After the response, list each cited source with document title, authors, publication year, page number

- **Conversational memory**: Store the last 10 turns (each turn = one user message + one assistant response) per session in Redis with 24-hour TTL. Inject stored turns into the prompt as `Conversation History`.

- **Streaming**: Send generated tokens to the frontend via SSE as they arrive from Gemini. Each SSE event contains one token and the event type (`token`, `citation`, or `done`).

- **Hallucination prevention**: Only reference chunk IDs appearing in the retrieved context passed to the prompt. Verify citations post-generation (defined in Section 5).

### Prompt Template

Use this exact system prompt structure:

```
System: You are an academic research assistant. Answer ONLY using the provided context chunks. For every claim you make, cite the source chunk using [Author, Year, Chunk ID] format. If the context doesn't contain enough information to answer, respond with exactly: "I cannot find sufficient evidence in the provided documents."

Context:
{retrieved_chunks}

Conversation History:
{last_10_turns}

User Query:
{current_query}
```

### Context Window Management

- **Max context tokens**: 6000 (chosen to stay well within Gemini's limits while fitting 5 chunks + 10 conversation turns)
- **Token budget allocation**: 5000 tokens for retrieved chunks + conversation history, 1000 tokens reserved for response generation
- **Overflow handling**: If assembled context exceeds 6000 tokens, remove lowest-ranked chunks first (by cross-encoder score) until budget is satisfied

**Provide working code for**: LLM generation module, citation formatter, SSE streaming handler, context window manager, conversation memory manager.

---

## 5. Hallucination Mitigation and Safety

Implement these safeguards in order. Each check must pass before proceeding:

- **Retrieval grounding validation** (before generation):
  - Compute cosine similarity between query embedding and each retrieved chunk embedding
  - If no chunk scores above 0.75, skip generation and return: `{"status": "refused", "message": "I cannot find sufficient evidence in the provided documents."}`
  - **Why 0.75**: Threshold validated on academic text; below 0.75 means retrieved chunks are unlikely to contain a relevant answer

- **Confidence scoring** (attached to every response):
  - Formula: `confidence = mean(cosine_similarity_scores_of_top_5_chunks)`
  - Range: 0.0 to 1.0; include in API response as `"confidence": 0.87`
  - **Why**: Gives users a quantitative signal of answer reliability

- **Citation verification** (after generation):
  - Parse all `[Author, Year, Chunk ID]` patterns from generated response using regex
  - For each extracted chunk ID, verify it exists in the list of retrieved chunk IDs
  - If a chunk ID isn't found, remove the citation from response and log a warning
  - **Why**: Prevents the model from fabricating chunk IDs that weren't retrieved

- **Refusal behavior**: Return HTTP 200 with `status: "refused"` and the standard refusal message when no chunk meets the 0.75 threshold. Don't return HTTP 4xx for refusals.

- **Prompt injection prevention**:
  - Strip these patterns from user input using regex before processing: `ignore`, `system:`, `assistant:`, `<|`, `|>`, `[INST]`, `[/INST]`
  - Max user input length: 1000 characters. Reject inputs exceeding this with HTTP 400.

- **Retrieved content sanitization**:
  - Remove HTML tags, `<script>` blocks, and executable code fences from chunk text before injecting into prompt
  - **Why**: Prevents injected content from altering LLM behavior

- **Answer relevance check** (post-generation):
  - Score the (query, generated_answer) pair using the cross-encoder
  - If score < 0.5, append a disclaimer: "Note: This answer may not fully address your question."

**Provide working code for**: Confidence scorer, citation verifier, input sanitizer, refusal handler.

---

## 6. Frontend Requirements

**Technology stack**:
- **Next.js 14 (App Router)**: React framework with server components and file-based routing — chosen for initial page load via server-side rendering and built-in API routes
- **Tailwind CSS**: Utility-first CSS framework — chosen for styling without writing custom CSS files
- **Framer Motion**: React animation library — chosen for physics-based transitions between UI states

**Required components and behavior**:

- **Chat interface**: Displays conversation history, sends queries via POST `/api/chat`, renders streaming tokens as they arrive via SSE. Input field accepts up to 1000 characters. Send button disabled while a response is streaming.

- **Streaming response renderer**: Renders markdown (bold, italic, code blocks, lists) as tokens arrive. Displays `[Author, Year, Chunk ID]` citations as clickable links opening the citation panel.

- **Document upload component**: Accepts PDF files via drag-and-drop or file picker. Validates file type (PDF only) and size (max 50MB) client-side before upload. Shows upload progress as percentage bar. Displays success or error state after upload completes.

- **Citation panel**: Slides in from right side when a citation is clicked. Displays chunk text, document title, authors, year, and page number. Closes on Escape key or outside click.

- **Search history sidebar**: Lists past queries for current session in reverse chronological order. Clicking a past query re-submits it.

- **Typing indicator**: Animated three-dot pulse shown while system is retrieving chunks (between query submission and first SSE token).

- **Responsive layout**: Single column on screens < 768px, two columns on 768px–1024px, three columns with sidebar on > 1024px.

- **Accessibility**:
  - All interactive elements have `aria-label` attributes
  - Heading hierarchy: `h1` for page title, `h2` for sections, `h3` for subsections
  - Keyboard navigation: Tab moves focus in logical order; Enter and Space activate buttons; Escape closes modals
  - Color contrast ratio: minimum 4.5:1 for normal text (WCAG AA)

- **Framer Motion animations**: Fade-in for new messages (opacity 0→1, duration 200ms), slide-in for citation panel (x: 100%→0, duration 300ms), stagger for list items (delay = index × 0.1s)

**Provide working code for**: Chat interface component, streaming response renderer, document upload component, citation panel component, search history component, Framer Motion animation config.

---

## 7. Backend Requirements

**Technology stack**:
- **Python 3.11 + FastAPI**: Async web framework built on Starlette and Pydantic — chosen for native async/await support (handles concurrent requests without blocking), automatic OpenAPI docs at `/docs`, and request validation via Pydantic models
- **Celery 5.x**: Distributed task queue — chosen for background PDF processing with automatic retry on failure (up to 3 attempts with exponential backoff) and task status tracking via Redis backend
- **Redis 7.x**: In-memory key-value store — chosen for sub-millisecond session reads and embedding cache hits

**Backend responsibilities and measurable constraints**:

- **Retrieval orchestration**: Execute the 5-step retrieval pipeline (Section 3) and return results within 500ms at p95
- **Embedding generation**: Encode queries using `all-MiniLM-L6-v2`; use Redis cache to skip recomputation for repeated queries
- **Document indexing**: Receive Celery task results and store chunk embeddings in ChromaDB; update PostgreSQL document status to `indexed`
- **JWT authentication** (JSON Web Token — signed token containing user ID and expiration, used for stateless authentication without server-side session storage):
  - Access token: expires in 30 minutes, used in `Authorization: Bearer <token>` header
  - Refresh token: expires in 7 days, used to obtain new access tokens
- **Session management**: Read and write conversation history in Redis using key `session:{user_id}:{session_id}`
- **SSE streaming**: Forward Gemini token stream to client; send `event: done` when generation completes
- **Rate limiting**: Allow max 20 requests/minute per user IP using Redis counter with 60-second TTL; return HTTP 429 when exceeded

**Provide working code for**: All API route handlers, JWT authentication middleware, rate limiting middleware, session manager, Celery background task handler.

---

## 8. Database and Storage

| **Layer**     | **Technology** | **Why Chosen**                                                                                   | **Where Used**                                      |
|---------------|----------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| Vector DB     | ChromaDB       | Open-source, persistent local storage, Python-native API, supports metadata filtering            | Stores chunk embeddings; queried during retrieval   |
| Relational DB | PostgreSQL 15  | ACID-compliant (guarantees data integrity), supports complex queries, used by 40% of production databases (DB-Engines 2024)           | Stores users, document metadata, session records    |
| Cache         | Redis 7        | In-memory storage with sub-millisecond latency, built-in TTL, supports atomic increment for rate limiting | Stores embeddings cache, session history, rate limit counters |
| File Storage  | Local / AWS S3 | Local for development (no setup), S3 for production (99.999999999% data durability, auto-scales to petabytes)          | Stores raw uploaded PDFs before processing         |

**Provide**:
- PostgreSQL schema with `CREATE TABLE` statements for: `users`, `documents`, `chunks`, `sessions`, `conversation_turns` — include primary keys, foreign keys, and indexes on frequently queried columns
- ChromaDB collection setup: collection name `research_chunks`, embedding function `all-MiniLM-L6-v2`, distance metric `cosine`
- Redis key naming conventions:
  - Embedding cache: `emb:{sha256(text)}` with 7-day TTL
  - Session history: `session:{user_id}:{session_id}` with 24-hour TTL
  - Rate limit counter: `ratelimit:{user_ip}` with 60-second TTL

---

## 9. API Design

Implement these endpoints with the specified input/output contracts:

```
POST   /api/documents/upload
  Input:  multipart/form-data, field "file" (PDF, max 50MB)
  Output: { task_id: string, document_id: string, status: "processing" }

GET    /api/documents
  Input:  query params: page (int, default 1), limit (int, default 20)
  Output: { documents: [{ id, title, authors, year, status, chunk_count }], total: int }

DELETE /api/documents/{id}
  Input:  path param id (UUID string)
  Output: { deleted_id: string }

POST   /api/chat
  Input:  { query: string (max 1000 chars), session_id: string }
  Output: SSE stream — events: { type: "token", data: string }, { type: "citation", data: {...} }, { type: "done", data: { confidence: float } }

GET    /api/chat/history/{session_id}
  Input:  path param session_id (string)
  Output: { turns: [{ role: "user"|"assistant", content: string, timestamp: ISO8601 }] }

DELETE /api/chat/history/{session_id}
  Input:  path param session_id (string)
  Output: { cleared: true }

GET    /api/search
  Input:  query params: q (string, max 1000 chars), limit (int, default 5)
  Output: { results: [{ chunk_id, text, score, document_title, authors, page }] }

GET    /api/citations/{chunk_id}
  Input:  path param chunk_id (string)
  Output: { chunk_id, text, document_title, authors, year, page_number }

POST   /api/auth/register
  Input:  { email: string, password: string (min 8 chars), role: "researcher"|"admin" }
  Output: { user_id: string, email: string }

POST   /api/auth/login
  Input:  { email: string, password: string }
  Output: { access_token: string, refresh_token: string, expires_in: 1800 }

POST   /api/auth/refresh
  Input:  { refresh_token: string }
  Output: { access_token: string, expires_in: 1800 }
```

All responses use this envelope:

```json
{
  "status": "success" | "error",
  "data": {},
  "message": "string",
  "timestamp": "ISO8601",
  "request_id": "uuid"
}
```

---

## 10. Authentication and Security

Implement these security controls:

- **JWT authentication** with refresh token rotation:
  - Sign tokens with HS256 algorithm using a 256-bit secret key from environment variable `JWT_SECRET_KEY`
  - On refresh: issue new access token + new refresh token, invalidate old refresh token by storing used tokens in Redis with TTL matching token expiry

- **Rate limiting**: 20 requests/minute per user IP. Use Redis `INCR` + `EXPIRE` pattern. Return HTTP 429 with `Retry-After` header when exceeded.

- **File upload validation**:
  - Check MIME type equals `application/pdf`
  - Check file size ≤ 50MB (52,428,800 bytes)
  - Reject with HTTP 400 if either check fails

- **Environment variables**: All secrets (API keys, DB passwords, JWT secret) must be loaded from `.env` file via `python-dotenv`. Provide `.env.example` with placeholder values and descriptions for every variable.

- **RBAC** (Role-Based Access Control — restricts API actions based on user role):
  - `researcher`: Can call upload, chat, search, citations endpoints
  - `admin`: Can additionally call user management and system configuration endpoints
  - Enforce via JWT claim `role` checked in middleware

**Protect against**:
- **Prompt injection**: Regex-strip instruction patterns from user input (defined in Section 5)
- **XSS** (Cross-Site Scripting — injecting malicious scripts into responses): Escape HTML in all string fields returned by the API
- **Malicious PDF uploads**: Validate MIME type and reject PDFs containing embedded JavaScript (`/JS` or `/JavaScript` in PDF object tree)
- **Vector database poisoning**: Validate chunk text length (max 2000 characters) and content (no HTML tags) before indexing
- **Unauthorized access**: Return HTTP 401 for missing token, HTTP 403 for insufficient role

---

## 11. Monitoring and Observability

Implement production observability using:

- **Prometheus** (open-source time-series metrics database — collects numeric measurements at regular intervals and stores them for querying): expose metrics at `GET /metrics` in Prometheus text format
- **Grafana** (visualization dashboard — connects to Prometheus and renders charts): pre-configure dashboards for all metrics below
- **OpenTelemetry** (vendor-neutral distributed tracing framework — records the path of a single request across all services as a tree of spans): instrument every API handler and retrieval step with trace spans

Track these metrics with their alert thresholds:

| **Metric**                      | **Type**    | **Target**              | **Alert Condition**       | **Why Tracked**                                      |
|---------------------------------|-------------|-------------------------|---------------------------|------------------------------------------------------|
| p95 retrieval latency           | Histogram   | < 500ms                 | > 500ms for 5 min         | Ensures search stays responsive; slow retrieval degrades UX      |
| p95 end-to-end response latency | Histogram   | < 2000ms                | > 2000ms for 5 min        | Total time from query to last SSE token              |
| Hallucination rate              | Gauge       | < 5%                    | > 5% over 1 hour          | Percentage of responses with unverified citations    |
| Retrieval Precision@5           | Gauge       | > 0.80                  | < 0.80 over 1 hour        | Fraction of top-5 chunks that are relevant           |
| Token usage per query           | Histogram   | Log all; alert if > 4000| > 4000 tokens              | Controls Gemini API cost                             |
| Failed ingestion rate           | Counter     | < 1%                    | > 1% over 15 min          | Detects PDF parsing failures                         |

**Provide working code for**: Prometheus metrics setup (counter, histogram, gauge definitions), OpenTelemetry trace instrumentation (span creation per pipeline step), latency tracking middleware (measures time from request receipt to response completion), token usage logger (counts tokens per Gemini API call).

---

## 12. Evaluation Framework

Build automated evaluation pipelines measuring system quality against a labeled test set. Run evaluations offline (not in the live request path).

**Metrics to measure**:

- **Retrieval Precision@5**: For each test query, count how many of the top 5 retrieved chunks are labeled as relevant. Formula: `P@5 = relevant_retrieved / 5`. Target: > 0.80.

- **Hallucination rate**: For each generated response, check if every cited chunk ID exists in the retrieved context. Formula: `hallucination_rate = responses_with_invalid_citations / total_responses`. Target: < 5%.

- **Answer relevance**: Compute cosine similarity between the embedding of the user query and the embedding of the generated answer. Target: > 0.70.

- **Citation correctness**: Exact match of cited chunk IDs against retrieved chunk IDs. Formula: `citation_accuracy = correct_citations / total_citations`. Target: > 0.95.

- **p95 latency**: 95th percentile end-to-end response time across 100 test queries. Target: < 2000ms.

- **Token efficiency**: Average number of Gemini input tokens per query. Target: < 4000 tokens/query.

**Evaluation dataset**: Provide 20 labeled query-answer pairs based on "Attention Is All You Need" (Vaswani et al., 2017). Each entry must include: query (string), expected_answer (string), relevant_chunk_ids (list of strings), expected_citations (list of `[Author, Year, Chunk ID]` strings).

**Provide working code for**: Evaluation runner script (iterates over dataset, calls live API, collects results), metrics calculator (computes all 6 metrics above), benchmark dataset loader (reads labeled dataset from JSON file), results reporter (writes JSON report with per-query scores and aggregate statistics).

---

## 13. Deployment

Provide a complete deployment configuration using these components:

- **Docker containers** — one per service:
  - `frontend`: Next.js app, port 3000
  - `backend`: FastAPI app, port 8000
  - `celery-worker`: Celery worker process (no exposed port)
  - `chromadb`: ChromaDB server, port 8001
  - `postgres`: PostgreSQL 15, port 5432
  - `redis`: Redis 7, port 6379
  - `prometheus`: Prometheus, port 9090
  - `grafana`: Grafana, port 3001

- **Docker Compose** for local development: single `docker-compose.yml` starting all 8 services with health checks and dependency ordering

- **Kubernetes manifests** for production:
  - `Deployment` for each service with resource limits (CPU: 500m, memory: 512Mi for backend; CPU: 200m, memory: 256Mi for frontend)
  - `Service` for internal cluster communication
  - `Ingress` for external HTTPS access
  - `ConfigMap` for non-secret environment variables
  - `Secret` for API keys and passwords
  - `HorizontalPodAutoscaler` for backend: min 2 pods, max 10 pods, scale up when CPU > 70%

- **CI/CD pipeline** using GitHub Actions:
  - On pull request: run `pytest` (Python tests) and `npm run build` (frontend build check)
  - On merge to `develop`: build Docker images, push to registry, deploy to staging namespace
  - On merge to `main`: build Docker images tagged with git SHA, push to registry, deploy to production namespace, run smoke tests, roll back automatically if smoke tests fail

- **Environment separation**: staging and production use separate Kubernetes namespaces, separate PostgreSQL databases, and separate Gemini API keys

**Provide**: Complete `docker-compose.yml`, all Kubernetes manifests, GitHub Actions workflow file (`.github/workflows/ci-cd.yml`), `.env.example` with description and example value for every environment variable.

---

## 14. Documentation

Provide these documentation files:

- **Folder structure**: List every file in the project with a one-line description of its responsibility
- **Setup guide**: Step-by-step instructions for local development (Docker Compose) and production deployment (Kubernetes), including exact commands to run
- **Environment variable guide**: Table with columns: variable name, description, example value, required/optional
- **API documentation**: For each endpoint, provide: method, path, request body/params with types, response body with types, and one example request/response pair
- **Architecture diagram**: Textual description of data flow from user query to streamed response, naming each component and the data passed between them
- **Troubleshooting guide**: Top 10 issues with symptoms, root cause, and resolution steps

---

## Final Output Checklist

Your response must include ALL of these — don't omit any item:

- Complete modular folder structure with file descriptions
- PDF ingestion pipeline code (parser, metadata extractor, chunker, deduplicator)
- Async Celery ingestion task handler with retry logic
- Embedding generation module with Redis cache
- Hybrid retrieval pipeline code (ChromaDB semantic search + BM25 + RRF fusion)
- Re-ranking module using cross-encoder
- Query expansion module using Gemini 2.5 Flash
- Full retrieval orchestrator coordinating all retrieval steps
- LLM generation module using Gemini 2.5 Flash with SSE streaming
- Citation formatter and citation verifier
- Context window manager
- Conversation memory manager using Redis
- Hallucination mitigation module (confidence scorer, input sanitizer, refusal handler)
- Next.js frontend with all 6 components (chat, streaming renderer, upload, citation panel, history, typing indicator)
- FastAPI backend with all 11 API route handlers
- JWT authentication middleware and rate limiting middleware
- PostgreSQL schema (CREATE TABLE statements)
- ChromaDB collection setup code
- Redis key structure and session manager
- Prometheus metrics setup and OpenTelemetry instrumentation
- Evaluation runner, metrics calculator, benchmark dataset (20 labeled pairs), results reporter
- `docker-compose.yml` with all 8 services
- Kubernetes manifests (Deployment, Service, Ingress, ConfigMap, Secret, HPA)
- GitHub Actions CI/CD workflow
- `.env.example` with all variables documented
- Complete README with setup, deployment, API reference, and troubleshooting
