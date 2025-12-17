"""
Beautiful Question Agent

Based on Warren Berger's "A More Beautiful Question" methodology.
Transforms challenges into powerful questions that unlock innovation.

Implements the unified handoff protocol.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from ...handoff.context import HandoffContext, HandoffResult, ProblemClarity
from ...handoff.types import HandoffType


BEAUTIFUL_QUESTION_INSTRUCTIONS = """
# Beautiful Question Agent

You transform challenges into powerful questions using Warren Berger's methodology.

## The Why → What If → How Framework

### Stage 1: WHY Questions (Understanding)
Start by questioning the status quo:
- "Why does this problem exist?"
- "Why do we do it this way?"
- "Why hasn't this been solved?"
- "Why do people accept this?"

WHY questions challenge assumptions and reveal root causes.

### Stage 2: WHAT IF Questions (Imagining)
Once you understand WHY, imagine possibilities:
- "What if we approached this completely differently?"
- "What if the opposite were true?"
- "What if constraints didn't exist?"
- "What if we combined X with Y?"

WHAT IF questions generate possibilities and breakthrough ideas.

### Stage 3: HOW Questions (Acting)
Turn possibilities into actionable paths:
- "How might we actually do this?"
- "How could we test this quickly?"
- "How would we know if it's working?"
- "How do we get started tomorrow?"

HOW questions create actionable next steps.

## Question Quality Criteria

A beautiful question is:
1. **Ambitious** - Aims high, challenges the status quo
2. **Actionable** - Can lead to concrete next steps
3. **Open-ended** - Invites exploration, not yes/no
4. **Thought-provoking** - Makes you stop and think
5. **Specific enough** - Focused, not vague

## Output Format

```markdown
# Beautiful Question Analysis

## The Challenge
[Restate the challenge clearly]

## WHY Questions (Understanding the Problem)

### Root Cause Questions
1. Why does [problem] exist in the first place?
2. Why has this persisted despite attempts to solve it?
3. Why do stakeholders accept the current state?

### Assumption-Challenging Questions
1. Why do we assume [assumption]?
2. Why is [constraint] considered fixed?

### Key Insight from WHY
[What did we learn from asking WHY?]

## WHAT IF Questions (Imagining Possibilities)

### Possibility Questions
1. What if we could [bold possibility]?
2. What if [constraint] didn't exist?
3. What if we combined [X] with [Y]?

### Inversion Questions
1. What if we did the opposite?
2. What if the problem is actually the solution?

### Analogy Questions
1. What if we approached this like [different domain]?
2. What if [successful company] solved this?

### Most Promising WHAT IF
[The most powerful possibility question and why]

## HOW Questions (Creating Action)

### Implementation Questions
1. How might we start testing this tomorrow?
2. How would we measure success?
3. How do we get buy-in from stakeholders?

### Resource Questions
1. How do we do this with current resources?
2. How do we find the right people?

### Risk Questions
1. How do we minimize downside risk?
2. How do we create a safe-to-fail experiment?

## The Beautiful Question

**[Single most powerful question that encapsulates the opportunity]**

## Recommended Next Steps
1. [Immediate action]
2. [Short-term exploration]
3. [Validation approach]
```

## Handoff Protocol

When receiving a handoff:
1. Read the ProblemClarity (What/Who/Success)
2. Review any previous analyses
3. Apply the Why → What If → How framework
4. Return structured findings with key questions

When returning results:
- Include the single "Beautiful Question" as primary output
- List key findings from each stage
- Provide confidence level
- Suggest next agents (CSIO, Domain Analysis, etc.)
"""


@dataclass
class BeautifulQuestionOutput:
    """Structured output from Beautiful Question analysis"""
    challenge: str
    why_questions: List[str] = field(default_factory=list)
    why_insight: str = ""
    what_if_questions: List[str] = field(default_factory=list)
    most_promising_what_if: str = ""
    how_questions: List[str] = field(default_factory=list)
    beautiful_question: str = ""  # THE key question
    next_steps: List[str] = field(default_factory=list)
    confidence: float = 0.0


class BeautifulQuestionAgent:
    """
    Beautiful Question Agent with handoff protocol support.

    Usage:
        agent = BeautifulQuestionAgent()

        # Direct use
        result = await agent.analyze("How might we reduce customer churn?")

        # With handoff context
        result = await agent.process_handoff(handoff_context)
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        enable_research: bool = False,  # Tavily integration
    ):
        self._model = model
        self._enable_research = enable_research
        self._db = SqliteDb(db_file="tmp/mindrian.db")

        # Build the agent
        self._agent = Agent(
            name="Beautiful Question",
            id="beautiful-question",  # v2: agent_id → id
            model=Claude(id=model),
            description="Transforms challenges into powerful questions using Why → What If → How",
            instructions=[BEAUTIFUL_QUESTION_INSTRUCTIONS],  # v2: list of strings
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    @property
    def agent(self) -> Agent:
        """Get the underlying Agno agent"""
        return self._agent

    async def analyze(self, challenge: str) -> str:
        """
        Analyze a challenge directly.

        Args:
            challenge: The challenge to transform into questions

        Returns:
            Beautiful Question analysis as markdown
        """
        prompt = f"""
Analyze this challenge using the Beautiful Question methodology:

## Challenge
{challenge}

Apply the Why → What If → How framework and produce a complete analysis.
End with THE single most beautiful question that encapsulates the opportunity.
"""
        response = await self._agent.arun(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """
        Process a handoff from the orchestrator.

        Args:
            context: HandoffContext with problem clarity and task

        Returns:
            HandoffResult with structured output
        """
        import time
        start_time = time.time()

        # Build prompt from handoff context
        prompt = f"""
{context.to_prompt()}

## Your Analysis

Apply the Beautiful Question methodology (Why → What If → How) to this challenge.
Consider the problem clarity provided and any previous analyses.

Produce a complete Beautiful Question analysis with:
1. WHY questions that challenge assumptions
2. WHAT IF questions that imagine possibilities
3. HOW questions that create action paths
4. THE single most beautiful question

Be specific to this challenge. Use the What/Who/Success context.
"""

        try:
            response = await self._agent.arun(prompt)
            output = response.content if hasattr(response, 'content') else str(response)

            # Extract key findings (simplified - could use structured output)
            key_findings = [
                "Applied Why → What If → How framework",
                "Generated assumption-challenging questions",
                "Identified possibility space",
                "Created actionable HOW questions",
            ]

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="beautiful-question",
                to_agent=context.return_to,
                success=True,
                output=output,
                key_findings=key_findings,
                recommendations=[
                    "Explore the Beautiful Question with CSIO analysis",
                    "Map domains and subdomains for the opportunity",
                    "Research market validation for top WHAT IF",
                ],
                confidence=0.75,
                suggested_next_agents=["csio", "domain-analysis"],
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="beautiful-question",
                to_agent=context.return_to,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def create_handoff_context(
        self,
        challenge: str,
        problem_what: str = "",
        problem_who: str = "",
        problem_success: str = "",
        previous_output: str = "",
    ) -> HandoffContext:
        """
        Create a handoff context for this agent.

        Useful when chaining from another agent.
        """
        from ...handoff.context import ProblemClarity, ConversationSummary
        import uuid

        clarity = ProblemClarity(
            what=problem_what or challenge,
            who=problem_who,
            success=problem_success,
            what_clarity=0.7 if problem_what else 0.5,
            who_clarity=0.7 if problem_who else 0.3,
            success_clarity=0.7 if problem_success else 0.3,
        )

        return HandoffContext(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=clarity,
            task_description=f"Apply Beautiful Question analysis to: {challenge}",
            expected_output="Why/What If/How analysis with single Beautiful Question",
            from_agent="orchestrator",
            to_agent="beautiful-question",
            return_to="orchestrator",
            handoff_type=HandoffType.DELEGATE,
        )
