# Configuration Guide

This document explains the different configuration options for the RAG Research Assistant.

## Two Configuration Approaches

### 1. Minimal Setup (Recommended for Development)

**File**: `.env.minimal`

**What you need**: Just your Google API key!

```env
# ── REQUIRED ──
GOOGLE_API_KEY=your-google-ai-studio-api-key

# ── OPTIONAL (have working defaults) ──
POSTGRES_PASSWORD=devpass123
REDIS_PASSWORD=devpass123
JWT_SECRET_KEY=dev-jwt-secret-key-min-32-chars-for-development-only
APP_SECRET_KEY=dev-app-secret-key-min-32-chars-for-development-only
```

**Use when:**
- ✅ Getting started / testing
- ✅ Local development
- ✅ Learning the system
- ✅ Quick demos

**Setup:**
```bash
copy .env.minimal .env
notepad .env  # Set GOOGLE_API_KEY
docker-compose up -d
```

---

### 2. Full Setup (Required for Production)

**File**: `.env.example`

**What you need**: 50+ environment variables for complete control

**Use when:**
- ✅ Deploying to production
- ✅ Multi-environment setup (dev/staging/prod)
- ✅ Custom infrastructure (AWS S3, external databases)
- ✅ Advanced tuning and optimization

**Setup:**
```bash
copy .env.example .env
notepad .env  # Configure all variables
docker-compose up -d
```

---

## Configuration Variables Reference

### Critical (Required)

| Variable | Description | Minimal | Full |
|----------|-------------|---------|------|
| `GOOGLE_API_KEY` | Google AI Studio API key | ✅ Required | ✅ Required |

### Application

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `APP_ENV` | Environment name | `development` | Set to `production` for prod |
| `APP_SECRET_KEY` | App encryption key | `change-me` | **Must change for production** |
| `APP_DEBUG` | Debug mode | `false` | Set `true` for verbose logs |
| `APP_HOST` | Bind address | `0.0.0.0` | Usually keep default |
| `APP_PORT` | API port | `8000` | Change if port conflict |

### Database (PostgreSQL)

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `POSTGRES_HOST` | Database host | `localhost` | External DB: set hostname |
| `POSTGRES_PORT` | Database port | `5432` | Custom port |
| `POSTGRES_DB` | Database name | `rag_research` | Custom DB name |
| `POSTGRES_USER` | Database user | `rag_user` | Custom username |
| `POSTGRES_PASSWORD` | Database password | `password` | **Must change for production** |
| `DATABASE_URL` | Full connection URL | Auto-generated | Override for custom setup |

**Docker Compose Note**: When using docker-compose, the host should be the service name (e.g., `postgres` not `localhost`). The docker-compose.yml handles this automatically via environment variable overrides.

### Redis

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `REDIS_HOST` | Redis host | `localhost` | External Redis: set hostname |
| `REDIS_PORT` | Redis port | `6379` | Custom port |
| `REDIS_PASSWORD` | Redis password | `password` | **Must change for production** |
| `REDIS_URL` | Full connection URL | Auto-generated | Override for custom setup |

### Celery (Background Tasks)

| Variable | Description | Default |
|----------|-------------|---------|
| `CELERY_BROKER_URL` | Task queue URL | `redis://...` |
| `CELERY_RESULT_BACKEND` | Result storage URL | `redis://...` |

### Google Gemini (LLM)

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `GOOGLE_API_KEY` | API key | **Required** | Get from https://aistudio.google.com |
| `GEMINI_MODEL` | Model name | `gemini-2.5-flash` | `gemini-2.5-flash`, `gemini-2.0-flash-exp`, `gemini-1.5-pro` |

**Model Comparison:**

| Model | Speed | Cost | Context | Best For |
|-------|-------|------|---------|----------|
| `gemini-2.5-flash` | ⚡ Fastest | Free tier | 1M tokens | Development, most queries |
| `gemini-2.0-flash-exp` | ⚡ Fast | Free tier | 1M tokens | Experimental features |
| `gemini-1.5-pro` | 🐢 Slower | Paid | 2M tokens | Complex reasoning |

### Embeddings

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `EMBEDDING_MODEL` | Sentence transformer | `all-MiniLM-L6-v2` | Better quality: `all-mpnet-base-v2` |
| `EMBEDDING_DIMENSION` | Vector dimensions | `384` | Must match model |
| `CHUNK_SIZE` | Tokens per chunk | `512` | Larger: more context, slower |
| `CHUNK_OVERLAP` | Overlap tokens | `50` | Increase for better continuity |

**Embedding Model Options:**

| Model | Dimensions | Speed | Quality | RAM |
|-------|------------|-------|---------|-----|
| `all-MiniLM-L6-v2` | 384 | ⚡ Fast | Good | ~90MB |
| `all-mpnet-base-v2` | 768 | 🐢 Slower | Better | ~420MB |
| `multi-qa-mpnet-base-dot-v1` | 768 | 🐢 Slower | Best for Q&A | ~420MB |

### ChromaDB (Vector Store)

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `CHROMA_HOST` | ChromaDB host | `localhost` | External ChromaDB |
| `CHROMA_PORT` | ChromaDB port | `8001` | Custom port |
| `CHROMA_COLLECTION` | Collection name | `research_papers` | Multiple collections |

### JWT Authentication

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `JWT_SECRET_KEY` | Token signing key | `change-me-jwt` | **Must change for production** |
| `JWT_ALGORITHM` | Signing algorithm | `HS256` | Usually keep default |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` | Shorter for higher security |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` | Longer for convenience |

**Security Note**: JWT secrets should be:
- At least 32 characters
- Randomly generated
- Never committed to git
- Different for each environment

### File Storage

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `UPLOAD_DIR` | Local storage path | `./uploads` | Custom path |
| `MAX_FILE_SIZE_MB` | Max upload size | `50` | Larger papers |
| `STORAGE_BACKEND` | Storage type | `local` | Set to `s3` for production |
| `AWS_ACCESS_KEY_ID` | AWS key | - | When using S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS secret | - | When using S3 |
| `AWS_S3_BUCKET` | S3 bucket name | - | When using S3 |
| `AWS_REGION` | AWS region | `us-east-1` | Your region |

### Rate Limiting

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | `20` | Higher for production |

**Recommended Values:**
- Development: `20`
- Production (free tier): `60`
- Production (paid): `100+`

### Retrieval Settings

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `TOP_K_RETRIEVAL` | Results after re-ranking | `5` | More context: `10` |
| `SIMILARITY_THRESHOLD` | Min relevance score | `0.75` | Lower for more results: `0.5` |
| `MAX_CONTEXT_TOKENS` | Max LLM context | `6000` | Adjust for model limits |
| `RESERVED_RESPONSE_TOKENS` | Buffer for response | `1000` | Longer answers: `2000` |

**Tuning Guide:**

| Use Case | TOP_K | SIMILARITY_THRESHOLD |
|----------|-------|---------------------|
| Precise answers | `3-5` | `0.75-0.85` |
| Broad exploration | `10-15` | `0.5-0.65` |
| Balanced (default) | `5` | `0.75` |

### Memory (Conversation History)

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `CONVERSATION_HISTORY_TURNS` | Turns to remember | `10` | More context: `20` |
| `SESSION_TTL_SECONDS` | Session expiry | `86400` (24h) | Longer sessions |

### Monitoring

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_PORT` | Metrics port | `9090` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry endpoint | `http://localhost:4317` |
| `OTEL_SERVICE_NAME` | Service name | `rag-research-assistant` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |

---

## Environment-Specific Configurations

### Development

```env
APP_ENV=development
APP_DEBUG=true
RATE_LIMIT_PER_MINUTE=100
SIMILARITY_THRESHOLD=0.5
```

### Staging

```env
APP_ENV=staging
APP_DEBUG=false
RATE_LIMIT_PER_MINUTE=60
SIMILARITY_THRESHOLD=0.75
```

### Production

```env
APP_ENV=production
APP_DEBUG=false
RATE_LIMIT_PER_MINUTE=100
SIMILARITY_THRESHOLD=0.75

# Strong secrets (example - generate your own!)
APP_SECRET_KEY=prod-secret-key-32-chars-minimum-random-string-here
JWT_SECRET_KEY=prod-jwt-secret-32-chars-minimum-random-string-here
POSTGRES_PASSWORD=strong-random-password-here
REDIS_PASSWORD=strong-random-password-here

# Production storage
STORAGE_BACKEND=s3
AWS_S3_BUCKET=my-rag-papers-prod
AWS_REGION=us-east-1

# External services
POSTGRES_HOST=my-rds-instance.region.rds.amazonaws.com
REDIS_HOST=my-elasticache.region.cache.amazonaws.com
CHROMA_HOST=my-chromadb-service.internal
```

---

## How Defaults Work

When you use `.env.minimal`, the system loads defaults from `backend/config.py`:

```python
class Settings(BaseSettings):
    # These are the fallback values
    app_env: str = "development"
    postgres_password: str = "password"
    redis_password: str = "password"
    gemini_model: str = "gemini-2.5-flash"
    # ... etc
```

**Priority Order:**
1. Environment variables (highest)
2. `.env` file values
3. `backend/config.py` defaults (lowest)

This means:
- Docker Compose can override via `environment:` section
- You can override via shell: `export GEMINI_MODEL=gemini-1.5-pro`
- Defaults are used if nothing else is set

---

## Security Checklist for Production

Before deploying to production, ensure:

- [ ] `GOOGLE_API_KEY` is set and valid
- [ ] `APP_SECRET_KEY` is 32+ random characters
- [ ] `JWT_SECRET_KEY` is 32+ random characters
- [ ] `POSTGRES_PASSWORD` is strong and unique
- [ ] `REDIS_PASSWORD` is strong and unique
- [ ] `APP_DEBUG=false`
- [ ] `APP_ENV=production`
- [ ] `STORAGE_BACKEND=s3` (not local)
- [ ] Database backups are configured
- [ ] HTTPS is enabled (via reverse proxy)
- [ ] Firewall rules are configured
- [ ] Monitoring and alerting are set up
- [ ] Rate limiting is appropriate for your scale

---

## Generating Secure Secrets

**Python:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**OpenSSL:**
```bash
openssl rand -base64 32
```

---

## Troubleshooting Configuration

### "GOOGLE_API_KEY not set"
- Check `.env` file exists in project root
- Verify the key is on the line: `GOOGLE_API_KEY=AIzaSy...`
- No quotes needed around the value
- Restart docker-compose: `docker-compose restart backend`

### "Database connection failed"
- Check `POSTGRES_PASSWORD` matches in `.env` and docker-compose
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check logs: `docker-compose logs postgres`

### "Redis connection refused"
- Check `REDIS_PASSWORD` matches
- Verify Redis is running: `docker-compose ps redis`
- Test connection: `docker-compose exec redis redis-cli -a yourpassword ping`

### "ChromaDB not found"
- Wait 15 seconds after starting (ChromaDB takes time to initialize)
- Restart backend: `docker-compose restart backend`
- Check logs: `docker-compose logs chromadb`

### "Invalid JWT token"
- Token expired (30 min default) - use refresh endpoint
- `JWT_SECRET_KEY` changed - all tokens invalidated
- Token from different environment - can't mix dev/prod tokens

---

## Next Steps

- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Full Setup**: See [SETUP.md](SETUP.md)
- **Architecture**: See [README.md](README.md)
- **API Reference**: http://localhost:8000/docs (when running)
