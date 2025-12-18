"""
Health Check Routes

Provides endpoints for checking API and service health.
"""

import os
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health():
    """
    Detailed health check - verifies connections to external services.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check Neo4j
    neo4j_uri = os.getenv("NEO4J_URI")
    health_status["services"]["neo4j"] = {
        "configured": bool(neo4j_uri),
        "status": "configured" if neo4j_uri else "not_configured"
    }

    # Check Pinecone
    pinecone_key = os.getenv("PINECONE_API_KEY")
    health_status["services"]["pinecone"] = {
        "configured": bool(pinecone_key),
        "status": "configured" if pinecone_key else "not_configured"
    }

    # Check Supabase (PWS Brain)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    health_status["services"]["supabase_pws"] = {
        "configured": bool(supabase_url and supabase_key),
        "status": "configured" if (supabase_url and supabase_key) else "not_configured"
    }

    # Check Google API (for embeddings)
    google_key = os.getenv("GOOGLE_API_KEY")
    health_status["services"]["google_embeddings"] = {
        "configured": bool(google_key),
        "status": "configured" if google_key else "not_configured"
    }

    # Check Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    health_status["services"]["anthropic"] = {
        "configured": bool(anthropic_key),
        "status": "configured" if anthropic_key else "not_configured"
    }

    # Overall status
    all_configured = all(
        s["configured"] for s in health_status["services"].values()
    )
    health_status["status"] = "healthy" if all_configured else "degraded"

    return health_status
