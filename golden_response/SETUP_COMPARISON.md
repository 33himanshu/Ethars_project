# Setup Comparison: Minimal vs Full

Visual side-by-side comparison of the two setup approaches.

---

## Setup Steps Comparison

### Minimal Setup (5 minutes)

```bash
# Step 1: Get API key (2 min)
# Visit https://aistudio.google.com/app/apikey

# Step 2: Configure (1 min)
cd rag-research-assistant
copy .env.minimal .env
notepad .env
# → Set GOOGLE_API_KEY only

# Step 3: Start (2 min)
docker-compose up -d

# Step 4: Use it!
# Open http://localhost:3000
```

**Total: 5 minutes** ⚡

---

### Full Setup (30 minutes)

```bash
# Step 1: Get API key (2 min)
# Visit https://aistudio.google.com/app/apikey

# Step 2: Configure (15 min)
cd rag-research-assistant
copy .env.example .env
notepad .env
# → Set 50+ variables:
#   - GOOGLE_API_KEY
#   - POSTGRES_PASSWORD (strong)
#   - REDIS_PASSWORD (strong)
#   - JWT_SECRET_KEY (32+ chars)
#   - APP_SECRET_KEY (32+ chars)
#   - AWS credentials (if using S3)
#   - Database URLs
#   - Performance tuning
#   - Monitoring config
#   - etc.

# Step 3: Generate secrets (5 min)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → Copy to JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → Copy to APP_SECRET_KEY
# ... repeat for other secrets

# Step 4: Review settings (5 min)
# - Check all database URLs
# - Verify AWS credentials
# - Confirm rate limits
# - Review security settings

# Step 5: Start (3 min)
docker-compose up -d

# Step 6: Verify (optional)
# - Check all services healthy
# - Test API endpoints
# - Verify monitoring
```

**Total: 30 minutes** 🐢

---

## Configuration File Comparison

### .env.minimal (5 lines)

```env
# ============================================================================
# MINIMAL .env FOR QUICK START
# ============================================================================

# ─── REQUIRED ──
GOOGLE_API_KEY=your-google-ai-studio-api-key

# ─── OPTIONAL (have working defaults) ──
POSTGRES_PASSWORD=devpass123
REDIS_PASSWORD=devpass123
JWT_SECRET_KEY=dev-jwt-secret-key-min-32-chars-for-development-only
APP_SECRET_KEY=dev-app-secret-key-min-32-chars-for-development-only
```

**Lines to edit: 1** (just the API key)

---

### .env.example (50+ lines)

```env
# ─── Application ───────────────────────────────────────────────────────────────
APP_ENV=development
APP_SECRET_KEY=your-super-secret-key-change-in-production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# ─── Database (PostgreSQL) ──────────────────────────────────────────────────────
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_research
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=your-postgres-password
DATABASE_URL=postgresql+asyncpg://rag_user:your-postgres-password@localhost:5432/rag_research

# ─── Redis ─────────────────────────────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_URL=redis://:your-redis-password@localhost:6379/0

# ─── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL=redis://:your-redis-password@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:your-redis-password@localhost:6379/2

# ─── Google AI Studio (Gemini) ─────────────────────────────────────────────────
GOOGLE_API_KEY=your-google-ai-studio-api-key
GEMINI_MODEL=gemini-2.5-flash

# ─── Embedding Model ───────────────────────────────────────────────────────────
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# ─── ChromaDB ──────────────────────────────────────────────────────────────────
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION=research_papers

# ─── JWT Authentication ────────────────────────────────────────────────────────
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── File Storage ──────────────────────────────────────────────────────────────
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
STORAGE_BACKEND=local
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket
AWS_REGION=us-east-1

# ─── Rate Limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE=20

# ─── Retrieval Settings ────────────────────────────────────────────────────────
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.75
MAX_CONTEXT_TOKENS=6000
RESERVED_RESPONSE_TOKENS=1000
CONVERSATION_HISTORY_TURNS=10
SESSION_TTL_SECONDS=86400

# ─── Monitoring ────────────────────────────────────────────────────────────────
PROMETHEUS_PORT=9090
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=rag-research-assistant

# ─── Frontend ──────────────────────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Lines to edit: 50+** (all the settings)

---

## What You Get

### Minimal Setup

| Feature | Status | Notes |
|---------|--------|-------|
| **Core RAG Pipeline** | ✅ Full | Same as full setup |
| **Hybrid Search** | ✅ Full | Vector + BM25 + re-ranking |
| **LLM Generation** | ✅ Full | Gemini 2.5 Flash streaming |
| **Citation Verification** | ✅ Full | Hallucination prevention |
| **Authentication** | ✅ Basic | JWT with dev secrets |
| **File Upload** | ✅ Local | Saves to disk |
| **Database** | ✅ Docker | PostgreSQL in container |
| **Vector Store** | ✅ Docker | ChromaDB in container |
| **Caching** | ✅ Docker | Redis in container |
| **Monitoring** | ✅ Basic | Prometheus + Grafana |
| **Security** | ⚠️ Dev-grade | Default passwords |
| **Scalability** | ⚠️ Single server | Docker Compose |
| **Cloud Storage** | ❌ No | Local disk only |
| **Custom Tuning** | ⚠️ Limited | Uses defaults |

**Perfect for:** Development, testing, demos, learning

---

### Full Setup

| Feature | Status | Notes |
|---------|--------|-------|
| **Core RAG Pipeline** | ✅ Full | Same as minimal |
| **Hybrid Search** | ✅ Full | Vector + BM25 + re-ranking |
| **LLM Generation** | ✅ Full | Gemini 2.5 Flash streaming |
| **Citation Verification** | ✅ Full | Hallucination prevention |
| **Authentication** | ✅ Production | Strong JWT secrets |
| **File Upload** | ✅ S3 or Local | Configurable |
| **Database** | ✅ Flexible | Docker or external RDS |
| **Vector Store** | ✅ Flexible | Docker or external |
| **Caching** | ✅ Flexible | Docker or ElastiCache |
| **Monitoring** | ✅ Full | Prometheus + Grafana + OTEL |
| **Security** | ✅ Production | Strong passwords, secrets |
| **Scalability** | ✅ Horizontal | Kubernetes ready |
| **Cloud Storage** | ✅ Yes | AWS S3 support |
| **Custom Tuning** | ✅ Full | Every setting configurable |

**Perfect for:** Production, staging, compliance, scale

---

## Performance Comparison

### RAG Pipeline Performance (Identical)

| Metric | Minimal | Full |
|--------|---------|------|
| Query expansion | Same | Same |
| Vector search | Same | Same |
| BM25 search | Same | Same |
| Re-ranking | Same | Same |
| LLM generation | Same | Same |
| Citation verification | Same | Same |
| **End-to-end latency** | **~2s** | **~2s** |

**Both setups have identical RAG performance!**

---

### Infrastructure Performance

| Metric | Minimal | Full |
|--------|---------|------|
| Concurrent users | ~10 | Unlimited (with scaling) |
| File storage | Local disk | S3 (unlimited) |
| Database | Single container | Managed RDS (HA) |
| Caching | Single Redis | ElastiCache (HA) |
| Horizontal scaling | ❌ No | ✅ Yes (Kubernetes) |
| Load balancing | ❌ No | ✅ Yes |
| Auto-scaling | ❌ No | ✅ Yes |

---

## Security Comparison

### Minimal Setup Security

| Aspect | Status | Details |
|--------|--------|---------|
| **Passwords** | ⚠️ Default | `devpass123` |
| **JWT Secret** | ⚠️ Dev | Predictable |
| **App Secret** | ⚠️ Dev | Predictable |
| **HTTPS** | ❌ No | HTTP only |
| **Firewall** | ❌ No | All ports open |
| **Backups** | ❌ No | Manual only |
| **Audit Logs** | ⚠️ Basic | Console logs |
| **Rate Limiting** | ✅ Yes | 20 req/min |

**Safe for:** Local development only

**NOT safe for:** Internet-facing deployments

---

### Full Setup Security

| Aspect | Status | Details |
|--------|--------|---------|
| **Passwords** | ✅ Strong | Random, 32+ chars |
| **JWT Secret** | ✅ Strong | Random, 32+ chars |
| **App Secret** | ✅ Strong | Random, 32+ chars |
| **HTTPS** | ✅ Yes | SSL/TLS configured |
| **Firewall** | ✅ Yes | Restricted ports |
| **Backups** | ✅ Yes | Automated |
| **Audit Logs** | ✅ Full | Structured logging |
| **Rate Limiting** | ✅ Yes | Configurable |

**Safe for:** Production deployments

---

## Cost Comparison

### Minimal Setup (Local)

| Component | Cost |
|-----------|------|
| Google Gemini API | **Free** (60 req/min) |
| Docker containers | **Free** |
| Storage | **Free** (local disk) |
| Compute | **Free** (your laptop) |
| **Total** | **$0/month** |

---

### Full Setup (AWS Example)

| Component | Cost/Month |
|-----------|------------|
| Google Gemini API | **Free** or $0.10/1M tokens |
| EC2 (t3.small) | ~$10 |
| RDS PostgreSQL (db.t3.micro) | ~$15 |
| ElastiCache Redis (cache.t3.micro) | ~$15 |
| S3 Storage (100GB) | ~$1 |
| Data Transfer | ~$5 |
| **Total** | **~$45-50/month** |

**Note:** You can use full setup with Docker (like minimal) for $0, just with production-grade configuration.

---

## Migration Path

### From Minimal to Full

```bash
# 1. Backup current data
docker-compose exec postgres pg_dump -U rag_user rag_research > backup.sql

# 2. Export documents
# (Use API or copy from uploads/ directory)

# 3. Switch to full config
copy .env .env.minimal.backup
copy .env.example .env
notepad .env  # Configure all settings

# 4. Restart with new config
docker-compose down
docker-compose up -d

# 5. Restore data
docker-compose exec -T postgres psql -U rag_user rag_research < backup.sql

# 6. Re-upload documents (if needed)
```

**Downtime:** ~5 minutes

---

## Decision Matrix

### Choose Minimal Setup If:

- ✅ You're trying it for the first time
- ✅ You're developing locally
- ✅ You're learning RAG systems
- ✅ You want to get started in 5 minutes
- ✅ You're running demos
- ✅ Security is not a concern (local only)
- ✅ You don't need cloud storage
- ✅ You're on a budget ($0)

### Choose Full Setup If:

- ✅ You're deploying to production
- ✅ You have real users
- ✅ You need strong security
- ✅ You're using cloud services (AWS, GCP)
- ✅ You need compliance (HIPAA, SOC2)
- ✅ You need horizontal scaling
- ✅ You need high availability
- ✅ You need custom performance tuning

---

## Quick Reference

### Minimal Setup

```bash
# Files
.env.minimal → .env

# Variables to set
GOOGLE_API_KEY=...

# Start
docker-compose up -d

# Time
5 minutes

# Cost
$0

# Security
Dev-grade

# Use case
Development
```

### Full Setup

```bash
# Files
.env.example → .env

# Variables to set
GOOGLE_API_KEY=...
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
JWT_SECRET_KEY=...
APP_SECRET_KEY=...
+ 45 more

# Start
docker-compose up -d

# Time
30 minutes

# Cost
$0 (Docker) or $45/mo (AWS)

# Security
Production-grade

# Use case
Production
```

---

## Still Deciding?

### Quick Test

Answer these questions:

1. **Are you deploying to production?**
   - No → Minimal
   - Yes → Full

2. **Do you have real users?**
   - No → Minimal
   - Yes → Full

3. **Is this internet-facing?**
   - No → Minimal
   - Yes → Full

4. **Do you need compliance?**
   - No → Minimal
   - Yes → Full

5. **Do you want to start in 5 minutes?**
   - Yes → Minimal
   - No → Full

**If you answered "No" to questions 1-4 and "Yes" to question 5:**
→ Use Minimal Setup

**Otherwise:**
→ Use Full Setup

---

## Next Steps

### For Minimal Setup:
1. Go to [QUICKSTART.md](QUICKSTART.md)
2. Follow the 5-minute guide
3. Start using the system!

### For Full Setup:
1. Go to [SETUP.md](SETUP.md)
2. Follow the production guide
3. Configure all settings
4. Deploy!

### Not Sure?
1. Go to [WHICH_SETUP.md](WHICH_SETUP.md)
2. Read the decision guide
3. Choose your path

---

**Remember:** You can always start with minimal and upgrade to full later!
