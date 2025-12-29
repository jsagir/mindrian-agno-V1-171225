"""
Chat Routes

Handles conversation with Mindrian agents (Larry, frameworks, etc.)

This uses the high-grade Larry implementation with:
- Neo4j-validated system prompt
- PWS methodology integration
- Problem classification (Un-defined, Ill-defined, Well-defined)
- Tool triggering based on clarity thresholds
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from mindrian.agents.conversational.larry import (
    create_larry_agent,
    get_tool_trigger_conditions,
    should_trigger_tool,
)
from mindrian.teams.deep_research_team import DeepResearchTeam
from mindrian.tools.pws_brain_pinecone import PWSBrainPinecone

router = APIRouter()


# In-memory session storage (replace with Redis/DB in production)
sessions: Dict[str, Dict[str, Any]] = {}

# PWS Brain instance for knowledge retrieval (Pinecone-based, no Neo4j needed)
pws_brain = PWSBrainPinecone()


class ChatMessage(BaseModel):
    """A chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    session_id: str
    response: str
    thinking: Optional[str] = None
    framework_output: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = None


class SessionCreate(BaseModel):
    """Request to create a new session."""
    user_id: Optional[str] = None
    initial_context: Optional[str] = None


class SessionResponse(BaseModel):
    """Response with session info."""
    session_id: str
    created_at: str
    message_count: int


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate = None):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "messages": [],
        "clarity": {"what": 0.0, "who": 0.0, "success": 0.0},
        "context": request.initial_context if request else None,
    }
    return SessionResponse(
        session_id=session_id,
        created_at=sessions[session_id]["created_at"],
        message_count=0,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session info."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return SessionResponse(
        session_id=session_id,
        created_at=session["created_at"],
        message_count=len(session["messages"]),
    )


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str) -> List[ChatMessage]:
    """Get all messages in a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id]["messages"]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response from Larry.

    This is the main chat endpoint. Larry will clarify the problem,
    and when appropriate, trigger framework analysis.
    """
    # Get or create session
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "clarity": {"what": 0.0, "who": 0.0, "success": 0.0},
        }

    session = sessions[session_id]

    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow().isoformat(),
    )
    session["messages"].append(user_message)

    # Build conversation history for Larry
    history = "\n".join([
        f"{m.role}: {m.content}"
        for m in session["messages"][-10:]  # Last 10 messages
    ])

    try:
        # Create Larry agent with PWS brain enabled
        larry = create_larry_agent(pws_brain_enabled=True)

        # Retrieve relevant PWS context for the user's message (Pinecone RAG)
        pws_context = ""
        try:
            pws_context = await pws_brain.get_pws_context(request.message, top_k=3)
        except Exception as e:
            print(f"PWS brain retrieval error: {e}")

        # Build the prompt with knowledge context
        prompt = f"Conversation so far:\n{history}\n\nUser's latest message: {request.message}"
        if pws_context:
            prompt = f"{prompt}\n\n{pws_context}"

        # Run Larry with the conversation + knowledge context
        response = larry.run(prompt)

        # Extract response content
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Add assistant message
        assistant_message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow().isoformat(),
        )
        session["messages"].append(assistant_message)

        # Determine suggested actions based on clarity and tool triggering logic
        suggested_actions = []
        clarity = session["clarity"]
        overall = (clarity["what"] + clarity["who"] + clarity["success"]) / 3
        problem_type = session.get("problem_type", None)

        # Use tool triggering logic to suggest actions
        if should_trigger_tool(
            "pws_validation", overall, problem_type,
            has_what=clarity["what"] > 0.5,
            has_who=clarity["who"] > 0.5,
            has_success=clarity["success"] > 0.5,
        ):
            suggested_actions.append("Run PWS Validation (GO/PIVOT/NO-GO)")

        if should_trigger_tool("jobs_to_be_done", overall, problem_type):
            suggested_actions.append("Map Jobs to Be Done")

        if should_trigger_tool("minto_pyramid", overall, problem_type):
            suggested_actions.append("Structure with Minto Pyramid (SCQA)")

        if should_trigger_tool("devil_advocate", overall, problem_type):
            suggested_actions.append("Stress-test with Devil's Advocate")

        if should_trigger_tool("beautiful_question", overall, problem_type):
            suggested_actions.append("Explore with Beautiful Questions")

        if should_trigger_tool("trending_to_absurd", overall, problem_type):
            suggested_actions.append("Extrapolate with Trending to Absurd")

        if should_trigger_tool("scenario_analysis", overall, problem_type):
            suggested_actions.append("Run Scenario Analysis")

        # Add team suggestions for high clarity
        if should_trigger_tool("validation_team", overall, problem_type,
            has_what=clarity["what"] > 0.5,
            has_who=clarity["who"] > 0.5,
            has_success=clarity["success"] > 0.5,
        ):
            suggested_actions.insert(0, "Run Full Validation Team (PWS → Devil → JTBD)")

        return ChatResponse(
            session_id=session_id,
            response=response_text,
            suggested_actions=suggested_actions if suggested_actions else None,
        )

    except Exception as e:
        # Return error but don't crash
        error_msg = f"I encountered an issue processing your message. Error: {str(e)}"
        return ChatResponse(
            session_id=session_id,
            response=error_msg,
        )


@router.post("/chat/{session_id}/deep-research")
async def trigger_deep_research(session_id: str):
    """
    Trigger the Deep Research Team workflow.

    This runs the multi-agent research process:
    1. Beautiful Question Agent
    2. Domain Analysis Agent
    3. CSIO Agent
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    # Get problem context from session
    messages = session.get("messages", [])
    if not messages:
        raise HTTPException(
            status_code=400,
            detail="No messages in session. Start a conversation first."
        )

    # Build context from conversation
    context = "\n".join([
        f"{m.role}: {m.content}"
        for m in messages
    ])

    try:
        # Create and run Deep Research Team
        team = DeepResearchTeam()
        result = team.run(f"Based on this conversation, research innovation opportunities:\n\n{context}")

        return {
            "session_id": session_id,
            "status": "completed",
            "result": result.content if hasattr(result, 'content') else str(result),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Deep research failed: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"status": "deleted", "session_id": session_id}
