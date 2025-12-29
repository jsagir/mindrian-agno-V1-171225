"""
Scenario Analysis Agent

Guided 8-step Scenario Analysis methodology for strategic foresight
and innovation discovery. Based on Lawrence Aronhime's PWS curriculum.

Supports three entry modes:
1. Full guided build from scratch
2. Continue from existing notes/work
3. Synthesize multiple team versions

Integrates Tavily research at every step with citation tracking.
"""

from .agent import (
    ScenarioAnalysisAgent,
    SCENARIO_ANALYSIS_INSTRUCTIONS,
    create_scenario_analysis_agent,
)

__all__ = [
    "ScenarioAnalysisAgent",
    "SCENARIO_ANALYSIS_INSTRUCTIONS",
    "create_scenario_analysis_agent",
]
