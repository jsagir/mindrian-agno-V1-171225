"""
Mindrian Agent Builder

Meta-agent factory that transforms SKILL.md definitions into production-ready agents.
"""

from .agent_builder import AgentBuilder
from .schema import AgentSpec, HandoffConfig, ToolConfig, Neo4jConfig
from .phases import (
    SkillAnalysisPhase,
    ArchitecturePhase,
    HandoffProtocolPhase,
    ToolAssemblyPhase,
    Neo4jSchemaPhase,
    CodeGenerationPhase,
    RegistrationPhase,
)

__all__ = [
    "AgentBuilder",
    "AgentSpec",
    "HandoffConfig",
    "ToolConfig",
    "Neo4jConfig",
    "SkillAnalysisPhase",
    "ArchitecturePhase",
    "HandoffProtocolPhase",
    "ToolAssemblyPhase",
    "Neo4jSchemaPhase",
    "CodeGenerationPhase",
    "RegistrationPhase",
]
