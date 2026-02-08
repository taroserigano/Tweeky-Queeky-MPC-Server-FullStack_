from pydantic_settings import BaseSettings
from typing import Optional, Literal


class Settings(BaseSettings):
    # ──────────────────────────────────────────────────────────────────────────
    # CORE SETTINGS
    # ──────────────────────────────────────────────────────────────────────────
    PORT: int = 5001
    MONGO_URI: str = "mongodb://localhost:27017/tweekyqueeky"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30
    NODE_ENV: str = "development"
    PAGINATION_LIMIT: int = 12

    # ──────────────────────────────────────────────────────────────────────────
    # PAYPAL
    # ──────────────────────────────────────────────────────────────────────────
    PAYPAL_CLIENT_ID: str
    PAYPAL_APP_SECRET: str
    PAYPAL_API_URL: str = "https://api-m.sandbox.paypal.com"

    # ──────────────────────────────────────────────────────────────────────────
    # STRIPE
    # ──────────────────────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None

    # ──────────────────────────────────────────────────────────────────────────
    # LLM PROVIDERS
    # ──────────────────────────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["openai", "anthropic", "ollama"] = "openai"
    
    # OpenAI
    OPEN_AI: Optional[str] = None  # Legacy key name
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    
    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"
    
    # Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # ──────────────────────────────────────────────────────────────────────────
    # EMBEDDING SETTINGS
    # ──────────────────────────────────────────────────────────────────────────
    EMBEDDING_PROVIDER: Literal["openai", "sentence_transformers", "ollama"] = "openai"
    SENTENCE_TRANSFORMERS_MODEL: str = "intfloat/e5-large-v2"
    
    # Embedding dimensions (must match Pinecone index)
    # OpenAI text-embedding-3-large: 3072
    # OpenAI text-embedding-3-small: 1536
    # Sentence Transformers e5-large-v2: 1024
    EMBEDDING_DIMENSION: int = 3072

    # ──────────────────────────────────────────────────────────────────────────
    # PINECONE VECTOR DB
    # ──────────────────────────────────────────────────────────────────────────
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX: str = "tweeky-products"
    PINECONE_NAMESPACE: str = "products"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    # ──────────────────────────────────────────────────────────────────────────
    # RAG SETTINGS
    # ──────────────────────────────────────────────────────────────────────────
    RAG_TOP_K: int = 10  # Number of results to retrieve
    RAG_SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score
    RAG_RERANK_ENABLED: bool = True  # Enable reranking

    @property
    def openai_key(self) -> Optional[str]:
        """Get OpenAI API key (handles legacy key name)"""
        return self.OPENAI_API_KEY or self.OPEN_AI

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
