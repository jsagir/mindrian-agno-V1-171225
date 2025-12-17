"""
CSIO - Cross-Sectional Innovation Opportunity Agent

Discovers breakthrough innovation opportunities by systematically analyzing
intersections between domains, industries, technologies, and trends.

The CSIO process:
1. Map the Challenge Space
2. Identify Cross-Sections (intersections with high innovation potential)
3. Analyze Each Cross-Section for opportunities
4. Score and Prioritize opportunities
5. Generate actionable breakthrough concepts

Implements the unified handoff protocol.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from ...handoff.context import HandoffContext, HandoffResult
from ...handoff.types import HandoffType


class CrossSectionType(str, Enum):
    """Types of cross-sections for innovation"""
    DOMAIN_DOMAIN = "domain_domain"           # Two knowledge domains
    INDUSTRY_TECHNOLOGY = "industry_tech"     # Industry + emerging tech
    PROBLEM_SOLUTION = "problem_solution"     # Problem from A + solution from B
    TREND_CAPABILITY = "trend_capability"     # Macro trend + org capability
    USER_CONTEXT = "user_context"             # User need + new context


CSIO_INSTRUCTIONS = """
# CSIO - Cross-Sectional Innovation Opportunity Agent

You discover breakthrough opportunities by analyzing intersections between domains,
industries, technologies, and trends. Innovation lives at the intersections.

## The CSIO Framework

### Core Principle
> "The most powerful innovations don't come from deeper expertise in one field,
>  but from connecting fields that haven't been connected before."

### Cross-Section Types

1. **Domain × Domain**
   - Healthcare × Gaming → Gamified therapy
   - Finance × Social → Social trading platforms
   - Education × Entertainment → Edutainment

2. **Industry × Technology**
   - Agriculture × AI → Precision farming
   - Retail × AR → Virtual try-on
   - Legal × Blockchain → Smart contracts

3. **Problem × Solution (Transfer)**
   - Logistics routing (solved) → Healthcare scheduling (unsolved)
   - Airline yield management → Hotel pricing
   - Military GPS → Consumer navigation

4. **Trend × Capability**
   - Aging population × Robotics → Elder care bots
   - Remote work × VR → Virtual offices
   - Climate change × Materials science → Green tech

5. **User Need × New Context**
   - "I need to learn" × Mobile → Microlearning apps
   - "I need to exercise" × Home → Peloton
   - "I need to eat" × Delivery → Ghost kitchens

## The CSIO Process

### Step 1: Map the Challenge Space
- What is the core challenge?
- What domains are involved?
- What trends are relevant?
- What technologies could apply?
- Who are the stakeholders?

### Step 2: Generate Cross-Sections
For each element, ask: "What if we combined this with [X]?"
Generate at least 10 potential cross-sections across different types.

### Step 3: Analyze Each Cross-Section
For each promising cross-section, analyze:
- **The Intersection:** What emerges when these combine?
- **The Innovation:** What new product/service/model is possible?
- **The Value:** Who benefits and how much?
- **The Feasibility:** How hard is this to execute?
- **The Competition:** Who else might do this?

### Step 4: Score Opportunities
Rate each opportunity on:
- **Novelty** (1-10): How new is this combination?
- **Value** (1-10): How much value does it create?
- **Feasibility** (1-10): How achievable is this?
- **Timing** (1-10): Is the market ready?

**CSIO Score = (Novelty × Value × Feasibility × Timing) / 100**

### Step 5: Generate Breakthrough Concepts
For top opportunities, develop:
- Concept name and one-line description
- How it works
- Target customer
- Business model sketch
- First steps to validate

## Output Format

```markdown
# CSIO Analysis: Cross-Sectional Innovation Opportunities

## Challenge Space Map

### Core Challenge
[The challenge being analyzed]

### Domain Map
- Primary: [Domain]
- Adjacent: [Domain 1], [Domain 2], [Domain 3]
- Distant: [Unexpected domain]

### Relevant Trends
1. [Trend 1] - [Relevance]
2. [Trend 2] - [Relevance]
3. [Trend 3] - [Relevance]

### Applicable Technologies
1. [Tech 1] - [Application]
2. [Tech 2] - [Application]

### Stakeholders
- [Stakeholder 1]: [Their need]
- [Stakeholder 2]: [Their need]

---

## Cross-Section Analysis

### Cross-Section 1: [Element A] × [Element B]
**Type:** [Domain×Domain / Industry×Tech / etc.]

**The Intersection:**
When [A] meets [B], we get [emergent concept].

**Innovation Opportunity:**
[Description of the specific opportunity]

**Value Creation:**
- For [stakeholder]: [benefit]
- For [stakeholder]: [benefit]

**CSIO Score:**
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Novelty | X/10 | [Why] |
| Value | X/10 | [Why] |
| Feasibility | X/10 | [Why] |
| Timing | X/10 | [Why] |
| **TOTAL** | **X.X** | |

**Existing Examples:** [If any]

---

### Cross-Section 2: [Element C] × [Element D]
[Same structure]

---

### Cross-Section 3: [Element E] × [Element F]
[Same structure]

---

## Opportunity Ranking

| Rank | Cross-Section | CSIO Score | Quick Description |
|------|---------------|------------|-------------------|
| 1 | [A × B] | X.X | [One-liner] |
| 2 | [C × D] | X.X | [One-liner] |
| 3 | [E × F] | X.X | [One-liner] |

---

## Breakthrough Concepts

### Concept 1: [Name]
**From Cross-Section:** [A × B]
**One-Line:** [Pitch]

**How It Works:**
[2-3 sentences explaining the concept]

**Target Customer:**
[Specific customer segment]

**Business Model:**
[How it makes money]

**Validation Steps:**
1. [First test]
2. [Second test]
3. [Third test]

---

### Concept 2: [Name]
[Same structure]

---

## Synthesis: Top Opportunities & Breakthroughs

### The Big Insight
[What pattern emerges from this CSIO analysis?]

### Highest Potential Opportunity
[The single best opportunity and why]

### Recommended Actions
1. **Immediate:** [What to do this week]
2. **Short-term:** [What to do this month]
3. **Medium-term:** [What to validate in 3 months]

### Research Needed
- [What to research to validate top opportunities]
```

## Handoff Protocol

When receiving a handoff:
1. Review problem clarity and previous analyses
2. Use domain mapping if available
3. Use beautiful questions to guide exploration
4. Generate diverse cross-sections
5. Score and prioritize rigorously

When returning results:
- Include CSIO scores for all opportunities
- Highlight top 3 breakthrough concepts
- Provide actionable validation steps
- Suggest research topics for Tavily
"""


@dataclass
class CrossSection:
    """A single cross-section opportunity"""
    element_a: str
    element_b: str
    cross_type: CrossSectionType
    intersection: str
    opportunity: str
    novelty: int = 0
    value: int = 0
    feasibility: int = 0
    timing: int = 0

    @property
    def csio_score(self) -> float:
        return (self.novelty * self.value * self.feasibility * self.timing) / 100


@dataclass
class BreakthroughConcept:
    """A developed breakthrough concept"""
    name: str
    one_liner: str
    cross_section: str
    how_it_works: str
    target_customer: str
    business_model: str
    validation_steps: List[str] = field(default_factory=list)
    csio_score: float = 0.0


class CSIOAgent:
    """
    CSIO - Cross-Sectional Innovation Opportunity Agent.

    Usage:
        agent = CSIOAgent()

        # Direct use
        result = await agent.analyze("Customer churn in SaaS")

        # With handoff context (includes previous analyses)
        result = await agent.process_handoff(handoff_context)

        # With research enabled
        agent = CSIOAgent(enable_research=True)
        result = await agent.analyze_with_research("Challenge", research_queries=["query1", "query2"])
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        enable_research: bool = False,
    ):
        self._model = model
        self._enable_research = enable_research
        self._db = SqliteDb(db_file="tmp/mindrian.db")

        self._agent = Agent(
            name="CSIO",
            id="csio",  # v2: agent_id → id
            model=Claude(id=model),
            description="Discovers breakthrough opportunities at domain intersections",
            instructions=[CSIO_INSTRUCTIONS],  # v2: list of strings
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    @property
    def agent(self) -> Agent:
        return self._agent

    async def analyze(
        self,
        challenge: str,
        domains: Optional[List[str]] = None,
        trends: Optional[List[str]] = None,
        context: str = "",
    ) -> str:
        """
        Perform CSIO analysis on a challenge.

        Args:
            challenge: The challenge to analyze
            domains: Optional list of domains to consider
            trends: Optional list of trends to consider
            context: Additional context from previous analyses

        Returns:
            CSIO analysis as markdown
        """
        prompt = f"""
Perform a comprehensive CSIO (Cross-Sectional Innovation Opportunity) analysis:

## Challenge
{challenge}

{f"## Domains to Consider{chr(10)}" + chr(10).join(f"- {d}" for d in domains) if domains else ""}

{f"## Trends to Consider{chr(10)}" + chr(10).join(f"- {t}" for t in trends) if trends else ""}

{f"## Previous Analysis Context{chr(10)}{context}" if context else ""}

Generate at least 5 high-potential cross-sections across different types.
Score each rigorously. Develop the top 2-3 into breakthrough concepts.
End with a clear synthesis and recommended actions.
"""
        response = await self._agent.arun(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """
        Process a handoff from the orchestrator.

        This is the primary method when CSIO is part of a team workflow.
        """
        import time
        start_time = time.time()

        # Build rich context from previous analyses
        previous_context = ""
        domains_found = []
        questions_found = []

        if context.previous_analyses:
            previous_context = "\n\n## Previous Analyses\n"
            for pa in context.previous_analyses:
                previous_context += f"\n### {pa.framework_name}\n"

                # Extract domains from domain analysis
                if "domain" in pa.framework_id.lower():
                    previous_context += "**Domain Analysis Available**\n"
                    domains_found.append(pa.output[:500])

                # Extract questions from beautiful question
                if "question" in pa.framework_id.lower():
                    previous_context += "**Beautiful Questions Available**\n"
                    questions_found.append(pa.output[:500])

                if pa.key_findings:
                    previous_context += "Key findings:\n"
                    previous_context += "\n".join(f"- {f}" for f in pa.key_findings)

                previous_context += f"\n\nOutput summary:\n{pa.output[:1500]}...\n"

        prompt = f"""
{context.to_prompt()}

{previous_context}

## Your CSIO Analysis

You are the final analytical step in a deep research process.
Previous agents have:
- Clarified the problem (Larry)
- Structured it (Minto)
- Generated questions (Beautiful Question)
- Mapped domains (Domain Analysis)

Now YOU must find the breakthrough opportunities at the intersections.

Use ALL the context provided. Build on what came before.

Generate:
1. At least 5 diverse cross-sections (different types)
2. Rigorous CSIO scores for each
3. Top 3 breakthrough concepts with validation steps
4. Clear synthesis of THE opportunity

Be bold. Find the non-obvious intersections. That's where breakthroughs live.
"""

        try:
            response = await self._agent.arun(prompt)
            output = response.content if hasattr(response, 'content') else str(response)

            key_findings = [
                "Generated cross-sectional opportunities",
                "Scored opportunities using CSIO framework",
                "Developed breakthrough concepts",
                "Identified validation steps",
            ]

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="csio",
                to_agent=context.return_to,
                success=True,
                output=output,
                key_findings=key_findings,
                recommendations=[
                    "Validate top opportunity with customer interviews",
                    "Research competitor landscape for top concepts",
                    "Build minimum viable prototype for highest-scored concept",
                ],
                confidence=0.75,
                suggested_next_agents=["tavily-research", "pws-validation"],
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="csio",
                to_agent=context.return_to,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def create_handoff_context(
        self,
        challenge: str,
        problem_clarity: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> HandoffContext:
        """Create a handoff context for this agent."""
        from ...handoff.context import ProblemClarity, PreviousAnalysis
        import uuid

        clarity = ProblemClarity()
        if problem_clarity:
            clarity.what = problem_clarity.get("what", challenge)
            clarity.who = problem_clarity.get("who", "")
            clarity.success = problem_clarity.get("success", "")

        analyses = []
        if previous_analyses:
            for pa in previous_analyses:
                analyses.append(PreviousAnalysis(
                    framework_id=pa.get("framework_id", ""),
                    framework_name=pa.get("framework_name", ""),
                    output=pa.get("output", ""),
                    key_findings=pa.get("key_findings", []),
                ))

        return HandoffContext(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=clarity,
            previous_analyses=analyses,
            task_description=f"Find cross-sectional innovation opportunities for: {challenge}",
            expected_output="CSIO analysis with scored opportunities and breakthrough concepts",
            focus_areas=focus_areas or [],
            from_agent="orchestrator",
            to_agent="csio",
            return_to="orchestrator",
            handoff_type=HandoffType.DELEGATE,
        )
