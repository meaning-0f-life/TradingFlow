from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ServiceEnum(str, Enum):
    openai = "openai"
    binance = "binance"
    anthropic = "anthropic"
    alpha_vantage = "alpha_vantage"
    yahoo_finance = "yahoo_finance"
    bybit = "bybit"
    mt5 = "mt5"
    qdrant = "qdrant"
    redis = "redis"
    open_router = "open_router"
    deepseek = "deepseek"
    telegram = "telegram"


class APIKey(Base):
    """API Key model for storing encrypted external service keys"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)  # User-friendly name (e.g., "OpenAI API Key")
    service = Column(SQLEnum(ServiceEnum), nullable=False)
    encrypted_key = Column(Text, nullable=False)  # Encrypted API key
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="api_keys")