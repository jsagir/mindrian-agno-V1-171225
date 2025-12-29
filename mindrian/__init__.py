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

__version__ = "1.0.0"

# Lazy imports - only import agno-dependent modules when actually needed
# This allows the prompts and tools subpackages to be used without agno

def __getattr__(name):
    """Lazy import for agno-dependent modules."""
    if name == "MindrianOrchestrator":
        from .workflow.orchestrator import MindrianOrchestrator
        return MindrianOrchestrator
    elif name == "ProblemRouter":
        from .workflow.router import ProblemRouter
        return ProblemRouter
    elif name == "ProblemType":
        from .workflow.router import ProblemType
        return ProblemType
    elif name == "LarryAgent":
        from .agents.conversational.larry import LarryAgent
        return LarryAgent
    elif name == "LarryMode":
        from .agents.conversational.larry import LarryMode
        return LarryMode
    elif name == "DevilsAdvocateAgent":
        from .agents.conversational.devil import DevilsAdvocateAgent
        return DevilsAdvocateAgent
    elif name in ["MindrianAgent", "FrameworkAgent", "ConversationalAgent"]:
        from .agents import base
        return getattr(base, name)
    elif name in ["AgentRegistry", "agent_registry"]:
        from .registry.agent_registry import AgentRegistry, agent_registry
        return AgentRegistry if name == "AgentRegistry" else agent_registry
    elif name in ["SkillLoader", "SkillDefinition"]:
        from .registry.skill_loader import SkillLoader, SkillDefinition
        return SkillLoader if name == "SkillLoader" else SkillDefinition
    elif name in ["MCPManager", "mcp_manager"]:
        from .registry.mcp_manager import MCPManager, mcp_manager
        return MCPManager if name == "MCPManager" else mcp_manager
    raise AttributeError(f"module 'mindrian' has no attribute '{name}'")

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
