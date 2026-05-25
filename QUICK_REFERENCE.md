# RAG Research Assistant - Quick Reference

## 🚀 Quick Start Commands

### Start Everything (Docker)
```bash
docker-compose up -d
```

### Stop Everything
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Restart a Service
```bash
docker-compose restart backend
docker-compose restart chromadb
```

---

## 🔗 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Register new account |
| **Backend API** | http://localhost:8000 | JWT token required |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Prometheus** | http://localhost:9090 | No auth |
| **Grafana** | http://localhost:3001 | admin / admin |
| **PostgreSQL** | localhost:5432 | See .env |
| **Redis** | localhost:6379 | See .env |
| **ChromaDB** | localhost:8001 | No auth |

---

## 📝 Common Tasks

### Register a New User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@example.com",
    "username": "researcher",
    "password": "SecurePass123"
  }'
```

### Login and Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@example.com",
    "password": "SecurePass123"
  }'
```

### Upload a Document
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@paper.pdf"
```

### List Documents
```bash
curl http://localhost:8000/api/documents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Search (Non-Streaming)
```bash
curl "http://localhost:8000/api/search?q=attention+mechanism&top_k=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🐛 Troubleshooting Quick Fixes

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Common fix: restart dependencies
docker-compose restart postgres redis chromadb
sleep 10
docker-compose restart backend
```

### ChromaDB Connection Issues
```bash
docker-compose restart chromadb
sleep 15
docker-compose restart backend celery-worker
```

### Frontend Build Errors
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Clear Redis Cache
```bash
docker-compose exec redis redis-cli -a YOUR_REDIS_PASSWORD FLUSHALL
```

---

## 📊 Monitoring Commands

### Check Service Health
```bash
curl http://localhost:8000/health
```

### View Metrics
```bash
curl http://localhost:8000/metrics
```

### Check Database Connection
```bash
docker-compose exec postgres psql -U rag_user -d rag_research -c "SELECT COUNT(*) FROM documents;"
```

### Check ChromaDB Collections
```bash
curl http://localhost:8001/api/v1/collections
```

### Check Redis Keys
```bash
docker-compose exec redis redis-cli -a YOUR_REDIS_PASSWORD KEYS "*"
```

---

## 🧪 Testing Commands

### Run All Backend Tests
```bash
pytest backend/tests/ -v
```

### Run Specific Test File
```bash
pytest backend/tests/test_retrieval.py -v
```

### Run with Coverage
```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

### Run Evaluation
```bash
export EVAL_AUTH_TOKEN="your-jwt-token"
python -m evaluation.evaluator
```

---

## 🔧 Development Commands

### Backend Development
```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker
celery -A backend.ingestion.tasks.celery_app worker --loglevel=info
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Format Code
```bash
# Python
black backend/
isort backend/

# TypeScript
cd frontend
npm run lint
```

---

## 📦 Environment Variables (Critical)

```env
# Required
GOOGLE_API_KEY=your-google-ai-studio-api-key
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-secure-password
JWT_SECRET_KEY=your-long-random-jwt-secret
APP_SECRET_KEY=your-long-random-app-secret

# Optional (with defaults)
SIMILARITY_THRESHOLD=0.75
TOP_K_RETRIEVAL=5
RATE_LIMIT_PER_MINUTE=20
MAX_FILE_SIZE_MB=50
```

---

## 🎯 Performance Targets

| Metric | Target | Check |
|--------|--------|-------|
| p95 Retrieval Latency | < 500ms | Prometheus |
| p95 E2E Latency | < 2000ms | Prometheus |
| Hallucination Rate | < 5% | Evaluation |
| Retrieval Precision@5 | > 0.80 | Evaluation |

---

## 📞 Getting Help

1. **Check logs:** `docker-compose logs -f backend`
2. **Review docs:** README.md, SETUP.md
3. **API reference:** http://localhost:8000/docs
4. **Troubleshooting:** SETUP.md (Troubleshooting section)

---

## 🔐 Security Checklist

Before production:
- [ ] Change all default passwords in `.env`
- [ ] Use strong JWT secrets (32+ chars)
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Set up PostgreSQL backups
- [ ] Review rate limits
- [ ] Enable monitoring alerts

---

## 📚 File Locations

| What | Where |
|------|-------|
| Backend code | `backend/` |
| Frontend code | `frontend/` |
| Tests | `backend/tests/` |
| Docker configs | `deployment/docker/` |
| Kubernetes | `deployment/kubernetes/` |
| Evaluation | `evaluation/` |
| Logs | `docker-compose logs` |
| Uploads | `./uploads/` (or S3) |

---

## 💡 Tips

- **First time?** Run `scripts/setup.bat` (Windows) or `scripts/setup.sh` (Mac/Linux)
- **Slow queries?** Lower `SIMILARITY_THRESHOLD` to 0.5 for testing
- **Out of memory?** Reduce Celery concurrency: `--concurrency=1`
- **Need more results?** Increase `TOP_K_RETRIEVAL` in `.env`
- **Token limit hit?** Reduce `MAX_CONTEXT_TOKENS` or `CHUNK_SIZE`

---

**Last Updated:** 2024  
**Version:** 1.0.0  
**Status:** Production Ready ✅
