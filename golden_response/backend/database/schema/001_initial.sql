-- ============================================================
-- Initial PostgreSQL schema for RAG Research Assistant
-- Run via Alembic or directly for initial setup
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for text search

-- ─── ENUM TYPES ──────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('researcher', 'admin');
CREATE TYPE document_status AS ENUM ('pending', 'processing', 'indexed', 'failed');

-- ─── USERS ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            user_role NOT NULL DEFAULT 'researcher',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);

-- ─── DOCUMENTS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title             VARCHAR(500) NOT NULL,
    authors           JSONB NOT NULL DEFAULT '[]',
    publication_year  INTEGER,
    abstract          TEXT,
    file_path         VARCHAR(1000) NOT NULL,
    file_hash         VARCHAR(64) UNIQUE NOT NULL,
    file_size_bytes   INTEGER,
    page_count        INTEGER,
    status            document_status NOT NULL DEFAULT 'pending',
    error_message     TEXT,
    retry_count       INTEGER NOT NULL DEFAULT 0,
    chroma_collection VARCHAR(255),
    doc_metadata      JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_hash  ON documents(file_hash);
CREATE INDEX idx_documents_status ON documents(status);

-- ─── DOCUMENT CHUNKS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_chunks (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index   INTEGER NOT NULL,
    content       TEXT NOT NULL,
    page_number   INTEGER,
    token_count   INTEGER,
    chroma_id     VARCHAR(255) UNIQUE,
    chunk_metadata JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_chroma   ON document_chunks(chroma_id);

-- ─── SESSIONS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at    TIMESTAMP
);
CREATE INDEX idx_sessions_token  ON sessions(session_token);
CREATE INDEX idx_sessions_user   ON sessions(user_id);

-- ─── CONVERSATION HISTORY ────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversation_history (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id       UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role             VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT NOT NULL,
    citations        JSONB NOT NULL DEFAULT '[]',
    confidence_score FLOAT,
    token_count      INTEGER,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_conv_session ON conversation_history(session_id);
CREATE INDEX idx_conv_created ON conversation_history(created_at);

-- ─── REFRESH TOKENS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX idx_refresh_token_hash ON refresh_tokens(token_hash);
