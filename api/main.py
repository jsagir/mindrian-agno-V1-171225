"""
Mindrian API - Main FastAPI Application

This is the backend API that serves the Mindrian platform.
It connects to Neo4j (knowledge graph), Pinecone (vectors), and runs Agno agents.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import routers from routes package (handles legacy import errors)
from api.routes import (
    chat_v4_router,
    health_router,
    chat_router,
    opportunities_router,
    ai_router,
    LEGACY_AVAILABLE as LEGACY_ROUTES_AVAILABLE,
)

if not LEGACY_ROUTES_AVAILABLE:
    print("Warning: Legacy routes not available (agno not installed). Running with v4 routes only.")


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
app.include_router(chat_v4_router, prefix="/api/v2", tags=["Chat v4 (Action-Oriented)"])  # New!

# Include legacy routers if available
if LEGACY_ROUTES_AVAILABLE:
    app.include_router(chat_router, prefix="/api/v1", tags=["Chat (Legacy)"])
    app.include_router(opportunities_router, prefix="/api/v1", tags=["Opportunities"])
    app.include_router(ai_router, prefix="/api/v1", tags=["AI"])


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Mindrian API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            # v2 - Action-oriented with role switching (RECOMMENDED)
            "chat": "/api/v2/chat",
            "switch_role": "/api/v2/chat/{session_id}/switch-role",
            "roles": "/api/v2/roles",
            "sessions": "/api/v2/sessions/{session_id}",
            "opportunities": "/api/v2/opportunities",
            "create_opportunity": "/api/v2/opportunities/create-from-session",
            "deep_dive": "/api/v2/opportunities/{id}/deep-dive",
            # System
            "health": "/health",
            # Legacy (v1) - may not be available without agno
            "chat_legacy": "/api/v1/chat",
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
