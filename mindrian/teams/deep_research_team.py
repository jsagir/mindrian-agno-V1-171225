"""
Deep Research Team

A comprehensive research workflow that:
1. Explores challenge with conversational agent (Larry)
2. Structures with Minto Pyramid (optional research via Tavily)
3. Generates Beautiful Questions
4. Maps Domains and Subdomains
5. Finds Cross-Sectional Innovation Opportunities (CSIO)
6. Consolidates into breakthrough opportunities report

This team demonstrates the full handoff protocol in action.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import os

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb
from agno.tools.tavily import TavilyTools

from ..handoff.context import HandoffContext, HandoffResult, ProblemClarity, PreviousAnalysis
from ..handoff.types import HandoffType, HandoffMode, ReturnBehavior
from ..handoff.manager import HandoffManager
from ..teams.team_registry import FrameworkTeam, TeamMember, TeamMode


# =============================================================================
# DEEP RESEARCH TEAM DEFINITION
# =============================================================================

DEEP_RESEARCH_SYNTHESIZER_PROMPT = """
You are synthesizing a comprehensive deep research analysis.

The team has produced:
1. **Larry's Clarification** - Problem clarity (What/Who/Success)
2. **Minto Pyramid** - Structured SCQA analysis
3. **Beautiful Questions** - Why/What If/How questions
4. **Domain Analysis** - Domain map and intersections
5. **CSIO Analysis** - Cross-sectional innovation opportunities

Your job is to create a **BREAKTHROUGH OPPORTUNITIES REPORT** that:

1. **Executive Summary** (1 paragraph)
   - The core opportunity in plain language
   - Why it matters now

2. **The Challenge Reframed**
   - How our understanding evolved through the analysis
   - The Beautiful Question that captures the opportunity

3. **Top 3 Breakthrough Opportunities**
   For each:
   - Name and one-liner
   - CSIO score
   - Why it's promising
   - Key risks
   - First validation step

4. **Domain Intersection Map**
   - Visual representation of where opportunities live
   - Which intersections are most promising

5. **Recommended Action Plan**
   - This week: [Immediate actions]
   - This month: [Validation activities]
   - This quarter: [Development milestones]

6. **Research Gaps**
   - What we still don't know
   - Suggested research queries

7. **Confidence Assessment**
   - Overall confidence in recommendations
   - What would increase/decrease confidence

Be concise but comprehensive. The user should be able to act on this report.
"""


@dataclass
class DeepResearchConfig:
    """Configuration for deep research workflow"""
    enable_tavily_research: bool = False
    research_queries: List[str] = field(default_factory=list)
    max_research_results: int = 5
    skip_minto: bool = False
    skip_beautiful_question: bool = False
    skip_domain_analysis: bool = False


@dataclass
class DeepResearchResult:
    """Complete result from deep research team"""
    challenge: str
    problem_clarity: ProblemClarity

    # Individual outputs
    larry_output: str = ""
    minto_output: str = ""
    beautiful_question_output: str = ""
    domain_analysis_output: str = ""
    csio_output: str = ""
    research_output: str = ""

    # Synthesis
    consolidated_report: str = ""
    breakthrough_opportunities: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    total_duration_seconds: float = 0.0
    handoff_count: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


class DeepResearchTeam:
    """
    Deep Research Team - Comprehensive innovation discovery workflow.

    The Flow:
    ```
    USER CHALLENGE
         │
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    LARRY (Exploration)                       │
    │              Conversational clarification                    │
    │              What / Who / Success                            │
    └─────────────────────────────────────────────────────────────┘
         │
         │ DELEGATE (with ProblemClarity)
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   MINTO PYRAMID                              │
    │              SCQA Structure                                  │
    │              + Optional Tavily Research                      │
    └─────────────────────────────────────────────────────────────┘
         │
         │ DELEGATE (with Minto output)
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                 BEAUTIFUL QUESTION                           │
    │              Why → What If → How                             │
    │              The Beautiful Question                          │
    └─────────────────────────────────────────────────────────────┘
         │
         │ DELEGATE (with questions)
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                 DOMAIN ANALYSIS                              │
    │              Domains / Subdomains                            │
    │              Adjacent / Distant                              │
    │              Intersections                                   │
    └─────────────────────────────────────────────────────────────┘
         │
         │ DELEGATE (with domain map)
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                      CSIO                                    │
    │              Cross-Sectional Analysis                        │
    │              CSIO Scores                                     │
    │              Breakthrough Concepts                           │
    └─────────────────────────────────────────────────────────────┘
         │
         │ RETURN (all outputs)
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   SYNTHESIZER                                │
    │              Consolidated Report                             │
    │              Top Opportunities                               │
    │              Action Plan                                     │
    └─────────────────────────────────────────────────────────────┘
         │
         ▼
    BREAKTHROUGH OPPORTUNITIES REPORT
    ```

    Usage:
        team = DeepResearchTeam()

        # Simple usage
        result = await team.run("How might we reduce customer churn in SaaS?")

        # With configuration
        config = DeepResearchConfig(
            enable_tavily_research=True,
            research_queries=["SaaS churn benchmarks", "customer retention strategies"],
        )
        result = await team.run("Challenge...", config=config)

        # With pre-clarified problem
        result = await team.run(
            "Challenge...",
            problem_clarity={
                "what": "Customer churn",
                "who": "B2B SaaS companies",
                "success": "Reduce churn from 15% to 8%",
            }
        )
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        handoff_manager: Optional[HandoffManager] = None,
    ):
        self._model = model
        self._db = SqliteDb(db_file="tmp/mindrian.db")

        # Use provided manager or create new one
        self._handoff_manager = handoff_manager or HandoffManager(model=model)

        # Create all team member agents
        self._create_agents()

        # Register agents with handoff manager
        self._register_agents()

    def _create_agents(self):
        """Create all team member agents"""

        # Larry - Exploration/Clarification
        self._larry = Agent(
            name="Larry",
            id="larry-explorer",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Explores and clarifies challenges through conversation",
            instructions=["""
# Larry: Deep Research Explorer

You are exploring a challenge to understand it deeply before analysis.

## Your Job
Ask probing questions to understand:
1. **What** is the real problem? (Not the symptom, the root)
2. **Who** has this problem? (Specific, not "everyone")
3. **Success** - What does solving it look like? (Measurable)

## Rules
- Short responses (under 100 words)
- One question at a time
- Challenge assumptions
- Don't give solutions yet

## When Ready
When you understand What/Who/Success clearly, summarize:
"Here's what I understand: The problem is [X], affecting [Y], and success means [Z]."
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Minto Pyramid
        self._minto = Agent(
            name="Minto Pyramid",
            id="minto-pyramid",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Structures thinking using SCQA framework",
            instructions=["""
# Minto Pyramid Agent

Structure the challenge using SCQA:

## Situation
What's the current state? (Facts everyone agrees on)

## Complication
What changed? Why is action needed? (The tension)

## Question
What must we answer? (The core question)

## Answer
What's the recommendation? (With supporting arguments)

Produce a complete SCQA analysis. Be specific to this challenge.
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Beautiful Question
        self._beautiful_question = Agent(
            name="Beautiful Question",
            id="beautiful-question",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Generates powerful questions using Why/What If/How",
            instructions=["""
# Beautiful Question Agent

Transform this challenge into powerful questions.

## The Framework

### WHY Questions
Challenge the status quo:
- Why does this exist?
- Why hasn't it been solved?

### WHAT IF Questions
Imagine possibilities:
- What if we approached this differently?
- What if constraints didn't exist?

### HOW Questions
Create action:
- How might we actually do this?
- How would we test it?

## Your Output
1. Key WHY questions (3-5)
2. Key WHAT IF questions (3-5)
3. Key HOW questions (3-5)
4. **THE Beautiful Question** - The single most powerful question
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Domain Analysis
        self._domain_analysis = Agent(
            name="Domain Analysis",
            id="domain-analysis",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Maps domains and finds intersections",
            instructions=["""
# Domain Analysis Agent

Map this challenge across knowledge domains.

## Your Analysis

### Primary Domain
What field does this belong to?

### Subdomains
Break it down: Technical, Application, Stakeholder, Process

### Adjacent Domains
What nearby fields have relevant solutions?

### Distant Analogies
What unexpected fields have solved similar problems?

### High-Potential Intersections
Where do domains collide with innovation potential?

Be specific. Name actual domains, companies, technologies.
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # CSIO
        self._csio = Agent(
            name="CSIO",
            id="csio",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Finds cross-sectional innovation opportunities",
            instructions=["""
# CSIO - Cross-Sectional Innovation Agent

Find breakthrough opportunities at intersections.

## Cross-Section Types
1. Domain × Domain
2. Industry × Technology
3. Problem × Solution (transfer)
4. Trend × Capability
5. User Need × New Context

## Your Analysis

For each cross-section:
1. What emerges at the intersection?
2. What innovation is possible?
3. Score: Novelty, Value, Feasibility, Timing (1-10 each)
4. CSIO Score = (N × V × F × T) / 100

Generate 5+ cross-sections. Develop top 3 into breakthrough concepts.

## Breakthrough Concept Format
- Name
- One-liner
- How it works
- Target customer
- Validation steps
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Synthesizer
        self._synthesizer = Agent(
            name="Research Synthesizer",
            id="research-synthesizer",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Synthesizes research into actionable report",
            instructions=[DEEP_RESEARCH_SYNTHESIZER_PROMPT],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Tavily Researcher - Optional web research
        self._tavily_researcher = Agent(
            name="Tavily Researcher",
            id="tavily-researcher",  # v2: agent_id → id
            model=Claude(id=self._model),
            description="Conducts web research using Tavily for real-time information",
            instructions=["""
# Tavily Web Researcher

You conduct targeted web research to validate and enrich analysis.

## Your Job
Use Tavily search to find:
1. **Market data** - Size, trends, competitors
2. **Case studies** - Who has done similar things?
3. **Expert opinions** - What do thought leaders say?
4. **Recent news** - What's happening now?
5. **Statistics** - Data to support or challenge hypotheses

## Research Quality
- Prioritize recent sources (last 2 years)
- Cross-reference multiple sources
- Note credibility of sources
- Highlight contradictions

## Output Format
```markdown
# Research Findings

## Query: [What was searched]

## Key Findings
1. [Finding with source]
2. [Finding with source]

## Market Data
- [Relevant statistics]

## Relevant Companies/Examples
- [Company/Example with what they're doing]

## Expert Perspectives
- [Quote/perspective from credible source]

## Confidence Notes
- [What's well-supported vs. needs more research]
```
"""],
            tools=[TavilyTools()],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    def _register_agents(self):
        """Register agents with handoff manager"""
        self._handoff_manager.register_agent("larry-explorer", self._larry)
        self._handoff_manager.register_agent("minto-pyramid", self._minto)
        self._handoff_manager.register_agent("beautiful-question", self._beautiful_question)
        self._handoff_manager.register_agent("domain-analysis", self._domain_analysis)
        self._handoff_manager.register_agent("csio", self._csio)
        self._handoff_manager.register_agent("research-synthesizer", self._synthesizer)
        self._handoff_manager.register_agent("tavily-researcher", self._tavily_researcher)

    async def run(
        self,
        challenge: str,
        config: Optional[DeepResearchConfig] = None,
        problem_clarity: Optional[Dict[str, Any]] = None,
    ) -> DeepResearchResult:
        """
        Run the complete deep research workflow.

        Args:
            challenge: The challenge to research
            config: Optional configuration
            problem_clarity: Optional pre-clarified problem (skips Larry)

        Returns:
            DeepResearchResult with all outputs and consolidated report
        """
        import time
        start_time = time.time()

        config = config or DeepResearchConfig()
        result = DeepResearchResult(challenge=challenge, problem_clarity=ProblemClarity())
        handoff_count = 0

        # Accumulated analyses for context passing
        previous_analyses: List[PreviousAnalysis] = []

        try:
            # =================================================================
            # STEP 1: Larry Exploration (or use provided clarity)
            # =================================================================
            if problem_clarity:
                # Use provided clarity
                result.problem_clarity = ProblemClarity(
                    what=problem_clarity.get("what", challenge),
                    who=problem_clarity.get("who", ""),
                    success=problem_clarity.get("success", ""),
                    what_clarity=0.8,
                    who_clarity=0.8 if problem_clarity.get("who") else 0.3,
                    success_clarity=0.8 if problem_clarity.get("success") else 0.3,
                )
                result.larry_output = f"Problem pre-clarified:\n- What: {result.problem_clarity.what}\n- Who: {result.problem_clarity.who}\n- Success: {result.problem_clarity.success}"
            else:
                # Run Larry exploration
                larry_context = self._create_handoff_context(
                    task=f"Explore and clarify this challenge: {challenge}",
                    to_agent="larry-explorer",
                    problem_clarity=ProblemClarity(what=challenge),
                )
                larry_result = await self._handoff_manager.execute(larry_context)
                handoff_count += 1

                if larry_result.success:
                    result.larry_output = larry_result.output
                    result.problem_clarity = ProblemClarity(
                        what=challenge,
                        what_clarity=0.7,
                    )
                    previous_analyses.append(larry_result.to_analysis())
                else:
                    result.errors.append(f"Larry: {larry_result.error}")

            # =================================================================
            # STEP 2: Minto Pyramid (SCQA Structure)
            # =================================================================
            if not config.skip_minto:
                minto_context = self._create_handoff_context(
                    task="Structure this challenge using SCQA (Situation, Complication, Question, Answer)",
                    to_agent="minto-pyramid",
                    problem_clarity=result.problem_clarity,
                    previous_analyses=previous_analyses,
                )
                minto_result = await self._handoff_manager.execute(minto_context)
                handoff_count += 1

                if minto_result.success:
                    result.minto_output = minto_result.output
                    previous_analyses.append(minto_result.to_analysis())
                else:
                    result.errors.append(f"Minto: {minto_result.error}")

            # =================================================================
            # STEP 2.5: Tavily Research (Optional)
            # =================================================================
            if config.enable_tavily_research:
                # Generate research queries if not provided
                queries = config.research_queries
                if not queries:
                    # Auto-generate queries from problem clarity
                    queries = [
                        f"{result.problem_clarity.what} market trends",
                        f"{result.problem_clarity.what} case studies",
                        f"{result.problem_clarity.what} statistics data",
                    ]

                research_results = []
                for query in queries[:config.max_research_results]:
                    research_prompt = f"""
Research the following topic to gather real-world data and insights:

**Query:** {query}

**Context:**
{result.problem_clarity.to_prompt() if hasattr(result.problem_clarity, 'to_prompt') else f"Problem: {result.problem_clarity.what}"}

Search for relevant market data, case studies, competitor information, and expert perspectives.
Provide well-sourced findings with confidence notes.
"""
                    try:
                        response = await self._tavily_researcher.arun(research_prompt)
                        research_output = response.content if hasattr(response, 'content') else str(response)
                        research_results.append(f"### Research: {query}\n\n{research_output}")
                        handoff_count += 1
                    except Exception as e:
                        result.errors.append(f"Tavily Research ({query}): {str(e)}")

                if research_results:
                    result.research_output = "\n\n---\n\n".join(research_results)
                    previous_analyses.append(PreviousAnalysis(
                        framework_id="tavily-research",
                        framework_name="Web Research",
                        output=result.research_output[:2000],  # Truncate for context
                        key_findings=["Gathered real-world market data", "Found relevant case studies"],
                    ))

            # =================================================================
            # STEP 3: Beautiful Question
            # =================================================================
            if not config.skip_beautiful_question:
                bq_context = self._create_handoff_context(
                    task="Generate powerful questions using Why → What If → How framework",
                    to_agent="beautiful-question",
                    problem_clarity=result.problem_clarity,
                    previous_analyses=previous_analyses,
                )
                bq_result = await self._handoff_manager.execute(bq_context)
                handoff_count += 1

                if bq_result.success:
                    result.beautiful_question_output = bq_result.output
                    previous_analyses.append(bq_result.to_analysis())
                else:
                    result.errors.append(f"Beautiful Question: {bq_result.error}")

            # =================================================================
            # STEP 4: Domain Analysis
            # =================================================================
            if not config.skip_domain_analysis:
                domain_context = self._create_handoff_context(
                    task="Map domains, subdomains, and find high-potential intersections",
                    to_agent="domain-analysis",
                    problem_clarity=result.problem_clarity,
                    previous_analyses=previous_analyses,
                )
                domain_result = await self._handoff_manager.execute(domain_context)
                handoff_count += 1

                if domain_result.success:
                    result.domain_analysis_output = domain_result.output
                    previous_analyses.append(domain_result.to_analysis())
                else:
                    result.errors.append(f"Domain Analysis: {domain_result.error}")

            # =================================================================
            # STEP 5: CSIO Analysis
            # =================================================================
            csio_context = self._create_handoff_context(
                task="Find cross-sectional innovation opportunities and breakthrough concepts",
                to_agent="csio",
                problem_clarity=result.problem_clarity,
                previous_analyses=previous_analyses,
            )
            csio_result = await self._handoff_manager.execute(csio_context)
            handoff_count += 1

            if csio_result.success:
                result.csio_output = csio_result.output
                previous_analyses.append(csio_result.to_analysis())
            else:
                result.errors.append(f"CSIO: {csio_result.error}")

            # =================================================================
            # STEP 6: Synthesis - Consolidated Report
            # =================================================================
            research_section = ""
            if result.research_output:
                research_section = f"""
### Web Research (Tavily)
{result.research_output}
"""

            synthesis_prompt = f"""
# Deep Research Synthesis Request

## Original Challenge
{challenge}

## Problem Clarity
{result.problem_clarity.to_prompt()}

## All Analyses

### Larry's Exploration
{result.larry_output}

### Minto Pyramid (SCQA)
{result.minto_output}
{research_section}
### Beautiful Questions
{result.beautiful_question_output}

### Domain Analysis
{result.domain_analysis_output}

### CSIO Analysis
{result.csio_output}

---

## Your Task

Create a **BREAKTHROUGH OPPORTUNITIES REPORT** that synthesizes all of this
into actionable recommendations. Follow the format in your instructions.

Focus on:
1. Top 3 breakthrough opportunities with CSIO scores
2. Clear action plan (this week / this month / this quarter)
3. What we still need to research
4. {"Incorporate the web research findings to validate opportunities" if result.research_output else "Note: No web research was conducted - consider enabling for validation"}
"""

            synthesis_context = HandoffContext(
                handoff_id="synthesis",
                problem_clarity=result.problem_clarity,
                task_description="Synthesize all research into breakthrough opportunities report",
                from_agent="deep-research-team",
                to_agent="research-synthesizer",
                return_to="deep-research-team",
            )

            # Direct call for synthesis
            response = await self._synthesizer.arun(synthesis_prompt)
            result.consolidated_report = response.content if hasattr(response, 'content') else str(response)
            handoff_count += 1

            # =================================================================
            # Finalize
            # =================================================================
            result.handoff_count = handoff_count
            result.total_duration_seconds = time.time() - start_time
            result.success = len(result.errors) == 0

        except Exception as e:
            result.errors.append(f"Team error: {str(e)}")
            result.success = False
            result.total_duration_seconds = time.time() - start_time

        return result

    def _create_handoff_context(
        self,
        task: str,
        to_agent: str,
        problem_clarity: ProblemClarity,
        previous_analyses: Optional[List[PreviousAnalysis]] = None,
    ) -> HandoffContext:
        """Create a handoff context for the workflow"""
        import uuid

        return HandoffContext(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=problem_clarity,
            previous_analyses=previous_analyses or [],
            task_description=task,
            from_agent="deep-research-team",
            to_agent=to_agent,
            return_to="deep-research-team",
            handoff_type=HandoffType.DELEGATE,
        )

    def get_team_definition(self) -> FrameworkTeam:
        """Get the team as a FrameworkTeam for registry"""
        return FrameworkTeam(
            team_id="deep-research-team",
            name="Deep Research Team",
            description="Comprehensive innovation discovery through multi-step analysis",
            purpose="Deep research and breakthrough opportunity discovery",
            mode=TeamMode.PIPELINE,
            suited_for=["research", "innovation", "exploration", "breakthrough", "deep-dive"],
            tags=["research", "innovation", "csio", "comprehensive"],
            synthesizer_prompt=DEEP_RESEARCH_SYNTHESIZER_PROMPT,
            members=[
                TeamMember(
                    agent_id="larry-explorer",
                    name="Larry Explorer",
                    role="Explores and clarifies challenges",
                    instructions="",
                ),
                TeamMember(
                    agent_id="minto-pyramid",
                    name="Minto Pyramid",
                    role="Structures thinking with SCQA",
                    instructions="",
                    receives_from=["larry-explorer"],
                ),
                TeamMember(
                    agent_id="beautiful-question",
                    name="Beautiful Question",
                    role="Generates Why/What If/How questions",
                    instructions="",
                    receives_from=["minto-pyramid"],
                ),
                TeamMember(
                    agent_id="domain-analysis",
                    name="Domain Analysis",
                    role="Maps domains and intersections",
                    instructions="",
                    receives_from=["beautiful-question"],
                ),
                TeamMember(
                    agent_id="csio",
                    name="CSIO",
                    role="Finds cross-sectional opportunities",
                    instructions="",
                    receives_from=["domain-analysis"],
                ),
            ],
        )
