"""
Domain & Subdomain Analysis Agent

Maps challenges across knowledge domains to find adjacent and cross-domain opportunities.
Identifies where innovation can transfer from one field to another.

Implements the unified handoff protocol.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from ...handoff.context import HandoffContext, HandoffResult
from ...handoff.types import HandoffType


DOMAIN_ANALYSIS_INSTRUCTIONS = """
# Domain & Subdomain Analysis Agent

You map challenges across knowledge domains to find innovation opportunities at intersections.

## Core Concept

Every challenge exists within domains. Innovation often comes from:
1. **Adjacent domains** - Nearby fields with transferable solutions
2. **Distant domains** - Unexpected fields with analogous problems
3. **Intersections** - Where two or more domains meet

## Domain Mapping Process

### Step 1: Identify Primary Domain
- What field does this challenge primarily belong to?
- What discipline would traditionally solve this?
- What expertise is typically required?

### Step 2: Map Subdomains
Break the primary domain into subdomains:
- Technical subdomains
- Application subdomains
- Stakeholder subdomains
- Process subdomains

### Step 3: Identify Adjacent Domains
Find related fields:
- What other industries face similar challenges?
- What academic disciplines study this?
- What technologies are relevant?

### Step 4: Discover Distant Analogies
Find unexpected connections:
- What completely different field has solved a similar problem?
- What nature-based solutions exist (biomimicry)?
- What historical precedents apply?

### Step 5: Map Intersections
Identify high-potential collision points:
- Where do domains overlap?
- What hybrid solutions emerge?
- Where is expertise rare but valuable?

## Output Format

```markdown
# Domain Analysis

## Challenge Summary
[Brief restatement of the challenge]

## Primary Domain
**Domain:** [Name]
**Description:** [What this domain covers]
**Traditional Approaches:** [How this domain typically solves problems]
**Limitations:** [Why traditional approaches may be insufficient]

## Subdomain Map

### Technical Subdomains
| Subdomain | Relevance | Key Concepts |
|-----------|-----------|--------------|
| [Name] | [High/Med/Low] | [Concepts] |

### Application Subdomains
| Subdomain | Relevance | Key Concepts |
|-----------|-----------|--------------|

### Stakeholder Subdomains
| Subdomain | Relevance | Key Concepts |
|-----------|-----------|--------------|

## Adjacent Domains

### Domain 1: [Name]
- **Connection to challenge:** [How it relates]
- **Transferable solutions:** [What could transfer]
- **Key players/examples:** [Who has solved similar]

### Domain 2: [Name]
[Same structure]

### Domain 3: [Name]
[Same structure]

## Distant Domain Analogies

### Analogy 1: [Domain] → [Challenge]
- **The parallel:** [What's similar]
- **The solution in that domain:** [How they solved it]
- **Transfer opportunity:** [How it could apply here]

### Analogy 2: [Domain] → [Challenge]
[Same structure]

## High-Potential Intersections

### Intersection 1: [Domain A] × [Domain B]
- **What emerges:** [The hybrid concept]
- **Why it's promising:** [The opportunity]
- **Who could do this:** [Required expertise]
- **Innovation potential:** [High/Medium/Low]

### Intersection 2: [Domain A] × [Domain C]
[Same structure]

## Domain Heat Map

```
                    RELEVANCE
                Low    Med    High
NOVELTY   High   ○      ●      ★     ← Sweet spot
          Med    ○      ○      ●
          Low    ○      ○      ○
```

Key intersections plotted:
- ★ [Intersection] - High novelty + High relevance
- ● [Intersection] - Medium-high potential
- ○ [Intersection] - Lower priority

## Recommended Focus Areas
1. **Highest potential:** [Intersection/domain]
2. **Quick wins:** [Easier intersections]
3. **Long-term exploration:** [Ambitious intersections]

## Experts/Resources to Consult
- [Domain]: [Specific experts, companies, papers]
- [Domain]: [Resources]
```

## Handoff Protocol

When receiving a handoff:
1. Extract the challenge from ProblemClarity
2. Review any Beautiful Question or Minto analysis
3. Map domains systematically
4. Return structured domain map with intersections

When returning results:
- Highlight top 3 intersections
- Include confidence in each mapping
- Suggest CSIO as next step for cross-sectional innovation
"""


@dataclass
class DomainMapping:
    """Structured domain analysis output"""
    primary_domain: str
    subdomains: Dict[str, List[str]] = field(default_factory=dict)
    adjacent_domains: List[Dict[str, str]] = field(default_factory=list)
    distant_analogies: List[Dict[str, str]] = field(default_factory=list)
    intersections: List[Dict[str, Any]] = field(default_factory=list)
    recommended_focus: List[str] = field(default_factory=list)


class DomainAnalysisAgent:
    """
    Domain & Subdomain Analysis Agent with handoff protocol.

    Usage:
        agent = DomainAnalysisAgent()

        # Direct use
        result = await agent.analyze("Customer churn in SaaS")

        # With handoff context
        result = await agent.process_handoff(handoff_context)
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
            name="Domain Analysis",
            id="domain-analysis",  # v2: agent_id → id
            model=Claude(id=model),
            description="Maps challenges across domains to find innovation intersections",
            instructions=[DOMAIN_ANALYSIS_INSTRUCTIONS],  # v2: list of strings
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    @property
    def agent(self) -> Agent:
        return self._agent

    async def analyze(self, challenge: str, context: str = "") -> str:
        """
        Analyze domains for a challenge.

        Args:
            challenge: The challenge to map
            context: Additional context (e.g., from previous analyses)

        Returns:
            Domain analysis as markdown
        """
        prompt = f"""
Perform a comprehensive domain analysis for this challenge:

## Challenge
{challenge}

{f"## Additional Context{chr(10)}{context}" if context else ""}

Map the primary domain, subdomains, adjacent domains, distant analogies,
and high-potential intersections. Be specific and actionable.
"""
        response = await self._agent.arun(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """
        Process a handoff from the orchestrator.
        """
        import time
        start_time = time.time()

        # Build context from previous analyses
        previous_context = ""
        if context.previous_analyses:
            previous_context = "\n\n## Previous Analyses\n"
            for pa in context.previous_analyses:
                previous_context += f"\n### {pa.framework_name}\n"
                if pa.key_findings:
                    previous_context += "Key findings:\n"
                    previous_context += "\n".join(f"- {f}" for f in pa.key_findings)
                previous_context += f"\n\n{pa.output[:1000]}..."  # Truncate long outputs

        prompt = f"""
{context.to_prompt()}

{previous_context}

## Your Analysis

Perform a comprehensive domain mapping for this challenge.
Use the problem clarity (What/Who/Success) to focus your analysis.
Build on any previous analyses provided.

Identify:
1. Primary domain and subdomains
2. Adjacent domains with transferable solutions
3. Distant analogies from unexpected fields
4. High-potential intersections for innovation

Be specific. Name actual domains, companies, technologies, and experts.
"""

        try:
            response = await self._agent.arun(prompt)
            output = response.content if hasattr(response, 'content') else str(response)

            key_findings = [
                "Mapped primary domain and subdomains",
                "Identified adjacent domain opportunities",
                "Found distant analogies for innovation transfer",
                "Highlighted high-potential intersections",
            ]

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="domain-analysis",
                to_agent=context.return_to,
                success=True,
                output=output,
                key_findings=key_findings,
                recommendations=[
                    "Apply CSIO process to top intersections",
                    "Research specific companies in adjacent domains",
                    "Validate distant analogies with domain experts",
                ],
                confidence=0.70,
                suggested_next_agents=["csio", "tavily-research"],
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="domain-analysis",
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
            task_description=f"Map domains and intersections for: {challenge}",
            expected_output="Domain map with subdomains, adjacent domains, and intersections",
            from_agent="orchestrator",
            to_agent="domain-analysis",
            return_to="orchestrator",
            handoff_type=HandoffType.DELEGATE,
        )
