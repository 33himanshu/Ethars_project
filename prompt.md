## **RAG-Based AI Research Assistant** 

Complete System Prompt — Production Grade 

## **Context and Role** 

As an AI/ML Engineer specializing in Large Language Models and Retrieval-Augmented Generation (RAG) systems, you are responsible for designing and implementing a production-grade AI research assistant for academic papers. The system must provide accurate, citation-aware responses using advanced retrieval pipelines while minimizing hallucinations and ensuring scalability, security, and observability. 

The assistant should help researchers, students, and professionals interact with large collections of academic documents through semantic search, conversational querying, and context-aware retrieval. 

## **Objective** 

Design and implement a complete, production-ready RAG-based AI research assistant that: 

- Ingests and processes academic papers (PDFs and text documents) 

- Supports semantic and hybrid retrieval 

- Provides citation-aware answers with source attribution 

- Maintains conversational memory across sessions 

- Minimizes hallucinations using grounded retrieval 

- Streams responses in real time using SSE or WebSocket 

- Supports scalable deployment for high-traffic usage 

- Includes monitoring, observability, and evaluation pipelines 

## **Critical Output Requirement** 

**Generate complete, working, production-ready code organized into modular files. Each file must serve a single responsibility. Provide every file needed to run the system end to end. Do not provide architecture descriptions alone — actual implementable code is required for every component described.** 

Structure all code output as follows: 

```
project-root/
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── utils/
```

```
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

## **Test Case and Sample Data** 

Use the following as a concrete test scenario throughout all implementation examples: 

- Sample document: "Attention Is All You Need" (Vaswani et al., 2017) 

- Sample user query: "What attention mechanism is proposed in this paper and how does it differ from RNNs?" 

- Expected behavior: System retrieves relevant chunks from the paper, injects them into LLM context, generates a citation-aware answer referencing specific sections, and streams the response token by token to the frontend 

All code examples, API response samples, and pipeline demonstrations must reference this test case. 

## **Core System Requirements** 

## **1. Document Ingestion Pipeline** 

The system must support: 

- PDF upload and parsing using PyMuPDF or pdfplumber 

- Metadata extraction per document: title, authors, publication year, citations, abstract 

- OCR fallback for scanned PDFs using Tesseract 

- Text cleaning and normalization 

- Automatic document chunking: Chunk size 512 tokens, Chunk overlap 50 tokens, Sentence-aware splitting 

- Incremental indexing for newly uploaded documents 

- Duplicate detection using document hash (SHA-256) 

- Asynchronous processing using Celery or FastAPI background tasks 

- Graceful failure logging with retry mechanism (max 3 retries) 

Provide working code for: PDF parser module, Metadata extractor, Chunking module, Async ingestion task handler, Duplicate detection utility. 

## **2. Embedding Strategy** 

Use the following embedding configuration and justify each choice in code comments: 

- Embedding model: sentence-transformers/all-MiniLM-L6-v2 

   - Justification: Strong balance between accuracy, latency, and cost for academic text 

   - Dimensionality: 384 

- Alternative for higher accuracy: text-embedding-ada-002 (OpenAI) 

   - Justification: Higher accuracy, higher cost, suitable for production with budget 

- Chunk size: 512 tokens | Overlap: 50 tokens 

Provide working code for: Embedding generation module, Batch embedding processor, Embedding cache layer using Redis. 

## **3. Retrieval Pipeline** 

Implement a hybrid retrieval architecture: 

- Semantic vector search using ChromaDB (primary vector database) 

   - Justification: Open-source, easy local and cloud deployment, strong Python integration 

- BM25 keyword retrieval using rank_bm25 library 

- Hybrid fusion using Reciprocal Rank Fusion (RRF) to merge semantic and keyword results 

- Re-ranking using cross-encoder/ms-marco-MiniLM-L-6-v2 

- Top-k retrieval: Return top 5 chunks after re-ranking 

- Metadata filtering: Filter by author, year, or document title before retrieval 

- Query expansion: Generate 3 alternative phrasings of user query before retrieval 

- Multi-query retrieval: Run all query variants, deduplicate results, merge before reranking 

Provide working code for: Vector search module, BM25 retrieval module, Hybrid RRF fusion module, Re-ranking module, Query expansion module, Full retrieval orchestrator. 

## **4. LLM and Generation** 

The assistant must: 

- Use gpt-4o as primary LLM via OpenAI API 

- Generate citation-aware responses referencing specific retrieved chunks 

- Display source attribution with document title, authors, and page number 

- Support conversational follow-up questions 

- Maintain last 10 conversation turns per session stored in Redis with 24-hour TTL 

- Stream responses progressively using Server-Sent Events (SSE) 

- Prevent hallucinated citations by only referencing chunks present in retrieved context 

## **Prompt Engineering Strategy** 

```
System: You are an academic research assistant. Answer ONLY using
the provided context chunks. For every claim you make, cite the
source chunk using [Author, Year, Chunk ID] format. If the context
does not contain enough information to answer, respond with:
"I cannot find sufficient evidence in the provided documents."
```

```
Context: {retrieved_chunks}
Conversation History: {last_10_turns}
User Query: {current_query}
```

## **Context Window Management** 

- Max context tokens: 6000 

- Reserve 1000 tokens for response generation 

- If retrieved chunks exceed limit, truncate lowest-ranked chunks first 

Provide working code for: LLM generation module, Citation formatter, Streaming SSE handler, Context window manager, Conversation memory manager. 

## **5. Hallucination Mitigation and Safety** 

- Retrieval grounding validation: Only generate answers when at least 1 chunk has similarity score above 0.75 

- Confidence scoring: Attach confidence score to each response based on average retrieval similarity 

- Citation verification: Verify every cited chunk ID exists in the retrieved context 

- Refusal behavior: If no chunk meets the 0.75 threshold, return structured refusal message 

- Prompt injection prevention: Strip special characters and instruction-like patterns from user input 

- Retrieved content sanitization: Remove executable code or script tags from chunks before injecting into prompt 

- Answer relevance checking: Use lightweight cross-encoder to score answer relevance post-generation 

Provide working code for: Confidence scorer, Citation verifier, Input sanitizer, Refusal handler. 

## **6. Frontend Requirements** 

Technology: Next.js (App Router), Tailwind CSS, Framer Motion 

Frontend must include: 

- Conversational research interface with streaming token rendering 

- Document upload UI with drag-and-drop and upload progress indicator 

- Citation panel showing source chunks alongside the response 

- Search history sidebar 

- Typing indicator during retrieval phase 

- Responsive design (mobile, tablet, desktop) 

- Accessibility support (ARIA labels, semantic HTML, keyboard navigation) 

- Animated transitions between states using Framer Motion 

Provide working code for: Chat interface component, Streaming response renderer, Document upload component, Citation panel component, Search history component, Framer Motion animation config. 

## **7. Backend Requirements** 

Technology: Python FastAPI with async support, REST API, Celery for background tasks, Redis for caching and session memory 

Backend responsibilities: 

- Retrieval orchestration 

- Embedding generation 

- Document indexing 

- JWT authentication 

- Session management 

- Streaming API responses via SSE 

- Rate limiting: max 20 requests per minute per user 

Provide working code for: All API route handlers, Authentication middleware, Rate limiting middleware, Session manager, Background task handler. 

## **8. Database and Storage** 

|**Layer**|**Technology**|**Justification**|
|---|---|---|
|Vector DB|ChromaDB|Open-source, simple deployment, strong<br>Python SDK|
|Relational DB|PostgreSQL|Structured metadata, user data, session<br>storage|
|Cache|Redis|Low-latency session memory and embedding<br>cache|



File Storage Local / S3 

Raw PDF storage before processing 

Provide: PostgreSQL schema for users, documents, sessions, and conversation history. ChromaDB collection setup. Redis key structure for sessions and cache. 

## **9. API Design** 

Design and implement the following endpoints: 

```
POST   /api/documents/upload        → Upload and ingest document
GET    /api/documents               → List all indexed documents
DELETE /api/documents/{id}          → Remove document from index
POST   /api/chat                    → Submit query, returns SSE stream
GET    /api/chat/history/{session}  → Retrieve conversation history
DELETE /api/chat/history/{session}  → Clear session history
GET    /api/search                  → Semantic search without chat
context
GET    /api/citations/{chunk_id}    → Retrieve specific source chunk
POST   /api/auth/register           → User registration
POST   /api/auth/login              → JWT token generation
POST   /api/auth/refresh            → Token refresh
```

All responses must follow this structure: 

```
{
  "status": "success" | "error",
  "data": {},
  "message": "string",
  "timestamp": "ISO8601",
  "request_id": "uuid"
}
```

## **10. Authentication and Security** 

Implement: 

- JWT authentication with refresh token rotation 

- Rate limiting: 20 requests per minute per user 

- Secure file upload validation (PDF only, max 50MB) 

- Environment variable management via .env with .env.example provided 

- RBAC with two roles: researcher (upload + query) and admin (full access) 

Protect against: Prompt injection, XSS, Malicious PDF uploads, Vector database poisoning, Unauthorized API access via JWT middleware. 

## **11. Monitoring and Observability** 

Implement production observability using Prometheus, Grafana, and OpenTelemetry. 

Track the following metrics: 

|**Metric**|**Target Threshold**|
|---|---|
|p95 retrieval latency|< 500ms|
|p95 end-to-end response latency|< 2000ms|
|Hallucination rate|< 5%|
|Retrieval precision@5|> 0.80|
|Token usage per query|Log and alert if > 4000|
|Failed ingestion rate|Alert if > 1%|



Provide working code for: Prometheus metrics setup, OpenTelemetry trace instrumentation, Latency tracking middleware, Token usage logger. 

## **12. Evaluation Framework** 

Design evaluation pipelines measuring: 

- Retrieval accuracy: Precision@5 against a labeled test set 

- Hallucination rate: Percentage of responses containing ungrounded claims 

- Answer relevance: Cosine similarity between query and response embedding 

- Citation correctness: Exact match of cited chunk ID against retrieved context 

- Latency: p95 response time across 100 test queries 

- Token efficiency: Average tokens used per query 

Include: Offline evaluation dataset with 20 labeled query-answer pairs based on 'Attention Is All You Need'. Automated benchmarking script. Human evaluation scoring rubric. 

Provide working code for: Evaluation runner script, Metrics calculator, Benchmark dataset loader, Results reporter. 

## **13. Deployment** 

Provide deployment architecture using: 

- Docker with separate containers for frontend, backend, ChromaDB, PostgreSQL, Redis, Celery worker 

- Docker Compose for local development 

- Kubernetes manifests for production deployment 

- CI/CD pipeline using GitHub Actions 

- Environment variable management with .env.example 

Include: Staging and production environment separation. Rollback mechanism via versioned Docker images. Horizontal pod autoscaling configuration. GPU inference optimization notes for embedding generation. 

Provide: Complete docker-compose.yml, Kubernetes deployment manifests, GitHub Actions CI/CD workflow file, .env.example with all required variables. 

## **14. Documentation** 

Provide: 

- Complete folder structure with file descriptions 

- Step-by-step setup instructions (local and production) 

- Environment variable configuration guide 

- API documentation with request/response examples 

- Architecture diagram described textually with data flow 

- Troubleshooting section covering top 10 common issues 

## **Final Output Checklist** 

Your response must include ALL of the following — do not skip any item: 

- Complete modular folder structure 

- PDF ingestion pipeline code 

- Chunking and embedding module code 

- Hybrid retrieval pipeline code (semantic + BM25 + RRF) 

- Re-ranking module code 

- Query expansion module code 

- LLM generation module with citation formatting 

- SSE streaming handler code 

- Conversation memory manager code 

- Hallucination mitigation module code 

- Next.js frontend with all components 

- FastAPI backend with all route handlers 

- PostgreSQL schema 

- ChromaDB setup code 

- Redis session and cache setup 

- JWT authentication middleware 

- Rate limiting middleware 

- Prometheus and OpenTelemetry instrumentation code 

- Evaluation runner script 

- docker-compose.yml 

- Kubernetes manifests 

- GitHub Actions CI/CD workflow 

- .env.example 

- Complete README with setup and deployment guide 

