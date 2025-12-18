"""
Mindrian API - Main FastAPI Application

This is the backend API that serves the Mindrian platform.
It connects to Neo4j (knowledge graph), Pinecone (vectors), and runs Agno agents.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import routers
from api.routes.chat import router as chat_router
from api.routes.opportunities import router as opportunities_router
from api.routes.health import router as health_router
from api.routes.ai import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("Mindrian API starting up...")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    yield
    # Shutdown
    print("Mindrian API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Mindrian API",
    description="AI-Powered Innovation Platform - Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration - Allow frontend origins
origins = [
    "http://localhost:3000",  # Local Next.js dev
    "http://localhost:8000",  # Local FastAPI
    "https://*.vercel.app",   # Vercel deployments
]

# Add specific Vercel domain if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(opportunities_router, prefix="/api/v1", tags=["Opportunities"])
app.include_router(ai_router, prefix="/api/v1", tags=["AI"])


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Mindrian API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/v1/chat",
            "opportunities": "/api/v1/opportunities",
            "ai": "/api/v1/ai",
            "health": "/health",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") != "production",
    )
