# 🚀 START HERE - RAG Research Assistant

Welcome! This guide will get you up and running in 5 minutes.

---

## What Is This?

An AI-powered research assistant that:
- 📄 Reads your PDF research papers
- 🔍 Finds relevant information using hybrid search
- 💬 Answers questions with citations
- ✅ Prevents hallucinations with grounding checks
- ⚡ Streams responses in real-time

**Powered by Google Gemini 2.5 Flash** - Fast, accurate, and free!

---

## Quick Start (5 Minutes)

### Step 1: Get Google API Key (2 min)
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)

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

Save and close. **Done!**

### Step 3: Start (2 min)
```bash
docker-compose up -d
```

### Step 4: Use It!
Open http://localhost:3000

1. **Register** an account
2. **Upload** a PDF paper
3. **Ask** questions!

**That's it!** 🎉

---

## What Just Happened?

You now have a complete RAG system running:

```
┌─────────────────────────────────────────┐
│  Frontend (Next.js)                     │
│  http://localhost:3000                  │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Backend API (FastAPI)                  │
│  http://localhost:8000                  │
│                                         │
│  • Query Expansion (Gemini)             │
│  • Hybrid Search (Vector + BM25)        │
│  • Re-ranking (Cross-encoder)           │
│  • Generation (Gemini 2.5 Flash)        │
│  • Citation Verification                │
└─────────────────────────────────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Postgres│ │ChromaDB│ │ Redis  │
│ Users  │ │Vectors │ │Sessions│
└────────┘ └────────┘ └────────┘
```

---

## Try These Questions

After uploading "Attention Is All You Need" paper:

1. "What is the main contribution of this paper?"
2. "Explain the multi-head attention mechanism"
3. "What are the advantages over RNNs?"
4. "What datasets were used for evaluation?"
5. "How does positional encoding work?"

---

## What's Running?

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main UI |
| **API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Interactive API |
| **Health** | http://localhost:8000/health | System status |
| **Prometheus** | http://localhost:9090 | Metrics |
| **Grafana** | http://localhost:3001 | Dashboards |

---

## Common Commands

```bash
# Stop everything
docker-compose down

# Start again
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps

# Restart a service
docker-compose restart backend
```

---

## Need Help?

### "Cannot connect to Docker daemon"
→ Make sure Docker Desktop is running

### "Port already in use"
→ Another app is using the port. Stop it or change ports in `docker-compose.yml`

### "ChromaDB connection refused"
→ Wait 15 seconds, then: `docker-compose restart backend`

### "No documents found"
→ Check upload status in the "Upload Papers" tab

### More help
→ See [QUICKSTART.md](QUICKSTART.md) for detailed troubleshooting

---

## What's Next?

### Learn More
- **Architecture**: [README.md](README.md) - How it works
- **Configuration**: [CONFIGURATION.md](CONFIGURATION.md) - All settings explained
- **Full Setup**: [SETUP.md](SETUP.md) - Production deployment

### Customize It
- Change the AI model (Gemini 1.5 Pro for better quality)
- Adjust retrieval settings (more/fewer results)
- Add more embedding models
- Deploy to production

### Explore Features
- Upload multiple papers
- Try semantic search
- View citation sources
- Check conversation history
- Monitor metrics in Grafana

---

## Documentation Map

```
START_HERE.md ← You are here!
    │
    ├─ QUICKSTART.md ─────────── Detailed 5-min guide
    │
    ├─ WHICH_SETUP.md ────────── Minimal vs Full setup
    │
    ├─ CONFIGURATION.md ──────── All settings explained
    │
    ├─ SETUP.md ──────────────── Full production setup
    │
    └─ README.md ─────────────── Architecture & API reference
```

**Recommendation**: You're already running! Explore the UI first, then read the other docs when you need them.

---

## Key Features

### 🔍 Hybrid Retrieval
- Vector search (semantic similarity)
- BM25 search (keyword matching)
- Reciprocal Rank Fusion (combines both)
- Cross-encoder re-ranking (best results)

### 🤖 Smart Generation
- Query expansion (3 variants)
- Context-aware responses
- Citation verification
- Hallucination prevention
- Real-time streaming

### 🔐 Production Ready
- JWT authentication
- Rate limiting
- Input sanitization
- Session management
- Monitoring & metrics

### 📊 Monitoring
- Prometheus metrics
- Grafana dashboards
- OpenTelemetry tracing
- Health checks

---

## System Requirements

**Minimum:**
- Docker Desktop
- 8GB RAM
- 10GB disk space

**Recommended:**
- 16GB RAM (for better performance)
- SSD (faster embeddings)

**Supported OS:**
- Windows 10/11
- macOS 12+
- Linux (Ubuntu 20.04+)

---

## What You're Using

| Component | Technology | Why |
|-----------|------------|-----|
| **LLM** | Gemini 2.5 Flash | Fast, accurate, free tier |
| **Embeddings** | all-MiniLM-L6-v2 | Fast, good quality, 384d |
| **Vector DB** | ChromaDB | Easy setup, good performance |
| **Keyword Search** | BM25 (rank_bm25) | Classic IR algorithm |
| **Re-ranker** | ms-marco cross-encoder | State-of-the-art |
| **Backend** | FastAPI | Fast, async, type-safe |
| **Frontend** | Next.js 15 | React, SSR, streaming |
| **Database** | PostgreSQL 16 | Reliable, feature-rich |
| **Cache** | Redis 7 | Fast, in-memory |
| **Tasks** | Celery | Async processing |

---

## Cost Breakdown

**Current Setup (Minimal):**
- Google Gemini API: **Free tier** (60 req/min)
- Docker containers: **Free** (local)
- Storage: **Free** (local disk)
- **Total: $0/month** ✅

**Scaling to Production:**
- Keep using free Gemini tier
- Add AWS/GCP hosting: ~$40-50/month
- Or self-host on your server: Still $0

---

## Security Note

The minimal setup uses development passwords:
- `POSTGRES_PASSWORD=devpass123`
- `REDIS_PASSWORD=devpass123`

**This is fine for local development!**

⚠️ **For production**: Use strong passwords. See [SETUP.md](SETUP.md)

---

## Upgrading to Production

When you're ready to deploy:

1. Read [WHICH_SETUP.md](WHICH_SETUP.md) - Choose your setup
2. Read [SETUP.md](SETUP.md) - Production guide
3. Use `.env.example` - Full configuration
4. Deploy with Kubernetes - See `deployment/kubernetes/`

You can migrate your data from minimal to full setup!

---

## Contributing

Want to improve the system?

- Add new embedding models
- Improve chunking strategies
- Add new LLM providers
- Enhance the UI
- Write more tests
- Improve documentation

---

## License

MIT - Use it however you want!

---

## Questions?

- **Quick issues**: See [QUICKSTART.md](QUICKSTART.md) troubleshooting
- **Configuration**: See [CONFIGURATION.md](CONFIGURATION.md)
- **Architecture**: See [README.md](README.md)
- **Production**: See [SETUP.md](SETUP.md)

---

**🎉 You're all set! Go to http://localhost:3000 and start researching!**
