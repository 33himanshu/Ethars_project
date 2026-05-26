# RAG Research Assistant

A production-grade AI research assistant for academic papers using Retrieval-Augmented Generation (RAG). Provides citation-aware, hallucination-minimized answers with real-time streaming.

**🤖 Powered by Google Gemini 2.5 Flash** - Fast, accurate, and free tier available!

**⚡ 5-Minute Setup** - Just Docker + Google API key required!

---

## 📚 Documentation

| Guide | Purpose | Time |
|-------|---------|------|
| **[START_HERE.md](START_HERE.md)** | 👈 **New users start here!** | 5 min |
| [QUICKSTART.md](QUICKSTART.md) | Detailed quick start guide | 10 min |
| [WHICH_SETUP.md](WHICH_SETUP.md) | Choose minimal vs full setup | 5 min |
| [CONFIGURATION.md](CONFIGURATION.md) | All settings explained | Reference |
| [SETUP.md](SETUP.md) | Production deployment guide | 30 min |
| [README.md](README.md) | Architecture & API reference (this file) | Reference |

**First time?** → Go to **[START_HERE.md](START_HERE.md)** now!

---

## Architecture Overview

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                          │
│  Chat Interface → SSE Stream → Citation Panel               │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Auth (JWT)  │  │ Rate Limiter │  │ Input Sanitizer  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Retrieval Orchestrator                  │   │
│  │                                                     │   │
│  │  Query Expansion (3 variants via Gemini)            │   │
│  │       ↓                                             │   │
│  │  ┌──────────────┐    ┌──────────────┐              │   │
│  │  │ ChromaDB     │    │ BM25 Search  │              │   │
│  │  │ Vector Search│    │ (rank_bm25)  │              │   │
│  │  └──────┬───────┘    └──────┬───────┘              │   │
│  │         └────────┬──────────┘                      │   │
│  │                  ▼                                  │   │
│  │         RRF Hybrid Fusion                           │   │
│  │                  ▼                                  │   │
│  │    Cross-Encoder Re-ranking (ms-marco)              │   │
│  │                  ▼                                  │   │
│  │         Top-5 Ranked Chunks                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Generation Pipeline                     │   │
│  │                                                     │   │
│  │  Hallucination Guard → Context Manager              │   │
│  │       ↓                                             │   │
│  │  Gemini 2.5 Flash (streaming)                       │   │
│  │       ↓                                             │   │
│  │  Citation Verifier → SSE Stream                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
    PostgreSQL             ChromaDB              Redis
  (metadata, users)    (vector index)      (sessions, cache)
```

## Project Structure

```
rag-research-assistant/
├── backend/
│   ├── api/
│   │   ├── auth.py              # JWT auth, register, login, refresh
│   │   ├── chat.py              # SSE streaming chat endpoint
│   │   ├── documents.py         # Upload, list, delete documents
│   │   ├── search.py            # Semantic search + citation lookup
│   │   └── middleware.py        # Rate limiting, CORS, security headers
│   ├── ingestion/
│   │   ├── pdf_parser.py        # PyMuPDF + pdfplumber + OCR fallback
│   │   ├── metadata_extractor.py # Title, authors, year, abstract
│   │   ├── chunker.py           # Sentence-aware 512-token chunking
│   │   ├── duplicate_detector.py # SHA-256 hash deduplication
│   │   └── tasks.py             # Celery async ingestion pipeline
│   ├── retrieval/
│   │   ├── embeddings.py        # all-MiniLM-L6-v2 + Redis cache
│   │   ├── vector_store.py      # ChromaDB semantic search
│   │   ├── bm25_retriever.py    # BM25 keyword search
│   │   ├── hybrid_fusion.py     # Reciprocal Rank Fusion (RRF)
│   │   ├── reranker.py          # Cross-encoder ms-marco re-ranking
│   │   ├── query_expander.py    # Gemini query expansion (3 variants)
│   │   └── orchestrator.py      # Full retrieval pipeline coordinator
│   ├── generation/
│   │   ├── llm_generator.py     # Gemini 2.5 Flash streaming generation
│   │   ├── context_manager.py   # 6000-token context window management
│   │   ├── citation_formatter.py # Citation parsing and verification
│   │   └── hallucination_guard.py # Safety checks and input sanitization
│   ├── memory/
│   │   └── session_manager.py   # Redis conversation history (10 turns, 24h TTL)
│   ├── monitoring/
│   │   └── metrics.py           # Prometheus + OpenTelemetry instrumentation
│   ├── database/
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── connection.py        # Async PostgreSQL connection
│   │   └── schema/
│   │       └── 001_initial.sql  # PostgreSQL schema
│   ├── config.py                # Pydantic settings management
│   ├── main.py                  # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Main page with tab navigation
│   │   └── globals.css          # Global styles
│   ├── components/
│   │   ├── ChatInterface.tsx    # Main chat UI with SSE streaming
│   │   ├── StreamingMessage.tsx # Token-by-token markdown renderer
│   │   ├── CitationPanel.tsx    # Sliding citation source panel
│   │   ├── DocumentUpload.tsx   # Drag-and-drop PDF upload
│   │   ├── SearchHistory.tsx    # Session history browser
│   │   └── TypingIndicator.tsx  # Animated typing dots
│   ├── hooks/
│   │   └── useChat.ts           # SSE streaming chat hook
│   ├── utils/
│   │   └── api.ts               # API client utilities
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── evaluation/
│   ├── benchmark_dataset.py     # 20 labeled Q&A pairs (Attention paper)
│   └── evaluator.py             # Automated evaluation runner
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.celery
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── backend-deployment.yaml  # Deployment + HPA
│   │   ├── frontend-deployment.yaml # Deployment + Ingress
│   │   └── configmap.yaml
│   └── monitoring/
│       └── prometheus.yml
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # GitHub Actions CI/CD
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start (5 Minutes!)

### Prerequisites
- **Docker Desktop** (that's it!)
- **Google AI Studio API key** (free at https://aistudio.google.com/app/apikey)

### 1. Get your API key
Visit https://aistudio.google.com/app/apikey and create a free API key.

### 2. Configure (minimal setup)

```bash
cd rag-research-assistant
copy .env.minimal .env
notepad .env
```

**Just set your API key** - everything else has working defaults:
```env
GOOGLE_API_KEY=your-google-ai-studio-api-key
```

That's it! The other 4 variables in `.env.minimal` have defaults that work fine for development.

### 3. Start everything

```bash
docker-compose up -d
```

First run downloads images (~2 minutes). Subsequent starts take ~10 seconds.

### 4. Open the app

Go to **http://localhost:3000**

1. **Register** an account
2. **Upload** a PDF paper (drag & drop)
3. **Ask** questions in the chat!

**That's it!** See [QUICKSTART.md](QUICKSTART.md) for detailed walkthrough.

---

## What's Running?

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Main UI |
| Backend API | 8000 | REST API + SSE streaming |
| PostgreSQL | 5432 | User data, document metadata |
| Redis | 6379 | Sessions, caching |
| ChromaDB | 8001 | Vector embeddings |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Monitoring dashboards |

**API Documentation**: http://localhost:8000/docs

---

## Advanced Setup

### Local Development (Without Docker)

For development with hot-reload and debugging:

**Backend:**
```bash
# Install Python 3.11+
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r backend/requirements.txt

# Start services manually (or use Docker for these)
# PostgreSQL, Redis, ChromaDB

# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (separate terminal)
celery -A backend.ingestion.tasks.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

See [SETUP.md](SETUP.md) for detailed manual setup instructions.

---

## Configuration

### Minimal Setup (Development)
The `.env.minimal` file contains only 5 variables:
- `GOOGLE_API_KEY` - **Required** (get from https://aistudio.google.com)
- `POSTGRES_PASSWORD` - Optional (default: `devpass123`)
- `REDIS_PASSWORD` - Optional (default: `devpass123`)
- `JWT_SECRET_KEY` - Optional (default provided)
- `APP_SECRET_KEY` - Optional (default provided)

All other settings use sensible defaults from `backend/config.py`.

### Full Configuration (Production)
For production deployment, use `.env.example` as a template with all 50+ variables for fine-grained control.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI Studio API key | **Required** |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `SIMILARITY_THRESHOLD` | Min similarity for grounding | `0.75` |
| `TOP_K_RETRIEVAL` | Chunks returned after re-ranking | `5` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit per user | `20` |
| `MAX_FILE_SIZE_MB` | Max PDF upload size | `50` |

See `.env.example` for the complete list of 50+ configurable settings.

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Get JWT tokens |
| POST | `/api/auth/refresh` | Rotate refresh token |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload PDF (multipart) |
| GET | `/api/documents` | List indexed documents |
| DELETE | `/api/documents/{id}` | Delete document |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Submit query → SSE stream |
| GET | `/api/chat/history/{session_id}` | Get conversation history |
| DELETE | `/api/chat/history/{session_id}` | Clear session |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search?q=...` | Semantic search |
| GET | `/api/citations/{chunk_id}` | Get source chunk |

All responses follow:
```json
{
  "status": "success|error",
  "data": {},
  "message": "string",
  "timestamp": "ISO8601",
  "request_id": "uuid"
}
```

## Production Deployment

### Kubernetes

```bash
# Apply namespace and config
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl apply -f deployment/kubernetes/configmap.yaml

# Update image tags in deployment files, then:
kubectl apply -f deployment/kubernetes/backend-deployment.yaml
kubectl apply -f deployment/kubernetes/frontend-deployment.yaml
```

### CI/CD

Push to `develop` → deploys to staging.
Push to `main` → deploys to production with automatic rollback on failure.

Required GitHub secrets:
- `KUBE_CONFIG_STAGING` - base64-encoded kubeconfig for staging
- `KUBE_CONFIG_PROD` - base64-encoded kubeconfig for production

## Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin / admin)
- **Metrics endpoint**: http://localhost:8000/metrics

Key metrics tracked:
| Metric | Target |
|--------|--------|
| p95 retrieval latency | < 500ms |
| p95 end-to-end latency | < 2000ms |
| Hallucination rate | < 5% |
| Retrieval Precision@5 | > 0.80 |

## Evaluation

```bash
# Set auth token
export EVAL_AUTH_TOKEN="your-jwt-token"

# Run evaluation against benchmark dataset
cd rag-research-assistant
python -m evaluation.evaluator
```

Results saved to `evaluation/results/eval_report_TIMESTAMP.json`.

## Troubleshooting

**1. ChromaDB connection refused**
```bash
docker-compose restart chromadb
# Wait 15s then restart backend
docker-compose restart backend
```

**2. Embedding model download fails**
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

**3. Celery tasks not processing**
```bash
docker-compose logs celery-worker
# Check Redis connection
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

**4. PDF parsing fails (scanned PDF)**
- Ensure Tesseract is installed: `tesseract --version`
- The system auto-falls back to OCR for scanned PDFs

**5. "I cannot find sufficient evidence" for all queries**
- Verify documents are indexed: `GET /api/documents?status=indexed`
- Lower `SIMILARITY_THRESHOLD` in `.env` (try 0.5 for testing)
- Check ChromaDB has chunks: `docker-compose exec chromadb curl localhost:8000/api/v1/collections`

**6. Rate limit errors (429)**
- Default: 20 requests/minute per IP
- Increase `RATE_LIMIT_PER_MINUTE` in `.env`

**7. JWT token expired**
- Access tokens expire in 30 minutes
- Use `/api/auth/refresh` with your refresh token

**8. High memory usage**
- Embedding model uses ~90MB RAM
- Reduce `CELERY_CONCURRENCY` for workers with limited RAM

**9. SSE stream disconnects**
- Check nginx proxy timeout settings (see Kubernetes ingress annotations)
- Ensure `X-Accel-Buffering: no` header is passed through

**10. Database migration needed**
```bash
# Run schema manually
docker-compose exec postgres psql -U rag_user -d rag_research \
  -f /docker-entrypoint-initdb.d/001_initial.sql
```

## Security Notes

- All API endpoints require JWT authentication
- PDFs are validated (type + size) before processing
- Input sanitization prevents prompt injection
- Retrieved content is sanitized before LLM injection
- Refresh tokens are rotated on each use
- RBAC: `researcher` (upload + query) vs `admin` (full access)
- Rate limiting: 20 req/min per user via Redis

## License

MIT
