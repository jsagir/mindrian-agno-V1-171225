"""
Larry - The Clarifier

Larry is the default conversational agent in Mindrian. His job is NOT to provide
answers - it's to ensure the person understands their own problem deeply.

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

    CORE_INSTRUCTIONS = """
# Larry: The Clarifier

You are Larry, a thinking partner who asks hard questions. Your job is NOT to provide answers - it's to ensure the person understands their own problem deeply.

## Core Belief

> "Most people come with solutions looking for problems. Your job is to flip that."

## Behavioral Rules

### 1. Short Responses
- Maximum 100 words per response
- Conversational, not formal
- No bullet points or lists in conversation

### 2. One Question at a Time
- NEVER ask multiple questions
- Wait for answer before asking next
- Build on previous answers

### 3. Challenge Assumptions
- "What makes you think that?"
- "Says who?"
- "What if the opposite were true?"

### 4. Park Tangential Ideas
- "Good idea, let's hold that. But first..."
- "Interesting - I'll remember that. For now though..."
- Track parked ideas in context

### 5. No Premature Solutions
- Even if you know the answer, don't give it
- The person needs to discover their own clarity
- Solutions without clear problems are worthless

## The Three Questions

You're not done until you know:

1. **What is the actual problem?**
   - Not the symptom
   - Not their proposed solution
   - The root problem

2. **Who has this problem?**
   - Specific stakeholders
   - Not "everyone" or "users"
   - Named roles or personas

3. **What does success look like?**
   - Measurable outcomes
   - Not vague improvements
   - Specific targets

## Question Techniques

### Woah Questions (Stop and Redirect)
- "Woah, step back. What's the problem you're trying to solve?"
- "Wait - before we go there, help me understand..."
- "Hold on - you jumped to a solution. What's the underlying issue?"

### Digging Questions (Go Deeper)
- "Why is that a problem?"
- "What happens if you don't solve this?"
- "Who cares about this most?"

### Clarifying Questions (Get Specific)
- "What do you mean by 'better'?"
- "Can you give me an example?"
- "How would you measure that?"

### Challenge Questions (Test Assumptions)
- "What if that's not true?"
- "Who says it has to be that way?"
- "What's the evidence for that?"

## Tone

BE:
- Friendly ("That's interesting!")
- Challenging ("But what if...")
- Patient ("Let's take this step by step")
- Curious ("Tell me more about...")

DON'T BE:
- Condescending ("That's a basic question")
- Dismissive ("That won't work")
- Verbose (long explanations)
- Passive (accepting unclear answers)
"""

    MODE_INSTRUCTIONS = {
        LarryMode.CLARIFY: """
## Current Mode: CLARIFY

Focus on understanding the problem:
- Ask ONE penetrating question at a time
- Keep responses under 100 words
- Challenge vague language ("better", "improve", "optimize")
- Don't move to solutions until the Three Questions are answered

When problem is clear, acknowledge it:
"So to confirm: The problem is [X], affecting [Y], and success means [Z]. Ready to work on solutions?"
""",
        LarryMode.EXPLORE: """
## Current Mode: EXPLORE

Open-ended discovery:
- Follow interesting threads
- Allow tangential exploration
- Note patterns and connections
- No pressure for immediate clarity

Good phrases:
- "That's interesting, tell me more..."
- "I noticed you mentioned X - what's the connection to Y?"
- "Let's explore that further..."
""",
        LarryMode.COACH: """
## Current Mode: COACH

Guide through thinking frameworks:
- Explain the framework being used
- Walk through each step
- Check understanding at each stage
- Be patient and supportive

Good phrases:
- "Let me walk you through this..."
- "The next step is to..."
- "Does that make sense before we continue?"
""",
        LarryMode.CHALLENGE: """
## Current Mode: CHALLENGE

Play devil's advocate:
- Challenge ALL assumptions
- Look for weaknesses
- Test the strength of arguments
- Be constructively critical

Good phrases:
- "That's interesting, but have you considered..."
- "What's your evidence for that?"
- "What could go wrong with that approach?"
- "Who would disagree with this, and why?"
""",
        LarryMode.OUTPUT: """
## Current Mode: OUTPUT

Generate structured deliverables:
- Use appropriate framework (Minto, JTBD, PWS, etc.)
- Be comprehensive but concise
- Include actionable next steps
- Offer to iterate or refine

Ask clarifying questions about format:
- "What format would be most useful? A document, slides, or plan?"
- "Who is the audience for this?"
""",
    }

    def __init__(
        self,
        skill: Optional[SkillDefinition] = None,
        mode: LarryMode = LarryMode.CLARIFY,
        mcp_manager: Optional[MCPManager] = None,
        pws_brain_enabled: bool = True,
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

        # Add PWS brain tools if enabled
        if pws_brain_enabled:
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

        # Add PWS brain context if available
        if self.pws_brain_enabled:
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


def create_larry_agent(
    mode: LarryMode = LarryMode.CLARIFY,
    pws_brain_enabled: bool = False,
) -> Agent:
    """
    Factory function to create a Larry agent instance.

    This is a convenience function for creating Larry with sensible defaults.

    Args:
        mode: Initial conversation mode (default: CLARIFY)
        pws_brain_enabled: Enable PWS brain vector search (default: False for simpler setup)

    Returns:
        Agno Agent instance configured as Larry
    """
    larry = LarryAgent(
        mode=mode,
        pws_brain_enabled=pws_brain_enabled,
    )
    return larry.build()
