"""
Mindrian Registry - Unified Agent and Skill Management

This module provides a plugin-based system for registering and discovering:
- Agents (conversational roles, framework operators)
- Skills (SKILL.md definitions)
- MCP Tools (external capabilities)
- Teams (agent compositions)
"""

from .agent_registry import AgentRegistry, agent_registry
from .skill_loader import SkillLoader, SkillDefinition
from .mcp_manager import MCPManager, mcp_manager

__all__ = [
    "AgentRegistry",
    "agent_registry",
    "SkillLoader",
    "SkillDefinition",
    "MCPManager",
    "mcp_manager",
]
