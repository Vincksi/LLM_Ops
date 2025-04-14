import logging
import os
import time
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .config import settings
from .api.errors import register_exception_handlers
from .api.middleware import register_middleware
from .api.routers import chat, embeddings, models

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("llm_gateway")

# Create the FastAPI application
app = FastAPI(
    title="LLM Gateway",
    description="A unified API gateway for LLM providers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_exception_handlers(app)

# Register middleware
register_middleware(app)

# Include routers
app.include_router(chat.router)
app.include_router(embeddings.router)
app.include_router(models.router)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": app.version,
        "timestamp": int(time.time())
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LLM Gateway",
        "version": app.version,
        "description": "A unified API gateway for LLM providers",
        "docs_url": "/docs",
        "health_check": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "llm_gateway.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 