from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "TradingFlow"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    APP_URL: str = "http://localhost:3000"  # For OpenRouter headers

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://tradingflow:tradingflow@localhost:5432/tradingflow"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Qdrant (Vector DB)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "tradingflow_docs"

    # Encryption
    ENCRYPTION_KEY: str = "your-encryption-key-change-in-production"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()