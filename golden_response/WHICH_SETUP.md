# Which Setup Should I Use?

Quick guide to choosing between minimal and full configuration.

## TL;DR

- **Just testing?** → Use `.env.minimal` (5 minutes)
- **Going to production?** → Use `.env.example` (30 minutes)

---

## Comparison Table

| Feature | Minimal Setup | Full Setup |
|---------|---------------|------------|
| **Setup Time** | 5 minutes | 30 minutes |
| **Variables to Set** | 1 (just API key) | 50+ |
| **Best For** | Development, testing, demos | Production, staging, custom infra |
| **Security** | Basic (dev passwords) | Production-grade |
| **Customization** | Limited (uses defaults) | Full control |
| **File Storage** | Local disk | Local or AWS S3 |
| **Database** | Docker PostgreSQL | Docker or external RDS |
| **Monitoring** | Basic | Full Prometheus + Grafana |
| **Documentation** | [QUICKSTART.md](QUICKSTART.md) | [SETUP.md](SETUP.md) |

---

## Decision Tree

```
Are you deploying to production?
│
├─ NO → Use .env.minimal
│   │
│   └─ Just want to try it out?
│      ├─ YES → Use .env.minimal (5 min setup)
│      └─ NO → Building a feature?
│         └─ YES → Use .env.minimal (can upgrade later)
│
└─ YES → Use .env.example
    │
    └─ Need custom infrastructure?
       ├─ YES → Use .env.example (full control)
       └─ NO → Use .env.example (security required)
```

---

## Use Minimal Setup When...

✅ You're trying the system for the first time
✅ You're developing locally
✅ You're running demos or presentations
✅ You're learning how RAG works
✅ You're testing new features
✅ You're running on your laptop
✅ Security is not a concern (local only)
✅ You want to get started in 5 minutes

**What you get:**
- Working system with sensible defaults
- All features enabled
- Docker handles everything
- Development-grade security (fine for local use)

**What you don't get:**
- Production-grade security
- Custom infrastructure integration
- Fine-grained performance tuning
- Multi-environment support

---

## Use Full Setup When...

✅ You're deploying to production
✅ You're setting up staging/QA environments
✅ You need strong security (real users)
✅ You're using external services (AWS RDS, S3, etc.)
✅ You need custom performance tuning
✅ You're integrating with existing infrastructure
✅ You need compliance (HIPAA, SOC2, etc.)
✅ You're scaling beyond a single server

**What you get:**
- Production-grade security
- Full control over every setting
- Integration with cloud services
- Performance optimization options
- Multi-environment configuration
- Compliance-ready setup

**What you need:**
- 30 minutes to configure
- Understanding of your infrastructure
- Strong passwords and secrets
- Cloud service accounts (if using AWS, etc.)

---

## Can I Upgrade Later?

**Yes!** You can start with minimal and upgrade to full setup anytime.

### Migration Path

1. **Start with minimal** (`.env.minimal`)
   ```bash
   copy .env.minimal .env
   # Set GOOGLE_API_KEY
   docker-compose up -d
   ```

2. **Develop and test** your application

3. **When ready for production**, switch to full:
   ```bash
   # Backup your current .env
   copy .env .env.minimal.backup
   
   # Copy full template
   copy .env.example .env
   
   # Migrate your settings
   # - Copy GOOGLE_API_KEY from backup
   # - Generate new strong passwords
   # - Configure production services
   
   # Restart with new config
   docker-compose down
   docker-compose up -d
   ```

**Data Migration:**
- Export documents from old setup
- Re-upload to new setup
- Or migrate PostgreSQL/ChromaDB data directly

---

## What About Staging/QA?

For staging environments, use **full setup** with:
- Separate `.env.staging` file
- Staging-specific secrets (different from prod)
- Same infrastructure as production (but smaller)
- Relaxed rate limits for testing

```bash
# Use environment-specific config
docker-compose --env-file .env.staging up -d
```

---

## Security Considerations

### Minimal Setup Security

**Safe for:**
- ✅ Local development on your laptop
- ✅ Internal demos (no internet exposure)
- ✅ Learning and experimentation

**NOT safe for:**
- ❌ Production with real users
- ❌ Internet-facing deployments
- ❌ Sensitive data processing
- ❌ Compliance requirements

**Why?**
- Uses default passwords (`devpass123`)
- Uses development secrets
- No external authentication
- Local file storage only

### Full Setup Security

**Provides:**
- ✅ Strong random passwords
- ✅ Production-grade JWT secrets
- ✅ Encrypted connections
- ✅ Cloud storage (S3)
- ✅ External database support
- ✅ Rate limiting
- ✅ Audit logging

---

## Cost Considerations

### Minimal Setup Costs

| Service | Cost |
|---------|------|
| Google Gemini API | **Free tier** (60 req/min) |
| Docker containers | **Free** (local) |
| Storage | **Free** (local disk) |
| **Total** | **$0/month** |

### Full Setup Costs (Example AWS)

| Service | Cost (estimate) |
|---------|-----------------|
| Google Gemini API | **Free tier** or $0.10/1M tokens |
| AWS RDS (PostgreSQL) | ~$15/month (db.t3.micro) |
| AWS ElastiCache (Redis) | ~$15/month (cache.t3.micro) |
| AWS S3 | ~$1/month (100GB) |
| AWS EC2 (app server) | ~$10/month (t3.small) |
| **Total** | **~$40-50/month** |

**Note:** You can still use Docker for everything (like minimal setup) but with production-grade configuration. This costs $0 but requires your own server.

---

## Performance Comparison

Both setups have **identical performance** for the core RAG pipeline:
- Same retrieval speed
- Same LLM generation speed
- Same embedding quality

**Differences:**
- Full setup can use faster embedding models (more RAM)
- Full setup can scale horizontally (multiple servers)
- Full setup can use CDN for frontend (faster loading)

---

## Quick Reference

### Minimal Setup Commands

```bash
# Setup
copy .env.minimal .env
notepad .env  # Set GOOGLE_API_KEY

# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f backend

# Reset everything
docker-compose down -v
```

### Full Setup Commands

```bash
# Setup
copy .env.example .env
notepad .env  # Configure all variables

# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f backend

# Backup data
docker-compose exec postgres pg_dump -U rag_user rag_research > backup.sql

# Restore data
docker-compose exec -T postgres psql -U rag_user rag_research < backup.sql
```

---

## Still Not Sure?

### Start with Minimal if:
- You answered "no" to "deploying to production?"
- You want to try it out first
- You're learning RAG systems
- You're on a tight deadline

### Use Full if:
- You answered "yes" to "deploying to production?"
- You have real users
- You're handling sensitive data
- You need compliance

### When in doubt:
**Start minimal, upgrade later!** It's easier to add complexity than remove it.

---

## Getting Help

- **Minimal Setup Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Full Setup Guide**: [SETUP.md](SETUP.md)
- **Configuration Reference**: [CONFIGURATION.md](CONFIGURATION.md)
- **Architecture Overview**: [README.md](README.md)

---

**Ready to start?**

- 👉 **Minimal**: Go to [QUICKSTART.md](QUICKSTART.md)
- 👉 **Full**: Go to [SETUP.md](SETUP.md)
