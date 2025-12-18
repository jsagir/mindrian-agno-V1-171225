"""
Agent Registry - Unified agent management and factory

Provides:
1. Agent registration and discovery
2. Dynamic agent creation from SKILL.md files
3. Multi-MCP tool injection
4. Team composition utilities
"""

from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
import importlib
from pathlib import Path

from agno.agent import Agent
from agno.models.anthropic import Claude

from .skill_loader import SkillLoader, SkillDefinition, SkillType
from .mcp_manager import MCPManager, mcp_manager


class AgentCategory(str, Enum):
    """Categories of agents in Mindrian"""
    FRAMEWORK = "framework"      # Minto, JTBD, PWS, etc.
    CONVERSATIONAL = "conversational"  # Larry, Devil, etc.
    SPECIALIST = "specialist"    # Domain experts
    ORCHESTRATOR = "orchestrator"  # Coordinators
    TOOL = "tool"                # Atomic tool wrappers


@dataclass
class AgentDefinition:
    """Definition for creating an agent"""
    name: str
    category: AgentCategory
    skill: Optional[SkillDefinition] = None
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    mcp_tools: List[str] = field(default_factory=list)
    custom_tools: List[Callable] = field(default_factory=list)
    custom_instructions: Optional[str] = None

    # Agent class override
    agent_class: Optional[Type[Agent]] = None

    # Runtime config
    thinking_enabled: bool = True  # Use Sequential Thinking MCP
    memory_enabled: bool = True


class AgentRegistry:
    """
    Central registry for all Mindrian agents.

    Usage:
        # Register from SKILL.md
        registry.register_from_skill("larry")

        # Register custom agent
        registry.register(AgentDefinition(
            name="custom-agent",
            category=AgentCategory.SPECIALIST,
            custom_instructions="You are a specialist..."
        ))

        # Create agent instance
        agent = registry.create("larry")

        # List available agents
        agents = registry.list_all()
    """

    def __init__(
        self,
        skill_loader: Optional[SkillLoader] = None,
        mcp_manager: Optional[MCPManager] = None,
    ):
        self._definitions: Dict[str, AgentDefinition] = {}
        self._skill_loader = skill_loader
        self._mcp_manager = mcp_manager or mcp_manager
        self._instances: Dict[str, Agent] = {}  # Cache of created agents

    def set_skill_loader(self, loader: SkillLoader) -> None:
        """Set the skill loader for loading SKILL.md files"""
        self._skill_loader = loader

    def register(self, definition: AgentDefinition) -> None:
        """Register an agent definition"""
        self._definitions[definition.name] = definition

    def register_from_skill(self, skill_name: str) -> Optional[AgentDefinition]:
        """
        Register an agent from a SKILL.md file.

        Args:
            skill_name: Name of the skill to load

        Returns:
            AgentDefinition if successful
        """
        if not self._skill_loader:
            raise ValueError("Skill loader not configured")

        skill = self._skill_loader.get(skill_name)
        if not skill:
            return None

        # Map skill type to agent category
        category_map = {
            SkillType.OPERATOR: AgentCategory.FRAMEWORK,
            SkillType.ROLE: AgentCategory.CONVERSATIONAL,
            SkillType.GUIDED: AgentCategory.SPECIALIST,
            SkillType.COLLABORATIVE: AgentCategory.FRAMEWORK,
            SkillType.PIPELINE: AgentCategory.FRAMEWORK,
            SkillType.TOOL: AgentCategory.TOOL,
            SkillType.ORCHESTRATOR: AgentCategory.ORCHESTRATOR,
        }

        definition = AgentDefinition(
            name=skill.name,
            category=category_map.get(skill.type, AgentCategory.SPECIALIST),
            skill=skill,
            mcp_tools=skill.get_required_mcps(),
        )

        self.register(definition)
        return definition

    def register_all_skills(self) -> int:
        """Register all skills from the skill loader"""
        if not self._skill_loader:
            return 0

        skills = self._skill_loader.load_all()
        count = 0
        for skill_name in skills:
            if self.register_from_skill(skill_name):
                count += 1
        return count

    def get(self, name: str) -> Optional[AgentDefinition]:
        """Get an agent definition by name"""
        return self._definitions.get(name)

    def list_all(self) -> List[str]:
        """List all registered agent names"""
        return list(self._definitions.keys())

    def list_by_category(self, category: AgentCategory) -> List[str]:
        """List agents in a specific category"""
        return [
            name for name, defn in self._definitions.items()
            if defn.category == category
        ]

    def create(
        self,
        name: str,
        session_id: Optional[str] = None,
        override_model: Optional[str] = None,
        additional_tools: Optional[List[Callable]] = None,
    ) -> Agent:
        """
        Create an agent instance from a registered definition.

        Args:
            name: Name of the registered agent
            session_id: Optional session ID for state management
            override_model: Override the default model
            additional_tools: Additional tools to inject

        Returns:
            Configured Agno Agent instance
        """
        definition = self._definitions.get(name)
        if not definition:
            raise ValueError(f"Agent '{name}' not registered")

        # Build instructions
        instructions = self._build_instructions(definition)

        # Build tools
        tools = self._build_tools(definition, additional_tools)

        # Create model
        model = Claude(id=override_model or definition.model)

        # Create agent
        agent = Agent(
            name=definition.name,
            model=model,
            instructions=instructions,
            tools=tools,
            markdown=True,
        )

        return agent

    def _build_instructions(self, definition: AgentDefinition) -> str:
        """Build agent instructions from definition"""
        instructions = []

        # Add skill instructions if available
        if definition.skill:
            instructions.append(definition.skill.to_agent_instructions())

        # Add custom instructions
        if definition.custom_instructions:
            instructions.append(definition.custom_instructions)

        # Add Sequential Thinking guidance if enabled
        if definition.thinking_enabled:
            instructions.append(self._get_thinking_instructions())

        return "\n\n---\n\n".join(instructions)

    def _build_tools(
        self,
        definition: AgentDefinition,
        additional_tools: Optional[List[Callable]] = None,
    ) -> List[Callable]:
        """Build tools list for agent"""
        tools = []

        # Add MCP tools
        if self._mcp_manager and definition.mcp_tools:
            mcp_tools = self._mcp_manager.create_tool_functions(definition.mcp_tools)
            tools.extend(mcp_tools.values())

        # Add custom tools from definition
        tools.extend(definition.custom_tools)

        # Add additional tools
        if additional_tools:
            tools.extend(additional_tools)

        return tools

    def _get_thinking_instructions(self) -> str:
        """Get instructions for Sequential Thinking integration"""
        return """
## Reasoning Process (Sequential Thinking)

For complex tasks, follow this structured thinking approach:

1. **Understand**: Clearly state what you understand about the task
2. **Plan**: Break down the task into logical steps
3. **Execute**: Work through each step, using available tools when needed
4. **Reflect**: Review your work and check for completeness
5. **Conclude**: Synthesize findings into a coherent response

When using tools:
- State WHY you're using a specific tool
- Interpret tool results in context
- Connect tool outputs to your overall reasoning
"""

    def create_team(
        self,
        agent_names: List[str],
        mode: str = "coordinate",
    ) -> List[Agent]:
        """
        Create a team of agents.

        Args:
            agent_names: Names of agents to include
            mode: Team mode (coordinate, collaborate, route)

        Returns:
            List of Agent instances configured as a team
        """
        agents = []
        for name in agent_names:
            agent = self.create(name)
            agents.append(agent)
        return agents


# Global registry instance
agent_registry = AgentRegistry()
