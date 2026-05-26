"""
Central configuration management using pydantic-settings.
All settings are loaded from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_secret_key: str = "change-me"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://rag_user:password@localhost:5432/rag_research"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "rag_research"
    postgres_user: str = "rag_user"
    postgres_password: str = "password"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 50

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "research_papers"

    # JWT
    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # File Storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    storage_backend: str = "local"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_region: str = "us-east-1"

    # Rate Limiting
    rate_limit_per_minute: int = 20

    # Retrieval
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.75
    max_context_tokens: int = 6000
    reserved_response_tokens: int = 1000
    conversation_history_turns: int = 10
    session_ttl_seconds: int = 86400

    # Monitoring
    prometheus_port: int = 9090
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "rag-research-assistant"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
