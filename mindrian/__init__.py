"""
Mindrian - AI-Powered Innovation Platform

Built on Agno framework with multi-MCP orchestration.

## Quick Start (Playground)

    cd mindrian-agno
    pip install -e .
    fastapi dev playground.py

    # Then open http://localhost:8000/docs
    # Or connect Agent UI: npx create-agent-ui@latest

## Programmatic Usage

    from mindrian import MindrianOrchestrator

    orchestrator = MindrianOrchestrator()
    await orchestrator.initialize()

    response = await orchestrator.process("I want to improve customer retention")
"""

from .workflow.orchestrator import MindrianOrchestrator
from .workflow.router import ProblemRouter, ProblemType
from .agents.conversational.larry import LarryAgent, LarryMode
from .agents.conversational.devil import DevilsAdvocateAgent
from .agents.base import MindrianAgent, FrameworkAgent, ConversationalAgent
from .registry.agent_registry import AgentRegistry, agent_registry
from .registry.skill_loader import SkillLoader, SkillDefinition
from .registry.mcp_manager import MCPManager, mcp_manager

__version__ = "1.0.0"
__all__ = [
    # Main entry point
    "MindrianOrchestrator",

    # Routing
    "ProblemRouter",
    "ProblemType",

    # Agents
    "LarryAgent",
    "LarryMode",
    "DevilsAdvocateAgent",
    "MindrianAgent",
    "FrameworkAgent",
    "ConversationalAgent",

    # Registry
    "AgentRegistry",
    "agent_registry",
    "SkillLoader",
    "SkillDefinition",
    "MCPManager",
    "mcp_manager",
]
