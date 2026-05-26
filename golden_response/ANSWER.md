# Answer to Your Question

## Your Question

> "Is all of this required or can we just run with Gemini API key for now?"

## Short Answer

**No, not all 50+ variables are required!**

You can run with **just your Gemini API key** using the minimal setup.

---

## What You Need (Minimal Setup)

### Required (1 variable)
```env
GOOGLE_API_KEY=your-google-ai-studio-api-key
```

### Optional (have defaults)
```env
POSTGRES_PASSWORD=devpass123
REDIS_PASSWORD=devpass123
JWT_SECRET_KEY=dev-jwt-secret-key-min-32-chars-for-development-only
APP_SECRET_KEY=dev-app-secret-key-min-32-chars-for-development-only
```

**That's it! Everything else uses defaults.**

---

## How to Run (5 Minutes)

### Step 1: Get API Key (2 min)
https://aistudio.google.com/app/apikey

### Step 2: Configure (1 min)
```bash
cd rag-research-assistant
copy .env.minimal .env
notepad .env
```

Paste your API key:
```env
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Step 3: Start (2 min)
```bash
docker-compose up -d
```

### Step 4: Use It!
Open http://localhost:3000

---

## What About All Those Other Variables?

### They Have Defaults!

The system uses sensible defaults from `backend/config.py`:

| Setting | Default | Good For |
|---------|---------|----------|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Fast & free |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Good quality |
| `TOP_K_RETRIEVAL` | `5` | Balanced |
| `SIMILARITY_THRESHOLD` | `0.75` | Accurate |
| `RATE_LIMIT_PER_MINUTE` | `20` | Development |
| ... | ... | ... |

**You don't need to set them unless you want to customize!**

---

## What LLM Are We Using?

### Google Gemini 2.5 Flash

**Why this model?**
- ⚡ **Fast**: ~1s response time
- 🎯 **Accurate**: State-of-the-art quality
- 💰 **Free**: 60 requests/minute on free tier
- 📚 **Large context**: 1M tokens
- 🔄 **Streaming**: Real-time responses

**Alternatives** (change `GEMINI_MODEL` in `.env`):
- `gemini-2.0-flash-exp` - Experimental features
- `gemini-1.5-pro` - Better quality, slower, paid

---

## How to Run in Development

### Option 1: Docker Compose (Recommended)

**Easiest way - everything in containers:**

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Option 2: Manual (For Development)

**If you want hot-reload and debugging:**

**Terminal 1 - Backend:**
```bash
cd rag-research-assistant
python -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
cd rag-research-assistant
venv\Scripts\activate
celery -A backend.ingestion.tasks.celery_app worker --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd rag-research-assistant\frontend
npm install
npm run dev
```

**Terminal 4 - Services (still need Docker for these):**
```bash
# PostgreSQL
docker run -d --name rag-postgres -e POSTGRES_PASSWORD=devpass123 -p 5432:5432 postgres:16-alpine

# Redis
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine redis-server --requirepass devpass123

# ChromaDB
docker run -d --name rag-chromadb -p 8001:8000 chromadb/chroma:latest
```

---

## Comparison

### Docker Compose (Recommended)

**Pros:**
- ✅ One command to start everything
- ✅ No Python/Node.js installation needed
- ✅ Consistent environment
- ✅ Easy to reset

**Cons:**
- ❌ No hot-reload (need to rebuild)
- ❌ Harder to debug

**Best for:** Testing, demos, production-like setup

---

### Manual Setup

**Pros:**
- ✅ Hot-reload (instant code changes)
- ✅ Easy debugging
- ✅ Full control

**Cons:**
- ❌ Need Python 3.11+
- ❌ Need Node.js 20+
- ❌ Multiple terminals
- ❌ More complex setup

**Best for:** Active development, debugging

---

## What's Running?

```
┌─────────────────────────────────────────┐
│  Frontend (Next.js)                     │
│  Port: 3000                             │
│  • Chat interface                       │
│  • Document upload                      │
│  • Citation panel                       │
└────────────┬────────────────────────────┘
             │ HTTP/SSE
┌────────────▼────────────────────────────┐
│  Backend (FastAPI)                      │
│  Port: 8000                             │
│  • Query expansion (Gemini)             │
│  • Hybrid search (Vector + BM25)        │
│  • Re-ranking                           │
│  • Generation (Gemini 2.5 Flash)        │
│  • Citation verification                │
└─────────────────────────────────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Postgres│ │ChromaDB│ │ Redis  │
│Port:   │ │Port:   │ │Port:   │
│5432    │ │8001    │ │6379    │
└────────┘ └────────┘ └────────┘

┌─────────────────────────────────────────┐
│  Celery Worker                          │
│  • Async PDF processing                 │
│  • Embedding generation                 │
│  • Document indexing                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Monitoring                             │
│  • Prometheus (Port: 9090)              │
│  • Grafana (Port: 3001)                 │
└─────────────────────────────────────────┘
```

---

## Development Workflow

### 1. Start the System
```bash
docker-compose up -d
```

### 2. Make Changes
- Edit code in `backend/` or `frontend/`
- For backend: Rebuild container
- For frontend: Rebuild container

### 3. Rebuild After Changes
```bash
# Rebuild specific service
docker-compose up -d --build backend

# Or rebuild everything
docker-compose up -d --build
```

### 4. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### 5. Test
```bash
# Backend tests
docker-compose exec backend pytest

# Or locally
cd rag-research-assistant
venv\Scripts\activate
pytest backend\tests\
```

---

## Common Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps

# Rebuild
docker-compose up -d --build

# Clean everything
docker-compose down -v
```

---

## Troubleshooting

### "Cannot connect to Docker daemon"
→ Start Docker Desktop

### "Port already in use"
→ Stop the conflicting app or change ports in `docker-compose.yml`

### "ChromaDB connection refused"
→ Wait 15 seconds, then: `docker-compose restart backend`

### "GOOGLE_API_KEY not set"
→ Check `.env` file exists and has your API key

---

## Next Steps

### Quick Start
1. Follow the 5-minute setup above
2. Open http://localhost:3000
3. Upload a paper
4. Ask questions!

### Learn More
- **Detailed guide**: [QUICKSTART.md](QUICKSTART.md)
- **Configuration**: [CONFIGURATION.md](CONFIGURATION.md)
- **Architecture**: [README.md](README.md)
- **Production**: [SETUP.md](SETUP.md)

---

## Summary

### Your Original Question
> "Is all of this required or can we just run with Gemini API key for now?"

### Answer
**You can run with just the Gemini API key!**

1. Use `.env.minimal` (not `.env.example`)
2. Set only `GOOGLE_API_KEY`
3. Everything else has working defaults
4. Run `docker-compose up -d`
5. Done! ✅

### What LLM?
**Google Gemini 2.5 Flash** - Fast, accurate, free tier available

### How to Run in Development?
**Docker Compose** (recommended) or **Manual** (for hot-reload)

---

**Ready to start? Go to [START_HERE.md](START_HERE.md)!** 🚀
