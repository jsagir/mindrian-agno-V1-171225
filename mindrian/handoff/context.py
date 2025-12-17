"""
Handoff Context - The State That Travels Between Agents

This is the CRITICAL piece: what information passes between agents during handoffs.
Good context = good handoffs. Bad context = agents working blind.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .types import HandoffType, HandoffMode, ReturnBehavior


class ClarityLevel(str, Enum):
    """How clear is the problem definition?"""
    UNCLEAR = "unclear"           # < 30% clarity
    PARTIAL = "partial"           # 30-60% clarity
    MOSTLY_CLEAR = "mostly_clear" # 60-85% clarity
    CLEAR = "clear"               # > 85% clarity


@dataclass
class ProblemClarity:
    """
    Larry's assessment of problem understanding.
    This is THE foundation for all downstream work.
    """

    # The Three Questions
    what: Optional[str] = None      # What is the actual problem?
    who: Optional[str] = None       # Who has this problem?
    success: Optional[str] = None   # What does success look like?

    # Clarity scores (0.0 - 1.0)
    what_clarity: float = 0.0
    who_clarity: float = 0.0
    success_clarity: float = 0.0

    # Assumptions identified
    assumptions: List[str] = field(default_factory=list)

    # Questions still open
    open_questions: List[str] = field(default_factory=list)

    @property
    def overall_clarity(self) -> float:
        """Overall clarity score (0.0 - 1.0)"""
        return (self.what_clarity + self.who_clarity + self.success_clarity) / 3

    @property
    def clarity_level(self) -> ClarityLevel:
        """Human-readable clarity level"""
        score = self.overall_clarity
        if score < 0.3:
            return ClarityLevel.UNCLEAR
        elif score < 0.6:
            return ClarityLevel.PARTIAL
        elif score < 0.85:
            return ClarityLevel.MOSTLY_CLEAR
        else:
            return ClarityLevel.CLEAR

    @property
    def is_ready_for_analysis(self) -> bool:
        """Is the problem clear enough for framework analysis?"""
        return self.overall_clarity >= 0.6

    def to_prompt(self) -> str:
        """Format for inclusion in agent prompts"""
        return f"""## Problem Clarity Assessment

**What is the problem?**
{self.what or '[Not yet clear]'}
Clarity: {self.what_clarity:.0%}

**Who has this problem?**
{self.who or '[Not yet clear]'}
Clarity: {self.who_clarity:.0%}

**What does success look like?**
{self.success or '[Not yet clear]'}
Clarity: {self.success_clarity:.0%}

**Overall Clarity:** {self.overall_clarity:.0%} ({self.clarity_level.value})

**Assumptions to validate:**
{chr(10).join(f'- {a}' for a in self.assumptions) or '- None identified'}

**Open questions:**
{chr(10).join(f'- {q}' for q in self.open_questions) or '- None remaining'}
"""


@dataclass
class ConversationSummary:
    """
    Compressed conversation history for context passing.
    We don't pass full history—we pass RELEVANT history.
    """

    # Key points from conversation
    key_points: List[str] = field(default_factory=list)

    # User's stated goals
    user_goals: List[str] = field(default_factory=list)

    # Constraints mentioned
    constraints: List[str] = field(default_factory=list)

    # Preferences expressed
    preferences: List[str] = field(default_factory=list)

    # Turn count
    turn_count: int = 0

    # Last N messages (raw, for reference)
    recent_messages: List[Dict[str, str]] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Format for inclusion in agent prompts"""
        sections = ["## Conversation Context"]

        if self.user_goals:
            sections.append("**User's Goals:**")
            sections.extend([f"- {g}" for g in self.user_goals])

        if self.key_points:
            sections.append("\n**Key Points Discussed:**")
            sections.extend([f"- {p}" for p in self.key_points])

        if self.constraints:
            sections.append("\n**Constraints:**")
            sections.extend([f"- {c}" for c in self.constraints])

        if self.preferences:
            sections.append("\n**User Preferences:**")
            sections.extend([f"- {p}" for p in self.preferences])

        return "\n".join(sections)


@dataclass
class PreviousAnalysis:
    """Output from a previously run framework"""
    framework_id: str
    framework_name: str
    output: str
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HandoffContext:
    """
    THE COMPLETE CONTEXT FOR A HANDOFF.

    This is what travels from one agent to another.
    Every field has a purpose. Nothing is optional fluff.
    """

    # === IDENTITY ===
    handoff_id: str = ""                    # Unique ID for tracking
    timestamp: datetime = field(default_factory=datetime.now)

    # === PROBLEM DEFINITION (from Larry) ===
    problem_clarity: ProblemClarity = field(default_factory=ProblemClarity)

    # === CONVERSATION STATE ===
    conversation: ConversationSummary = field(default_factory=ConversationSummary)
    session_id: Optional[str] = None

    # === PREVIOUS WORK ===
    previous_analyses: List[PreviousAnalysis] = field(default_factory=list)

    # === HANDOFF INSTRUCTIONS ===
    task_description: str = ""              # What the receiving agent should do
    expected_output: str = ""               # What format/content expected
    focus_areas: List[str] = field(default_factory=list)  # Specific areas to analyze
    ignore_areas: List[str] = field(default_factory=list)  # What to skip

    # === ROUTING INFO ===
    from_agent: str = ""                    # Who is sending
    to_agent: str = ""                      # Who is receiving
    return_to: str = ""                     # Who gets the results
    return_behavior: ReturnBehavior = ReturnBehavior.SYNTHESIZE

    # === METADATA ===
    handoff_type: HandoffType = HandoffType.DELEGATE
    handoff_mode: HandoffMode = HandoffMode.SEQUENTIAL
    priority: int = 1                       # 1=normal, 2=high, 3=urgent
    timeout_seconds: int = 300              # Max time for handoff

    # === CUSTOM DATA ===
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt(self) -> str:
        """
        Generate the complete prompt context for the receiving agent.
        This is what the agent sees when it receives the handoff.
        """
        sections = []

        # Header
        sections.append(f"# Handoff from {self.from_agent}")
        sections.append(f"*Handoff ID: {self.handoff_id}*\n")

        # Task
        sections.append("## Your Task")
        sections.append(self.task_description)
        if self.expected_output:
            sections.append(f"\n**Expected Output:** {self.expected_output}")

        # Problem Clarity
        sections.append("\n" + self.problem_clarity.to_prompt())

        # Conversation Context
        if self.conversation.key_points or self.conversation.user_goals:
            sections.append("\n" + self.conversation.to_prompt())

        # Previous Analyses
        if self.previous_analyses:
            sections.append("\n## Previous Analyses")
            for analysis in self.previous_analyses:
                sections.append(f"\n### {analysis.framework_name}")
                if analysis.key_findings:
                    sections.append("**Key Findings:**")
                    sections.extend([f"- {f}" for f in analysis.key_findings])
                if analysis.recommendations:
                    sections.append("**Recommendations:**")
                    sections.extend([f"- {r}" for r in analysis.recommendations])

        # Focus Areas
        if self.focus_areas:
            sections.append("\n## Focus Areas")
            sections.extend([f"- {f}" for f in self.focus_areas])

        if self.ignore_areas:
            sections.append("\n## Areas to Skip")
            sections.extend([f"- {i}" for i in self.ignore_areas])

        # Return Instructions
        sections.append(f"\n## Return Instructions")
        sections.append(f"Return your results to: **{self.return_to}**")
        sections.append(f"Return behavior: **{self.return_behavior.value}**")

        return "\n".join(sections)

    @classmethod
    def from_larry(
        cls,
        problem_what: str,
        problem_who: str,
        problem_success: str,
        task: str,
        to_agent: str,
        **kwargs
    ) -> "HandoffContext":
        """
        Convenience constructor for Larry's delegation.
        """
        import uuid

        clarity = ProblemClarity(
            what=problem_what,
            who=problem_who,
            success=problem_success,
            what_clarity=0.8 if problem_what else 0.0,
            who_clarity=0.8 if problem_who else 0.0,
            success_clarity=0.8 if problem_success else 0.0,
        )

        return cls(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=clarity,
            task_description=task,
            from_agent="larry",
            to_agent=to_agent,
            return_to="larry",
            **kwargs
        )


@dataclass
class HandoffResult:
    """
    What comes back from a completed handoff.
    """

    # === IDENTITY ===
    handoff_id: str                         # Matches original handoff
    from_agent: str                         # Who completed the work
    to_agent: str                           # Who receives results

    # === RESULTS ===
    success: bool = True
    output: str = ""                        # Main output content
    output_format: str = "markdown"         # markdown, json, structured

    # === STRUCTURED DATA ===
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0                 # 0.0-1.0 confidence in results
    scores: Dict[str, float] = field(default_factory=dict)  # Any numerical scores

    # === FOLLOW-UP ===
    suggested_next_agents: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    needs_human_input: bool = False
    human_input_reason: str = ""

    # === METADATA ===
    duration_seconds: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_analysis(self) -> PreviousAnalysis:
        """Convert to PreviousAnalysis for chaining"""
        return PreviousAnalysis(
            framework_id=self.from_agent,
            framework_name=self.from_agent,
            output=self.output,
            key_findings=self.key_findings,
            recommendations=self.recommendations,
            confidence=self.confidence,
            timestamp=self.timestamp,
        )

    def to_prompt(self) -> str:
        """Format results for next agent or synthesis"""
        sections = [f"# Results from {self.from_agent}"]

        if not self.success:
            sections.append(f"\n**ERROR:** {self.error}")
            return "\n".join(sections)

        sections.append(f"\n## Output\n{self.output}")

        if self.key_findings:
            sections.append("\n## Key Findings")
            sections.extend([f"- {f}" for f in self.key_findings])

        if self.recommendations:
            sections.append("\n## Recommendations")
            sections.extend([f"- {r}" for r in self.recommendations])

        if self.scores:
            sections.append("\n## Scores")
            for name, score in self.scores.items():
                sections.append(f"- {name}: {score}")

        if self.confidence:
            sections.append(f"\n**Confidence:** {self.confidence:.0%}")

        if self.suggested_next_agents:
            sections.append("\n## Suggested Next Steps")
            sections.extend([f"- Consult {a}" for a in self.suggested_next_agents])

        if self.open_questions:
            sections.append("\n## Open Questions")
            sections.extend([f"- {q}" for q in self.open_questions])

        return "\n".join(sections)
