"""
Base Agent Classes for Mindrian

Provides:
1. MindrianAgent - Base class with multi-MCP support
2. FrameworkAgent - For thinking frameworks (Minto, JTBD, PWS)
3. ConversationalAgent - For roles (Larry, Devil)
4. Factory function for creating agents from SKILL.md
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools import Toolkit

# Optional Gemini import - only needed if using Google models
try:
    from agno.models.google import Gemini
    GEMINI_AVAILABLE = True
except ImportError:
    Gemini = None
    GEMINI_AVAILABLE = False

from ..registry.skill_loader import SkillDefinition, SkillType
from ..registry.mcp_manager import MCPManager, mcp_manager


class ConversationMode(str, Enum):
    """Conversation modes for Larry and other conversational agents"""
    CLARIFY = "clarify"        # Default: Ask questions to understand
    EXPLORE = "explore"        # Open-ended exploration
    VALIDATE = "validate"      # Challenge and validate ideas
    GUIDE = "guide"            # Step-by-step guidance
    OUTPUT = "output"          # Generate structured output


@dataclass
class AgentState:
    """Shared state for agent reasoning"""
    # Problem clarity (from Larry)
    problem_what: Optional[str] = None
    problem_who: Optional[str] = None
    problem_success: Optional[str] = None

    # Classification
    problem_type: Optional[str] = None  # un-defined, ill-defined, well-defined

    # Conversation
    mode: ConversationMode = ConversationMode.CLARIFY
    questions_asked: int = 0
    parked_ideas: List[str] = field(default_factory=list)

    # Thinking chain
    thinking_steps: List[Dict[str, Any]] = field(default_factory=list)

    # Output
    output_requested: bool = False
    output_format: Optional[str] = None

    def problem_clarity_score(self) -> float:
        """Calculate problem clarity (0.0 to 1.0)"""
        score = 0.0
        if self.problem_what:
            score += 0.33
        if self.problem_who:
            score += 0.33
        if self.problem_success:
            score += 0.34
        return score

    def is_problem_clear(self) -> bool:
        """Check if problem is sufficiently clear"""
        return self.problem_clarity_score() >= 0.8


class MindrianAgent(ABC):
    """
    Base class for all Mindrian agents.

    Provides:
    - Multi-MCP tool integration
    - Sequential Thinking as reasoning core
    - Shared state management
    - Skill-based configuration
    """

    def __init__(
        self,
        name: str,
        skill: Optional[SkillDefinition] = None,
        model: str = "claude-sonnet-4-20250514",
        mcp_tools: Optional[List[str]] = None,
        custom_tools: Optional[List[Callable]] = None,
        mcp_manager: Optional[MCPManager] = None,
    ):
        self.name = name
        self.skill = skill
        self.model_id = model
        self.mcp_tools = mcp_tools or []
        self.custom_tools = custom_tools or []
        self._mcp_manager = mcp_manager or mcp_manager
        self._agent: Optional[Agent] = None
        self._state = AgentState()

        # Auto-detect MCP requirements from skill
        if skill and not mcp_tools:
            self.mcp_tools = skill.get_required_mcps()

    @property
    def state(self) -> AgentState:
        """Get agent state"""
        return self._state

    @abstractmethod
    def get_instructions(self) -> str:
        """Get agent instructions"""
        pass

    def build_tools(self) -> List[Callable]:
        """Build tool list from MCPs and custom tools"""
        tools = []

        # Add MCP tools
        if self._mcp_manager and self.mcp_tools:
            mcp_tools = self._mcp_manager.create_tool_functions(self.mcp_tools)
            tools.extend(mcp_tools.values())

        # Add custom tools
        tools.extend(self.custom_tools)

        return tools

    def build(self) -> Agent:
        """Build and return the Agno Agent instance"""
        if self._agent:
            return self._agent

        self._agent = Agent(
            name=self.name,
            model=Claude(id=self.model_id),
            instructions=self.get_instructions(),
            tools=self.build_tools(),
            show_tool_calls=True,
            markdown=True,
        )

        return self._agent

    async def run(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Run the agent with a message"""
        agent = self.build()
        response = await agent.arun(message)
        return response.content

    def update_state(self, **kwargs) -> None:
        """Update agent state"""
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)


class FrameworkAgent(MindrianAgent):
    """
    Agent for thinking frameworks (Minto, JTBD, PWS, etc.)

    Framework agents:
    - Process inputs through a specific methodology
    - Produce structured outputs
    - Can chain with other frameworks
    """

    def __init__(
        self,
        name: str,
        skill: SkillDefinition,
        **kwargs,
    ):
        super().__init__(name=name, skill=skill, **kwargs)

        # Framework-specific config
        self.output_format = skill.outputs[0] if skill.outputs else "markdown"
        self.can_chain_with = skill.chaining

    def get_instructions(self) -> str:
        """Get framework instructions from skill"""
        instructions = []

        # Base skill instructions
        if self.skill:
            instructions.append(self.skill.to_agent_instructions())

        # Add structured output guidance
        instructions.append(f"""
## Output Format
Produce output in the following format: {self.output_format}

## Chaining
This framework can chain with: {', '.join(self.can_chain_with) if self.can_chain_with else 'none'}
""")

        # Add Sequential Thinking guidance
        instructions.append(self._get_thinking_guidance())

        return "\n\n---\n\n".join(instructions)

    def _get_thinking_guidance(self) -> str:
        return """
## Reasoning Process

Use Sequential Thinking to process inputs:

1. **Parse Input**: Identify key themes, stakeholders, tensions
2. **Apply Framework**: Work through framework steps systematically
3. **Validate**: Check output against quality criteria
4. **Format**: Structure output according to template
"""


class ConversationalAgent(MindrianAgent):
    """
    Agent for conversational roles (Larry, Devil, etc.)

    Conversational agents:
    - Engage in dialogue with users
    - Support multiple conversation modes
    - Track problem clarity and state
    """

    def __init__(
        self,
        name: str,
        skill: SkillDefinition,
        default_mode: ConversationMode = ConversationMode.CLARIFY,
        **kwargs,
    ):
        super().__init__(name=name, skill=skill, **kwargs)
        self._state.mode = default_mode

        # Extract behavioral rules
        self.behavioral_rules = skill.behavioral_rules if skill else []
        self.tone = skill.tone if skill else ""

    def get_instructions(self) -> str:
        """Get conversational instructions from skill"""
        instructions = []

        # Base skill instructions
        if self.skill:
            instructions.append(self.skill.to_agent_instructions())

        # Add mode-specific instructions
        instructions.append(self._get_mode_instructions())

        # Add state tracking
        instructions.append(self._get_state_instructions())

        return "\n\n---\n\n".join(instructions)

    def _get_mode_instructions(self) -> str:
        """Get mode-specific instructions"""
        mode_guides = {
            ConversationMode.CLARIFY: """
## Current Mode: CLARIFY
- Ask ONE question at a time
- Keep responses under 100 words
- Challenge vague language
- Don't provide solutions until problem is clear
""",
            ConversationMode.EXPLORE: """
## Current Mode: EXPLORE
- Open-ended exploration encouraged
- Follow interesting threads
- Park ideas for later
- No pressure for clarity yet
""",
            ConversationMode.VALIDATE: """
## Current Mode: VALIDATE
- Challenge all assumptions
- Play devil's advocate
- Look for weaknesses
- Be constructively critical
""",
            ConversationMode.GUIDE: """
## Current Mode: GUIDE
- Provide step-by-step guidance
- Be patient and supportive
- Explain the 'why' behind each step
- Check understanding before proceeding
""",
            ConversationMode.OUTPUT: """
## Current Mode: OUTPUT
- Generate structured output
- Use appropriate framework
- Be comprehensive
- Include next steps
""",
        }
        return mode_guides.get(self._state.mode, "")

    def _get_state_instructions(self) -> str:
        """Get state tracking instructions"""
        return f"""
## Current State
- Problem clarity: {self._state.problem_clarity_score():.0%}
  - What: {self._state.problem_what or '[unknown]'}
  - Who: {self._state.problem_who or '[unknown]'}
  - Success: {self._state.problem_success or '[unknown]'}
- Questions asked: {self._state.questions_asked}
- Parked ideas: {len(self._state.parked_ideas)}
- Output requested: {self._state.output_requested}
"""

    def set_mode(self, mode: ConversationMode) -> None:
        """Change conversation mode"""
        self._state.mode = mode
        # Rebuild agent to update instructions
        self._agent = None

    def get_mode(self) -> ConversationMode:
        """Get current conversation mode"""
        return self._state.mode

    def park_idea(self, idea: str) -> None:
        """Park an idea for later"""
        self._state.parked_ideas.append(idea)

    def get_parked_ideas(self) -> List[str]:
        """Get parked ideas"""
        return self._state.parked_ideas


def create_agent_from_skill(
    skill: SkillDefinition,
    mcp_manager: Optional[MCPManager] = None,
    **kwargs,
) -> Union[FrameworkAgent, ConversationalAgent, MindrianAgent]:
    """
    Factory function to create appropriate agent type from skill.

    Args:
        skill: SkillDefinition from SKILL.md
        mcp_manager: Optional MCP manager
        **kwargs: Additional agent configuration

    Returns:
        Appropriate agent instance based on skill type
    """
    if skill.type == SkillType.ROLE:
        return ConversationalAgent(
            name=skill.name,
            skill=skill,
            mcp_manager=mcp_manager,
            **kwargs,
        )
    elif skill.type in (SkillType.OPERATOR, SkillType.COLLABORATIVE, SkillType.PIPELINE):
        return FrameworkAgent(
            name=skill.name,
            skill=skill,
            mcp_manager=mcp_manager,
            **kwargs,
        )
    else:
        # Default to framework agent
        return FrameworkAgent(
            name=skill.name,
            skill=skill,
            mcp_manager=mcp_manager,
            **kwargs,
        )
