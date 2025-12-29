"""
API Routes

v1 = Legacy routes (chat with endless questions) - requires agno
v2 = Action-oriented routes (5-question limit, role switching, PWS grounding) - standalone
"""

# v4 and health routes always available
from .chat_v4 import router as chat_v4_router
from .health import router as health_router

# Legacy routes may not be available if agno isn't installed
try:
    from .chat import router as chat_router
    from .opportunities import router as opportunities_router
    from .ai import router as ai_router
    LEGACY_AVAILABLE = True
except ImportError:
    chat_router = None
    opportunities_router = None
    ai_router = None
    LEGACY_AVAILABLE = False

__all__ = [
    "chat_router",
    "chat_v4_router",
    "health_router",
    "opportunities_router",
    "ai_router",
    "LEGACY_AVAILABLE",
]
