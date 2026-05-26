# Quick Start Guide - 5 Minutes to Running

Get the RAG Research Assistant running with just your Google API key!

## Prerequisites

- **Docker Desktop** installed and running
- **Google API Key** (free): Get yours at https://aistudio.google.com/app/apikey

That's it! No Python, Node.js, or other tools needed.

---

## Step 1: Get Your Google API Key (2 minutes)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)

---

## Step 2: Configure (1 minute)

```bash
# Navigate to the project
cd rag-research-assistant

# Copy the minimal config
copy .env.minimal .env

# Edit .env and paste your API key
notepad .env
```

Replace `your-google-ai-studio-api-key` with your actual key:

```env
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

Save and close. **That's all you need to change!**

---

## Step 3: Start Everything (2 minutes)

```bash
docker-compose up -d
```

This downloads and starts:
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ ChromaDB vector store
- ✅ Backend API
- ✅ Celery worker
- ✅ Frontend UI
- ✅ Monitoring tools

First run takes ~2 minutes to download images. Subsequent starts take ~10 seconds.

---

## Step 4: Verify It's Running

```bash
# Check all services are healthy
docker-compose ps
```

You should see all services with status "Up" or "Up (healthy)".

---

## Step 5: Open the App

Open your browser to: **http://localhost:3000**

### Create Your Account
1. Click "Register"
2. Enter email, username, password
3. Click "Sign Up"

### Upload a Paper
1. Go to "Upload Papers" tab
2. Drag and drop a PDF (or click to browse)
3. Wait for "Processing complete" status

### Ask Questions
1. Go to "Research Chat" tab
2. Type your question
3. Watch the AI stream its answer with citations!

---

## Example Questions to Try

After uploading "Attention Is All You Need" paper:

- "What is the main contribution of this paper?"
- "Explain the multi-head attention mechanism"
- "What are the advantages over RNNs?"
- "What datasets were used for evaluation?"

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main UI |
| **API Docs** | http://localhost:8000/docs | Interactive API |
| **Health Check** | http://localhost:8000/health | System status |
| **Prometheus** | http://localhost:9090 | Metrics |
| **Grafana** | http://localhost:3001 | Dashboards (admin/admin) |

---

## Common Commands

```bash
# Stop everything
docker-compose down

# Start again
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart a specific service
docker-compose restart backend

# Check what's using disk space
docker system df

# Clean up old images (frees space)
docker system prune
```

---

## Troubleshooting

### "Cannot connect to Docker daemon"
- Make sure Docker Desktop is running
- Windows: Check system tray for Docker icon

### "Port already in use"
- Another app is using port 3000, 8000, or 5432
- Stop the conflicting app or change ports in `docker-compose.yml`

### "ChromaDB connection refused"
```bash
# Wait 15 seconds for ChromaDB to fully start, then:
docker-compose restart backend
```

### "No documents found" after upload
- Check upload status: Go to "Upload Papers" tab
- View logs: `docker-compose logs -f celery-worker`

### "I cannot find sufficient evidence" for all queries
- Make sure your document shows "Indexed" status
- Try lowering the similarity threshold (advanced users):
  - Add to `.env`: `SIMILARITY_THRESHOLD=0.5`
  - Restart: `docker-compose restart backend`

---

## What's Using the Defaults?

Since you only set `GOOGLE_API_KEY`, everything else uses these defaults:

| Setting | Default Value | What It Does |
|---------|---------------|--------------|
| `POSTGRES_PASSWORD` | `devpass123` | Database password |
| `REDIS_PASSWORD` | `devpass123` | Cache password |
| `JWT_SECRET_KEY` | `dev-jwt-secret-key-...` | Auth token signing |
| `APP_SECRET_KEY` | `dev-app-secret-key-...` | App encryption |
| `GEMINI_MODEL` | `gemini-2.5-flash` | AI model (fast & free) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Text embeddings |
| `TOP_K_RETRIEVAL` | `5` | Results per query |
| `SIMILARITY_THRESHOLD` | `0.75` | Min relevance score |

**These defaults are fine for development and testing!**

⚠️ **For production:** Use the full `.env.example` with strong passwords and secrets.

---

## Next Steps

### Upload More Papers
Build your research corpus by uploading multiple PDFs. The system handles:
- Text-based PDFs (fast)
- Scanned PDFs (OCR, slower)
- Papers up to 50MB

### Explore the API
Visit http://localhost:8000/docs for:
- Interactive API testing
- Authentication endpoints
- Document management
- Search and chat endpoints

### Monitor Performance
- **Prometheus**: http://localhost:9090 - Raw metrics
- **Grafana**: http://localhost:3001 - Visual dashboards (login: admin/admin)

### Run Evaluation
Test system accuracy with the benchmark dataset:

```bash
# Get your JWT token from the frontend (browser dev tools)
# Or login via API:
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'

# Set token and run evaluation
set EVAL_AUTH_TOKEN=your-jwt-token
python -m evaluation.evaluator
```

---

## Understanding the Architecture

```
Your Question
    ↓
Frontend (Next.js) → Backend (FastAPI)
    ↓
Query Expansion (3 variants via Gemini)
    ↓
Hybrid Search (Vector + BM25)
    ↓
Re-ranking (Cross-encoder)
    ↓
Context Assembly (Top 5 chunks)
    ↓
LLM Generation (Gemini 2.5 Flash)
    ↓
Citation Verification
    ↓
Streaming Answer with Sources
```

**Data Stores:**
- **PostgreSQL**: User accounts, document metadata
- **ChromaDB**: Vector embeddings for semantic search
- **Redis**: Session history, caching

---

## Getting Help

- **Full Documentation**: See `README.md`
- **Detailed Setup**: See `SETUP.md`
- **View Logs**: `docker-compose logs -f [service-name]`
- **Check Health**: http://localhost:8000/health

---

## Clean Up

When you're done experimenting:

```bash
# Stop and remove containers (keeps data)
docker-compose down

# Remove everything including data volumes
docker-compose down -v

# Remove downloaded images (frees ~2GB)
docker-compose down --rmi all -v
```

---

**You're all set! Happy researching! 🚀**
