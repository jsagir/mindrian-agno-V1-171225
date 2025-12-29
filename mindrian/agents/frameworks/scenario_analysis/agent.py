"""
Scenario Analysis Agent

Agno agent for guided 8-step Scenario Analysis methodology.
Based on Lawrence Aronhime's PWS curriculum.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from agno.agent import Agent
from agno.models.anthropic import Claude


class ScenarioStep(Enum):
    """The 8 steps of scenario analysis"""
    SELECT_DOMAIN = 1
    STEEP_ANALYSIS = 2
    CRITICAL_UNCERTAINTIES = 3
    SELECT_AXES = 4
    BUILD_NARRATIVES = 5
    GAP_ANALYSIS = 6
    CROSS_SCENARIO_PATTERNS = 7
    FRAME_PROBLEMS = 8


SCENARIO_ANALYSIS_INSTRUCTIONS = """
# Scenario Analysis Agent - MINDRIAN FOR TEAMS

You guide users through the 8-step Scenario Analysis methodology for strategic
foresight and innovation discovery. Your goal is to help users discover
"problems that exist in plausible futures that nobody is working on today."

## Core Methodology

Based on Lawrence Aronhime's PWS curriculum (Week 2: Undefined Problems).

### The 8 Steps

| Step | Name | Research | Key Output |
|------|------|----------|------------|
| 1 | Select Domain | Yes | Scope, horizon, boundaries |
| 2 | STEEP Analysis | Yes (5x) | 20-30 driving forces |
| 3 | Critical Uncertainties | No | 5-10 uncertainties (PARTS test) |
| 4 | Select Two Axes | No | 2 axes, independence verified |
| 5 | Build Narratives | Yes | 4 detailed scenarios (300-500 words each) |
| 6 | Gap Analysis | Yes | 5-10 gaps per scenario |
| 7 | Cross-Scenario Patterns | No | Robustness matrix, tiered opportunities |
| 8 | Frame Problems | No | 3-5 PWS statements |

## Your Behavior

### At Each Step:
1. Explain the objective briefly
2. Do the work with the user
3. Offer research where marked
4. Present a CHECKPOINT with clear approval options
5. WAIT for explicit approval before proceeding

### Checkpoint Format:
```
CHECKPOINT [N]: [Step Name]

[Summary of completed work]

Options:
[ ] Approve and continue
[ ] Adjust something
[ ] Research more
```

### Research Integration:
- Before searching: "Would you like me to research {topic}?"
- After search: Present findings with [Source: {title}] citations
- NEVER proceed past checkpoint without approval

## Key Frameworks

### STEEP Analysis (Step 2)
- **S**ocial: Demographics, cultural shifts, values
- **T**echnological: Emerging tech, digital transformation
- **E**conomic: Market dynamics, business models
- **E**nvironmental: Sustainability, climate, resources
- **P**olitical: Regulations, policies, geopolitics

### PARTS Test (Step 3)
- **P**lausible: Could resolve different ways?
- **A**ctionable: Reveals something we can respond to?
- **R**elevant: Matters to our domain?
- **T**ransformative: Creates meaningfully different futures?
- **S**ystematic: Connects logically to other elements?

### Axis Independence Test (Step 4)
All 4 combinations must be plausible:
- High X + High Y → Plausible?
- High X + Low Y → Plausible?
- Low X + High Y → Plausible?
- Low X + Low Y → Plausible?

### Gap-Finding Questions (Step 6)
For each scenario, ask:
- What's MISSING?
- What FAILS?
- What's FRUSTRATING?
- What's EXPENSIVE?
- What's INEQUITABLE?
- What's UNSUSTAINABLE?
- What TRANSITIONS are hard?

### Robustness Tiers (Step 7)
- Tier 1 (4/4): Very Robust - Invest heavily
- Tier 2 (3/4): Robust - Strong investment
- Tier 3 (2/4): Conditional - Monitor indicators
- Tier 4 (1/4): Scenario-specific - Define triggers

### PWS Statement Format (Step 8)
[Population] needs [capability] in order to [benefit],
but current approaches fail because [root cause].
This matters because [significance].

## Quality Gates

### STEEP Analysis:
- Minimum 20 forces
- At least 3 per category
- Mix of obvious and non-obvious

### Critical Uncertainties:
- 5-10 uncertainties
- All pass PARTS test
- Framed as spectrums

### Scenarios:
- 300-500 words each
- All meaningfully different
- At least one makes you uncomfortable
- Include concrete details (prices, policies, daily life)

### Cross-Scenario:
- Formal robustness matrix
- Tier classification
- Leading indicators for Tier 3-4

### Final Output:
- 3-5 problem statements
- PWS format
- Strategic recommendations

## Common Mistakes to Catch

1. **Treating scenarios as predictions** - All 4 are equally plausible
2. **Scenarios too similar** - Push to extremes
3. **Correlated axes** - Test independence
4. **Vague scenarios** - Add concrete details
5. **Ignoring cross-scenario patterns** - Always do robustness matrix
6. **Stopping at scenarios** - Mining for problems is 50% of the work

## Global Actions (Available Anytime)

When user says:
- "Research this" or asks factual question → Tavily search with citations
- "Library guide" → Suggest databases, search terms, experts
- "Synthesize" or "Where are we" → Progress summary

## Output Templates

### Executive Summary (1 page):
- Domain and scope
- Key uncertainties
- Four scenario summaries
- Top 3 opportunities
- Recommended next steps

### Full Report (10-15 pages):
- All 8 steps documented
- Research citations
- Visual 2x2 matrix
- Robustness analysis
- Problem statements

## Entry Triggers

Respond to:
- "I have a scenario analysis to do"
- "Help me build scenarios for..."
- "Start a new scenario analysis"
- "STEEP analysis for..."
- "2x2 scenario matrix"
- "Future of [domain]"

## Remember

- Scenarios are TOOLS, not predictions
- The goal is discovering PROBLEMS, not building scenarios
- Robust opportunities (Tier 1-2) are most valuable
- Always complete through Step 8 (problem framing)
- Research enriches but doesn't replace judgment
"""


@dataclass
class ScenarioAnalysisState:
    """State for a scenario analysis session"""
    current_step: ScenarioStep = ScenarioStep.SELECT_DOMAIN
    domain: Optional[str] = None
    time_horizon: Optional[str] = None

    # Step 2: STEEP
    driving_forces: Dict[str, List[str]] = field(default_factory=dict)

    # Step 3: Uncertainties
    critical_uncertainties: List[Dict[str, Any]] = field(default_factory=list)

    # Step 4: Axes
    axis_1: Optional[Dict[str, str]] = None
    axis_2: Optional[Dict[str, str]] = None

    # Step 5: Scenarios
    scenarios: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Step 6: Gaps
    gaps_per_scenario: Dict[str, List[str]] = field(default_factory=dict)

    # Step 7: Patterns
    robustness_matrix: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    tiered_opportunities: Dict[str, List[str]] = field(default_factory=dict)

    # Step 8: Problems
    problem_statements: List[str] = field(default_factory=list)

    # Research
    research_citations: List[Dict[str, str]] = field(default_factory=list)

    def get_completion_status(self) -> Dict[str, bool]:
        """Get completion status for each step"""
        return {
            "step_1_domain": self.domain is not None,
            "step_2_steep": len(self.driving_forces) >= 5 and sum(len(v) for v in self.driving_forces.values()) >= 20,
            "step_3_uncertainties": len(self.critical_uncertainties) >= 5,
            "step_4_axes": self.axis_1 is not None and self.axis_2 is not None,
            "step_5_scenarios": len(self.scenarios) == 4,
            "step_6_gaps": len(self.gaps_per_scenario) == 4,
            "step_7_patterns": len(self.tiered_opportunities) > 0,
            "step_8_problems": len(self.problem_statements) >= 3,
        }


class ScenarioAnalysisAgent:
    """
    Agent for guided 8-step Scenario Analysis.

    Integrates Tavily research at every step with citation tracking.
    Produces presentation-ready outputs.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        tavily_tool: Optional[Callable] = None,
    ):
        self.model_id = model
        self.tavily_tool = tavily_tool
        self._agent: Optional[Agent] = None
        self.state = ScenarioAnalysisState()

    def _build_tools(self) -> List[Callable]:
        """Build tool list for the agent"""
        tools = []

        def get_progress() -> Dict[str, Any]:
            """Get current progress through the 8 steps."""
            status = self.state.get_completion_status()
            return {
                "current_step": self.state.current_step.name,
                "domain": self.state.domain,
                "time_horizon": self.state.time_horizon,
                "completion": status,
                "driving_forces_count": sum(len(v) for v in self.state.driving_forces.values()),
                "uncertainties_count": len(self.state.critical_uncertainties),
                "scenarios_count": len(self.state.scenarios),
                "gaps_count": sum(len(v) for v in self.state.gaps_per_scenario.values()),
                "problem_statements_count": len(self.state.problem_statements),
            }

        def set_domain(domain: str, time_horizon: str) -> Dict[str, Any]:
            """Set the domain and time horizon for analysis."""
            self.state.domain = domain
            self.state.time_horizon = time_horizon
            self.state.current_step = ScenarioStep.STEEP_ANALYSIS
            return {
                "status": "domain_set",
                "domain": domain,
                "time_horizon": time_horizon,
                "next_step": "STEEP Analysis",
            }

        def add_driving_force(category: str, force: str, evidence: str = "") -> Dict[str, Any]:
            """Add a driving force to STEEP analysis."""
            if category not in self.state.driving_forces:
                self.state.driving_forces[category] = []
            self.state.driving_forces[category].append({
                "force": force,
                "evidence": evidence,
            })
            return {
                "status": "force_added",
                "category": category,
                "total_in_category": len(self.state.driving_forces[category]),
                "total_overall": sum(len(v) for v in self.state.driving_forces.values()),
            }

        def add_uncertainty(name: str, extreme_a: str, extreme_b: str) -> Dict[str, Any]:
            """Add a critical uncertainty with its spectrum."""
            self.state.critical_uncertainties.append({
                "name": name,
                "extreme_a": extreme_a,
                "extreme_b": extreme_b,
            })
            return {
                "status": "uncertainty_added",
                "total": len(self.state.critical_uncertainties),
            }

        def set_axes(
            axis_1_name: str, axis_1_left: str, axis_1_right: str,
            axis_2_name: str, axis_2_bottom: str, axis_2_top: str,
        ) -> Dict[str, Any]:
            """Set the two axes for the 2x2 matrix."""
            self.state.axis_1 = {
                "name": axis_1_name,
                "left": axis_1_left,
                "right": axis_1_right,
            }
            self.state.axis_2 = {
                "name": axis_2_name,
                "bottom": axis_2_bottom,
                "top": axis_2_top,
            }
            self.state.current_step = ScenarioStep.BUILD_NARRATIVES
            return {
                "status": "axes_set",
                "axis_1": self.state.axis_1,
                "axis_2": self.state.axis_2,
                "quadrants": {
                    "A": f"{axis_1_right} + {axis_2_top}",
                    "B": f"{axis_1_right} + {axis_2_bottom}",
                    "C": f"{axis_1_left} + {axis_2_top}",
                    "D": f"{axis_1_left} + {axis_2_bottom}",
                },
            }

        def add_scenario(
            quadrant: str,
            name: str,
            narrative: str,
            characteristics: List[str],
        ) -> Dict[str, Any]:
            """Add a scenario narrative."""
            self.state.scenarios[quadrant] = {
                "name": name,
                "narrative": narrative,
                "characteristics": characteristics,
            }
            return {
                "status": "scenario_added",
                "quadrant": quadrant,
                "name": name,
                "total_scenarios": len(self.state.scenarios),
            }

        def add_gap(scenario: str, gap: str, severity: str = "medium") -> Dict[str, Any]:
            """Add a gap identified in a scenario."""
            if scenario not in self.state.gaps_per_scenario:
                self.state.gaps_per_scenario[scenario] = []
            self.state.gaps_per_scenario[scenario].append({
                "gap": gap,
                "severity": severity,
            })
            return {
                "status": "gap_added",
                "scenario": scenario,
                "total_in_scenario": len(self.state.gaps_per_scenario[scenario]),
            }

        def add_problem_statement(statement: str, robustness_tier: int) -> Dict[str, Any]:
            """Add a framed PWS problem statement."""
            self.state.problem_statements.append({
                "statement": statement,
                "tier": robustness_tier,
            })
            return {
                "status": "problem_added",
                "total": len(self.state.problem_statements),
            }

        tools.extend([
            get_progress,
            set_domain,
            add_driving_force,
            add_uncertainty,
            set_axes,
            add_scenario,
            add_gap,
            add_problem_statement,
        ])

        if self.tavily_tool:
            tools.append(self.tavily_tool)

        return tools

    def build(self) -> Agent:
        """Build and return the Agno Agent instance"""
        if self._agent:
            return self._agent

        self._agent = Agent(
            name="ScenarioAnalysis",
            model=Claude(id=self.model_id),
            instructions=SCENARIO_ANALYSIS_INSTRUCTIONS,
            tools=self._build_tools(),
            markdown=True,
        )

        return self._agent

    async def run(self, message: str) -> str:
        """Run the agent with a message"""
        agent = self.build()
        response = await agent.arun(message)
        return response.content

    def reset(self) -> None:
        """Reset state for a new analysis"""
        self.state = ScenarioAnalysisState()
        self._agent = None


def create_scenario_analysis_agent(
    model: str = "claude-sonnet-4-20250514",
    tavily_tool: Optional[Callable] = None,
) -> ScenarioAnalysisAgent:
    """
    Factory function to create a Scenario Analysis agent.

    Args:
        model: Claude model ID
        tavily_tool: Optional Tavily search tool

    Returns:
        Configured ScenarioAnalysisAgent
    """
    return ScenarioAnalysisAgent(
        model=model,
        tavily_tool=tavily_tool,
    )
