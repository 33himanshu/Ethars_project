# RAG Research Assistant - Setup Guide

Complete step-by-step setup instructions for local development and production deployment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Manual Setup](#manual-setup)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Node.js** 20+ and **npm** 9+
- **Python** 3.11+
- **Git**

### API Keys
- **Google AI Studio API Key** (free): https://aistudio.google.com/app/apikey

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **OS**: Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+)

---

## Quick Start (Docker)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd rag-research-assistant
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your API key
# Windows: notepad .env
# Mac/Linux: nano .env
```

**Required changes in `.env`:**
```env
GOOGLE_API_KEY=your-actual-google-ai-studio-api-key
POSTGRES_PASSWORD=your-secure-password-here
REDIS_PASSWORD=your-secure-password-here
JWT_SECRET_KEY=your-long-random-jwt-secret-at-least-32-chars
APP_SECRET_KEY=your-long-random-app-secret-at-least-32-chars
```

### 3. Start All Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- ChromaDB (port 8001)
- Backend API (port 8000)
- Celery Worker
- Frontend (port 3000)
- Prometheus (port 9090)
- Grafana (port 3001)

### 4. Verify Installation
```bash
# Check all containers are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Open the application
# Windows: start http://localhost:3000
# Mac: open http://localhost:3000
# Linux: xdg-open http://localhost:3000
```

### 5. Create Your First User
Open http://localhost:3000 and click "Register" to create an account.

### 6. Upload a Test Document
1. Download "Attention Is All You Need" PDF
2. Go to "Upload Papers" tab
3. Drag and drop the PDF
4. Wait for processing (check status in the UI)

### 7. Ask Your First Question
Go to "Research Chat" and ask:
```
What attention mechanism is proposed in this paper?
```

---

## Manual Setup

### Backend Setup

#### 1. Install Python Dependencies
```bash
cd rag-research-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

#### 2. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libpq-dev
```

**macOS:**
```bash
brew install tesseract postgresql
```

**Windows:**
- Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH

#### 3. Start Required Services

**PostgreSQL:**
```bash
# Using Docker
docker run -d --name rag-postgres \
  -e POSTGRES_DB=rag_research \
  -e POSTGRES_USER=rag_user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:16-alpine

# Initialize schema
docker exec -i rag-postgres psql -U rag_user -d rag_research < backend/database/schema/001_initial.sql
```

**Redis:**
```bash
docker run -d --name rag-redis \
  -p 6379:6379 \
  redis:7-alpine redis-server --requirepass password
```

**ChromaDB:**
```bash
docker run -d --name rag-chromadb \
  -p 8001:8000 \
  -e ANONYMIZED_TELEMETRY=false \
  chromadb/chroma:latest
```

#### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

#### 5. Start Backend
```bash
# Terminal 1: API Server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery Worker
celery -A backend.ingestion.tasks.celery_app worker --loglevel=info
```

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Configure Environment
```bash
# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

#### 3. Start Development Server
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

---

## Configuration

### Environment Variables Reference

#### Critical Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI Studio API key | `AIzaSy...` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://:password@localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing secret (32+ chars) | `your-secret-key` |

#### Retrieval Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `SIMILARITY_THRESHOLD` | Min similarity for grounding | `0.75` |
| `TOP_K_RETRIEVAL` | Results after re-ranking | `5` |
| `CHUNK_SIZE` | Tokens per chunk | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |

#### Performance Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_PER_MINUTE` | API rate limit per user | `20` |
| `MAX_CONTEXT_TOKENS` | Max LLM context | `6000` |
| `MAX_FILE_SIZE_MB` | Max PDF upload size | `50` |

---

## Testing

### Run Backend Tests
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_retrieval.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

### Run Frontend Tests
```bash
cd frontend
npm run lint
npm run build  # Checks for TypeScript errors
```

### Run Evaluation
```bash
# Set your auth token
export EVAL_AUTH_TOKEN="your-jwt-token"

# Run evaluation
python -m evaluation.evaluator
```

---

## Troubleshooting

### Issue: "lucide-react" TypeScript Error

**Solution:**
```bash
cd frontend
npm install
# If still failing:
rm -rf node_modules package-lock.json
npm install
```

### Issue: ChromaDB Connection Refused

**Solution:**
```bash
# Check ChromaDB is running
docker ps | grep chromadb

# Restart ChromaDB
docker-compose restart chromadb

# Wait 15 seconds, then restart backend
docker-compose restart backend
```

### Issue: Embedding Model Download Fails

**Solution:**
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Issue: PDF Parsing Fails

**Symptoms:** "Failed to parse PDF" error

**Solutions:**
1. **Check Tesseract installation:**
   ```bash
   tesseract --version
   ```

2. **For scanned PDFs:** System auto-falls back to OCR (slower)

3. **Check file size:** Max 50MB by default

### Issue: "Cannot find sufficient evidence" for All Queries

**Solutions:**
1. **Verify documents are indexed:**
   ```bash
   curl http://localhost:8000/api/documents?status=indexed \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Lower similarity threshold (for testing):**
   ```env
   SIMILARITY_THRESHOLD=0.5
   ```

3. **Check ChromaDB has chunks:**
   ```bash
   docker exec rag-chromadb curl localhost:8000/api/v1/collections
   ```

### Issue: High Memory Usage

**Solutions:**
- Reduce Celery concurrency: `--concurrency=1`
- Limit Docker memory: Add to docker-compose.yml:
  ```yaml
  services:
    backend:
      mem_limit: 2g
  ```

### Issue: Rate Limit Errors (429)

**Solution:**
Increase in `.env`:
```env
RATE_LIMIT_PER_MINUTE=50
```

### Issue: JWT Token Expired

**Solution:**
Access tokens expire in 30 minutes. Use the refresh endpoint:
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

---

## Next Steps

1. **Upload more papers** to build your research corpus
2. **Explore the API** at http://localhost:8000/docs
3. **Monitor metrics** at http://localhost:9090 (Prometheus) and http://localhost:3001 (Grafana)
4. **Run evaluation** to measure system performance
5. **Deploy to production** using Kubernetes manifests in `deployment/kubernetes/`

---

## Getting Help

- **Documentation:** See README.md for architecture details
- **API Reference:** http://localhost:8000/docs
- **Logs:** `docker-compose logs -f backend`
- **Issues:** Check the troubleshooting section above

---

## Security Notes

⚠️ **Before deploying to production:**

1. Change all default passwords in `.env`
2. Use strong JWT secrets (32+ random characters)
3. Enable HTTPS with valid SSL certificates
4. Configure firewall rules
5. Set up backup for PostgreSQL
6. Review rate limiting settings
7. Enable monitoring and alerting
