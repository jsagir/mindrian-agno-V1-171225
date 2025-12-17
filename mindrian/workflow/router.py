"""
Problem Router - Routes problems to appropriate agents/teams based on classification

Problem Types:
- Un-Defined (10+ year horizon): Exploratory, visionary
- Ill-Defined (1-5 year horizon): Strategic, directional
- Well-Defined (0-1 year horizon): Tactical, execution-focused
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ProblemType(str, Enum):
    """Problem classification based on time horizon and clarity"""
    UNDEFINED = "un-defined"      # 10+ years, exploratory
    ILL_DEFINED = "ill-defined"   # 1-5 years, strategic
    WELL_DEFINED = "well-defined"  # 0-1 year, tactical


@dataclass
class RoutingDecision:
    """Decision from the router"""
    problem_type: ProblemType
    primary_agents: List[str]
    frameworks: List[str]
    reasoning: str
    confidence: float


class ProblemRouter:
    """
    Routes problems to appropriate agents and frameworks.

    Based on problem classification:

    Un-Defined (10+ years):
    - Signal: Vague, aspirational, exploratory
    - Examples: "What will healthcare look like?", "How do we prepare for AI?"
    - Agents: Exploratory Team
    - Frameworks: Trending to Absurd, Scenario Analysis

    Ill-Defined (1-5 years):
    - Signal: Direction clear, path not
    - Examples: "How do we improve retention?", "What product should we build?"
    - Agents: Strategic Team
    - Frameworks: JTBD, Combining Ideas, Domain Breakdown

    Well-Defined (0-1 year):
    - Signal: Clear problem, needs validation/execution
    - Examples: "Should we launch this?", "How do we implement X?"
    - Agents: Execution Team
    - Frameworks: PWS Validation, Minto Pyramid, Work Plan
    """

    # Keywords that suggest problem type
    UNDEFINED_SIGNALS = [
        "future", "10 years", "will look like", "prepare for",
        "long term", "vision", "imagine", "explore possibilities",
        "emerging", "disrupt", "transform", "what if"
    ]

    ILL_DEFINED_SIGNALS = [
        "strategy", "should we", "which direction", "improve",
        "grow", "market", "customers want", "opportunity",
        "competitive", "position", "decide between", "options"
    ]

    WELL_DEFINED_SIGNALS = [
        "implement", "build", "launch", "validate", "execute",
        "plan", "timeline", "budget", "resources", "specific",
        "measure", "KPI", "deadline", "next steps"
    ]

    # Framework mappings
    FRAMEWORK_MAP = {
        ProblemType.UNDEFINED: [
            "trending-to-absurd",
            "scenario-analysis",
            "debono-hats",
        ],
        ProblemType.ILL_DEFINED: [
            "jobs-to-be-done",
            "combining-ideas",
            "domain-breakdown",
            "systems-thinking",
        ],
        ProblemType.WELL_DEFINED: [
            "pws-validation",
            "minto-pyramid",
            "work-plan",
        ],
    }

    # Agent team mappings
    AGENT_MAP = {
        ProblemType.UNDEFINED: ["larry", "mentor", "scenario-builder"],
        ProblemType.ILL_DEFINED: ["larry", "devil", "expert"],
        ProblemType.WELL_DEFINED: ["larry", "devil", "validation-agent"],
    }

    def __init__(self):
        self._classification_history: List[RoutingDecision] = []

    def classify(
        self,
        problem_description: str,
        clarity_score: float = 0.0,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Classify a problem and determine routing.

        Args:
            problem_description: Description of the problem
            clarity_score: Problem clarity from Larry (0-1)
            user_context: Additional context about the user/session

        Returns:
            RoutingDecision with type, agents, and frameworks
        """
        problem_lower = problem_description.lower()

        # Score each problem type
        scores = {
            ProblemType.UNDEFINED: self._score_signals(problem_lower, self.UNDEFINED_SIGNALS),
            ProblemType.ILL_DEFINED: self._score_signals(problem_lower, self.ILL_DEFINED_SIGNALS),
            ProblemType.WELL_DEFINED: self._score_signals(problem_lower, self.WELL_DEFINED_SIGNALS),
        }

        # Adjust based on clarity score
        if clarity_score > 0.8:
            scores[ProblemType.WELL_DEFINED] += 0.3
        elif clarity_score < 0.3:
            scores[ProblemType.UNDEFINED] += 0.2

        # Determine winner
        problem_type = max(scores, key=scores.get)
        confidence = scores[problem_type] / sum(scores.values()) if sum(scores.values()) > 0 else 0.33

        # Build decision
        decision = RoutingDecision(
            problem_type=problem_type,
            primary_agents=self.AGENT_MAP[problem_type],
            frameworks=self.FRAMEWORK_MAP[problem_type],
            reasoning=self._build_reasoning(problem_type, scores),
            confidence=confidence,
        )

        self._classification_history.append(decision)
        return decision

    def _score_signals(self, text: str, signals: List[str]) -> float:
        """Score text against signal keywords"""
        score = 0.0
        for signal in signals:
            if signal in text:
                score += 1.0
        return score

    def _build_reasoning(
        self,
        problem_type: ProblemType,
        scores: Dict[ProblemType, float],
    ) -> str:
        """Build reasoning explanation for classification"""
        reasons = {
            ProblemType.UNDEFINED: (
                "Problem appears exploratory with a long-term horizon. "
                "Signals suggest visionary or future-oriented thinking."
            ),
            ProblemType.ILL_DEFINED: (
                "Problem has directional clarity but path is unclear. "
                "Strategic analysis and market understanding needed."
            ),
            ProblemType.WELL_DEFINED: (
                "Problem is clear with specific execution focus. "
                "Validation and planning frameworks are appropriate."
            ),
        }

        return f"{reasons[problem_type]} (Confidence: {scores[problem_type]:.1f})"

    def get_frameworks_for_type(self, problem_type: ProblemType) -> List[str]:
        """Get frameworks for a problem type"""
        return self.FRAMEWORK_MAP.get(problem_type, [])

    def get_agents_for_type(self, problem_type: ProblemType) -> List[str]:
        """Get agents for a problem type"""
        return self.AGENT_MAP.get(problem_type, ["larry"])

    def suggest_next_framework(
        self,
        current_framework: str,
        problem_type: ProblemType,
    ) -> Optional[str]:
        """Suggest next framework in chain"""
        frameworks = self.FRAMEWORK_MAP.get(problem_type, [])
        if current_framework in frameworks:
            idx = frameworks.index(current_framework)
            if idx < len(frameworks) - 1:
                return frameworks[idx + 1]
        return None
