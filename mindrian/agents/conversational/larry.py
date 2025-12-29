"""
Larry - The Clarifier (High-Grade Implementation)

Larry is the default conversational agent in Mindrian. His job is NOT to provide
answers - it's to ensure the person understands their own problem deeply.

This implementation uses the Neo4j-validated system prompt that incorporates
the full PWS methodology, including:
- Problem Classification (Un-defined, Ill-defined, Well-defined)
- Question Techniques (Woah, Digging, Clarifying, Challenge, Beautiful)
- Framework Chains (Cynefin → JTBD, Minto → Issue Trees, etc.)
- Tool Triggering Logic (when to call each framework agent)

## Modes

1. CLARIFY (default) - Ask penetrating questions until problem is clear
2. EXPLORE - Open-ended exploration, follow interesting threads
3. COACH - Guide through frameworks step-by-step
4. CHALLENGE - Play devil's advocate on proposals
5. OUTPUT - Generate structured output when ready

## The Three Questions

Larry isn't done until he knows:
1. What is the actual problem? (not the symptom, not the solution)
2. Who has this problem? (specific stakeholders)
3. What does success look like? (measurable outcomes)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from agno.agent import Agent
from agno.models.anthropic import Claude

from ..base import ConversationalAgent, ConversationMode, AgentState
from ...registry.skill_loader import SkillLoader, SkillDefinition
from ...registry.mcp_manager import MCPManager
from ...prompts.larry_system_prompt import (
    get_larry_prompt,
    get_mode_instructions,
    LARRY_IDENTITY,
    LARRY_BEHAVIORAL_RULES,
    LARRY_QUESTION_TECHNIQUES,
    LARRY_PROBLEM_CLASSIFICATION,
    LARRY_TOOL_TRIGGERING,
)
from ...graphrag import get_graphrag_tools


class LarryMode(str, Enum):
    """Larry's conversation modes"""
    CLARIFY = "clarify"      # Default: understand the problem
    EXPLORE = "explore"      # Open-ended discovery
    COACH = "coach"          # Guide through frameworks
    CHALLENGE = "challenge"  # Play devil's advocate
    OUTPUT = "output"        # Generate deliverables


@dataclass
class LarryState(AgentState):
    """Extended state for Larry"""
    # Problem clarity tracking
    assumptions_challenged: List[str] = None
    question_techniques_used: List[str] = None

    # Session tracking
    session_summary: Optional[str] = None
    recommended_frameworks: List[str] = None

    def __post_init__(self):
        self.assumptions_challenged = self.assumptions_challenged or []
        self.question_techniques_used = self.question_techniques_used or []
        self.recommended_frameworks = self.recommended_frameworks or []


class LarryAgent(ConversationalAgent):
    """
    Larry - The Clarifier

    The default entry point for Mindrian conversations.
    Asks hard questions before providing answers.
    """

    # Use the Neo4j-validated high-grade system prompt
    CORE_INSTRUCTIONS = f"""
{LARRY_IDENTITY}

{LARRY_BEHAVIORAL_RULES}

{LARRY_QUESTION_TECHNIQUES}

{LARRY_PROBLEM_CLASSIFICATION}

{LARRY_TOOL_TRIGGERING}
"""

    # Mode instructions now use the helper function for consistency
    MODE_INSTRUCTIONS = {
        LarryMode.CLARIFY: get_mode_instructions("clarify"),
        LarryMode.EXPLORE: get_mode_instructions("explore"),
        LarryMode.COACH: get_mode_instructions("coach"),
        LarryMode.CHALLENGE: get_mode_instructions("challenge"),
        LarryMode.OUTPUT: get_mode_instructions("output"),
    }

    def __init__(
        self,
        skill: Optional[SkillDefinition] = None,
        mode: LarryMode = LarryMode.CLARIFY,
        mcp_manager: Optional[MCPManager] = None,
        pws_brain_enabled: bool = True,
        graphrag_enabled: bool = True,
        **kwargs,
    ):
        # Use provided skill or create default
        if not skill:
            skill = self._create_default_skill()

        super().__init__(
            name="larry",
            skill=skill,
            default_mode=ConversationMode(mode.value),
            mcp_manager=mcp_manager,
            **kwargs,
        )

        self._larry_mode = mode
        self._larry_state = LarryState()
        self.pws_brain_enabled = pws_brain_enabled
        self.graphrag_enabled = graphrag_enabled

        # GraphRAG tools (hybrid vector + graph retrieval)
        self._graphrag_tools = []
        if graphrag_enabled:
            try:
                self._graphrag_tools = get_graphrag_tools()
            except ImportError:
                print("Warning: GraphRAG tools not available")

        # Add PWS brain tools if enabled (legacy fallback)
        if pws_brain_enabled and not graphrag_enabled:
            self.mcp_tools.append("pinecone")  # For vector search

    @staticmethod
    def _create_default_skill() -> SkillDefinition:
        """Create default Larry skill definition"""
        from ...registry.skill_loader import SkillType

        return SkillDefinition(
            name="larry",
            type=SkillType.ROLE,
            description="The Clarifier - asks penetrating questions",
            instructions=LarryAgent.CORE_INSTRUCTIONS,
            triggers=["default for new conversations", "vague requests"],
            behavioral_rules=[
                "short responses (under 100 words)",
                "one question at a time",
                "challenge assumptions",
                "park tangential ideas",
                "never provide solutions until problem is clear",
            ],
            tone="friendly, challenging, patient, pedagogical",
        )

    def get_instructions(self) -> str:
        """Build Larry's instructions based on current mode"""
        instructions = [self.CORE_INSTRUCTIONS]

        # Add mode-specific instructions
        mode_inst = self.MODE_INSTRUCTIONS.get(self._larry_mode, "")
        if mode_inst:
            instructions.append(mode_inst)

        # Add current state
        instructions.append(self._get_state_context())

        # Add GraphRAG context if available
        if self.graphrag_enabled:
            instructions.append("""
## GraphRAG Knowledge Integration

You have access to Larry's hybrid knowledge retrieval system combining:
1. **Semantic Search** - Find similar content via Pinecone vector search
2. **Knowledge Graph** - Traverse relationships via Neo4j graph

**Available Tools:**
- `search_pws_knowledge(query)` - Search frameworks and methodologies
- `get_framework_details(name)` - Get details about a specific framework
- `get_problem_type_guidance(type)` - Get frameworks for un/ill/well-defined problems
- `find_related_concepts(concept)` - Explore connected concepts
- `get_framework_chain(framework)` - Find recommended framework chains
- `detect_problem_type(message)` - Classify the user's problem type

**When to Use:**
- When user asks about frameworks → `get_framework_details`
- When problem type is clear → `get_problem_type_guidance`
- When exploring connections → `find_related_concepts`
- When user needs methodology path → `get_framework_chain`
""")
        elif self.pws_brain_enabled:
            instructions.append("""
## PWS Brain Integration

You have access to Larry's Personal Wisdom System (PWS) - a knowledge base of
frameworks, methodologies, and structured thinking approaches. Use the vector
search tools to retrieve relevant context when the user's problem relates to
known frameworks.
""")

        return "\n\n---\n\n".join(instructions)

    def _get_state_context(self) -> str:
        """Get current state as context for instructions"""
        s = self._larry_state
        return f"""
## Current Conversation State

**Problem Clarity: {s.problem_clarity_score():.0%}**
- What is the problem: {s.problem_what or '[Not yet clear]'}
- Who has this problem: {s.problem_who or '[Not yet identified]'}
- What is success: {s.problem_success or '[Not yet defined]'}

**Session Info:**
- Questions asked: {s.questions_asked}
- Parked ideas: {len(s.parked_ideas)}
- Assumptions challenged: {len(s.assumptions_challenged)}

**Parked Ideas:** {', '.join(s.parked_ideas) if s.parked_ideas else 'None'}
"""

    def set_mode(self, mode: LarryMode) -> None:
        """Change Larry's mode"""
        self._larry_mode = mode
        self._state.mode = ConversationMode(mode.value)
        self._agent = None  # Rebuild agent

    def get_mode(self) -> LarryMode:
        """Get current mode"""
        return self._larry_mode

    def update_problem_clarity(
        self,
        what: Optional[str] = None,
        who: Optional[str] = None,
        success: Optional[str] = None,
    ) -> float:
        """Update problem clarity and return score"""
        if what:
            self._larry_state.problem_what = what
        if who:
            self._larry_state.problem_who = who
        if success:
            self._larry_state.problem_success = success

        return self._larry_state.problem_clarity_score()

    def record_question(self, technique: Optional[str] = None) -> None:
        """Record that a question was asked"""
        self._larry_state.questions_asked += 1
        if technique:
            self._larry_state.question_techniques_used.append(technique)

    def challenge_assumption(self, assumption: str) -> None:
        """Record a challenged assumption"""
        self._larry_state.assumptions_challenged.append(assumption)

    def recommend_framework(self, framework: str) -> None:
        """Recommend a framework based on problem type"""
        if framework not in self._larry_state.recommended_frameworks:
            self._larry_state.recommended_frameworks.append(framework)

    def should_transition_to_output(self) -> bool:
        """Check if ready to transition to output mode"""
        return (
            self._larry_state.is_problem_clear()
            or self._larry_state.output_requested
            or self._larry_state.questions_asked > 10
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        s = self._larry_state
        return {
            "problem_clarity": s.problem_clarity_score(),
            "problem": {
                "what": s.problem_what,
                "who": s.problem_who,
                "success": s.problem_success,
            },
            "problem_type": s.problem_type,
            "questions_asked": s.questions_asked,
            "parked_ideas": s.parked_ideas,
            "assumptions_challenged": s.assumptions_challenged,
            "recommended_frameworks": s.recommended_frameworks,
            "ready_for_output": self.should_transition_to_output(),
        }


    def get_tools(self) -> List:
        """Get all tools for this agent including GraphRAG tools"""
        tools = []

        # Add GraphRAG tools if enabled
        if self.graphrag_enabled and self._graphrag_tools:
            tools.extend(self._graphrag_tools)

        return tools


def create_larry_agent(
    mode: LarryMode = LarryMode.CLARIFY,
    pws_brain_enabled: bool = True,
    graphrag_enabled: bool = True,
    use_compact_prompt: bool = False,
) -> Agent:
    """
    Factory function to create a high-grade Larry agent instance.

    This uses the Neo4j-validated system prompt that incorporates the full
    PWS methodology including:
    - Problem Classification (Un-defined, Ill-defined, Well-defined)
    - Question Techniques (Woah, Digging, Clarifying, Challenge, Beautiful)
    - Framework Chains (Cynefin → JTBD, Minto → Issue Trees, etc.)
    - Tool Triggering Logic (when to call each framework agent)

    Args:
        mode: Initial conversation mode (default: CLARIFY)
        pws_brain_enabled: Enable PWS brain vector search (default: True)
        graphrag_enabled: Enable GraphRAG hybrid retrieval (default: True)
        use_compact_prompt: Use shorter prompt for API efficiency (default: False)

    Returns:
        Agno Agent instance configured as high-grade Larry with GraphRAG tools
    """
    larry = LarryAgent(
        mode=mode,
        pws_brain_enabled=pws_brain_enabled,
        graphrag_enabled=graphrag_enabled,
    )

    # Build with GraphRAG tools
    agent = larry.build()

    # Add GraphRAG tools to agent if available
    if graphrag_enabled and larry._graphrag_tools:
        if hasattr(agent, 'tools') and agent.tools is None:
            agent.tools = larry._graphrag_tools
        elif hasattr(agent, 'tools'):
            agent.tools = list(agent.tools or []) + larry._graphrag_tools

    return agent


def get_tool_trigger_conditions() -> Dict[str, Dict[str, Any]]:
    """
    Get the conditions under which each tool should be triggered.

    Returns a dictionary mapping tool names to their trigger conditions,
    based on the Neo4j-validated PWS methodology.

    Returns:
        Dict mapping tool names to trigger conditions
    """
    return {
        # Research Tools
        "pws_search": {
            "triggers": [
                "user mentions a domain or methodology",
                "problem type becomes clear",
                "user is stuck and needs framework guidance",
            ],
            "clarity_threshold": 0.0,  # Can use anytime
        },
        "patent_search": {
            "triggers": [
                "user mentions patents, IP, intellectual property",
                "innovation involves technical invention",
                "user asks about prior art or freedom to operate",
            ],
            "clarity_threshold": 0.3,
        },
        "web_research": {
            "triggers": [
                "need current market data or trends",
                "user references specific companies or industries",
                "fact-checking claims about market size or competitors",
            ],
            "clarity_threshold": 0.3,
        },

        # Framework Agents
        "pws_validation": {
            "triggers": [
                "problem is clear (clarity > 70%)",
                "user wants validation",
                "user asks 'is this a good idea?' or 'should I pursue this?'",
            ],
            "clarity_threshold": 0.7,
            "requires": ["what", "who", "success"],
            "output": "GO (>75%) / PIVOT (50-75%) / NO-GO (<50%)",
        },
        "jobs_to_be_done": {
            "triggers": [
                "problem is ill-defined AND involves customer behavior",
                "user asks 'what do customers want?' or 'why do they buy?'",
            ],
            "clarity_threshold": 0.4,
            "problem_type": "ill-defined",
            "output": "Functional, Emotional, Social jobs mapped",
        },
        "minto_pyramid": {
            "triggers": [
                "user has messy thinking needing structure",
                "user needs to communicate complex idea",
                "user asks for help organizing thoughts",
            ],
            "clarity_threshold": 0.5,
            "output": "SCQA structure",
        },
        "devil_advocate": {
            "triggers": [
                "user seems too confident in their idea",
                "problem is well-defined, ready for stress-testing",
                "user asks 'what could go wrong?'",
            ],
            "clarity_threshold": 0.6,
            "problem_type": "well-defined",
            "intensity_levels": ["light", "medium", "heavy"],
        },
        "beautiful_question": {
            "triggers": [
                "user is stuck in conventional thinking",
                "problem needs creative reframing",
            ],
            "clarity_threshold": 0.3,
            "output": "Why? What if? How might we? questions",
        },
        "trending_to_absurd": {
            "triggers": [
                "problem involves long-term trends",
                "user asks about future possibilities",
            ],
            "clarity_threshold": 0.3,
            "problem_type": "un-defined",
            "output": "10-year trend extrapolation",
        },
        "scenario_analysis": {
            "triggers": [
                "high uncertainty about future",
                "multiple possible outcomes",
            ],
            "clarity_threshold": 0.4,
            "problem_type": "un-defined",
            "output": "2x2 matrix of scenarios",
        },

        # Teams (Multi-Agent)
        "validation_team": {
            "chain": ["pws_validation", "devil_advocate", "jobs_to_be_done"],
            "triggers": [
                "user has clear opportunity needing full validation",
                "ready to invest resources and wants due diligence",
            ],
            "clarity_threshold": 0.7,
        },
        "exploration_team": {
            "parallel": ["cynefin", "scenario_analysis", "trending_to_absurd"],
            "triggers": [
                "completely new domain",
                "user exploring 5+ year horizons",
            ],
            "clarity_threshold": 0.2,
            "problem_type": "un-defined",
        },
        "strategy_team": {
            "chain": ["minto_pyramid", "business_model_canvas", "golden_circle"],
            "triggers": [
                "user needs to communicate strategy",
                "preparing for pitch or stakeholder presentation",
            ],
            "clarity_threshold": 0.6,
        },
    }


def should_trigger_tool(
    tool_name: str,
    clarity_score: float,
    problem_type: Optional[str] = None,
    has_what: bool = False,
    has_who: bool = False,
    has_success: bool = False,
) -> bool:
    """
    Determine if a tool should be triggered based on current state.

    Args:
        tool_name: Name of the tool to check
        clarity_score: Current problem clarity score (0.0-1.0)
        problem_type: Current problem classification (un-defined, ill-defined, well-defined)
        has_what: Whether 'what' is defined
        has_who: Whether 'who' is defined
        has_success: Whether 'success' is defined

    Returns:
        True if the tool should be triggered
    """
    conditions = get_tool_trigger_conditions().get(tool_name)
    if not conditions:
        return False

    # Check clarity threshold
    if clarity_score < conditions.get("clarity_threshold", 0.0):
        return False

    # Check problem type if required
    required_type = conditions.get("problem_type")
    if required_type and problem_type != required_type:
        return False

    # Check required fields
    requires = conditions.get("requires", [])
    if "what" in requires and not has_what:
        return False
    if "who" in requires and not has_who:
        return False
    if "success" in requires and not has_success:
        return False

    return True
