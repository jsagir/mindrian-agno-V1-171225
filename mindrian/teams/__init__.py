"""
Mindrian Framework Teams

Pre-configured bundles of frameworks that work together on complex tasks.
Larry orchestrates which team to deploy based on problem classification.

Teams provide coordinated agent execution:
- VALIDATION_TEAM: PWS + Devil's Advocate + JTBD (validate opportunities)
- EXPLORATION_TEAM: Scenario Planning + Trending Absurd + Cynefin (explore futures)
- STRATEGY_TEAM: Minto + SWOT + Business Model Canvas (strategic planning)
- INNOVATION_TEAM: Design Thinking + Six Hats + JTBD (innovation discovery)
- DECISION_TEAM: Cynefin + Thinking in Bets + Pre-mortem (decision support)
- COMMUNICATION_TEAM: Minto + SCQA + Golden Circle (structure communication)
"""

from .team_registry import (
    FrameworkTeam,
    TeamMode,
    TeamRegistry,
    team_registry,
)
from .team_definitions import (
    VALIDATION_TEAM,
    EXPLORATION_TEAM,
    STRATEGY_TEAM,
    INNOVATION_TEAM,
    DECISION_TEAM,
    COMMUNICATION_TEAM,
    FULL_ANALYSIS_TEAM,
)

__all__ = [
    "FrameworkTeam",
    "TeamMode",
    "TeamRegistry",
    "team_registry",
    "VALIDATION_TEAM",
    "EXPLORATION_TEAM",
    "STRATEGY_TEAM",
    "INNOVATION_TEAM",
    "DECISION_TEAM",
    "COMMUNICATION_TEAM",
    "FULL_ANALYSIS_TEAM",
]
