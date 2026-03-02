from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, workflows, nodes, execution, keys
from app.core.websocket import websocket_endpoint

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    print("Starting TradingFlow backend...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")
    yield
    # Shutdown
    print("Shutting down TradingFlow backend...")

app = FastAPI(
    title="TradingFlow API",
    description="Orchestration platform for financial market analysis and trading",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])
app.include_router(keys.router, prefix="/api/keys", tags=["api-keys"])

# WebSocket endpoint
app.websocket_route("/ws")(websocket_endpoint)

@app.get("/")
async def root():
    return {"message": "TradingFlow API", "version": "0.1.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )