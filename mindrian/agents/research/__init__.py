"""
Mindrian Research Agents

Deep research agents for comprehensive innovation discovery.
All agents implement the unified handoff protocol.

Agents:
    - BeautifulQuestionAgent: Generates Why/What If/How questions
    - DomainAnalysisAgent: Maps domains and intersections
    - CSIOAgent: Cross-sectional innovation opportunities
    - GeminiDeepResearchAgent: Autonomous multi-step web research (Google API)
    - ReverseSalientAgent: Cross-domain innovation via dual similarity analysis
"""

from .beautiful_question import BeautifulQuestionAgent, BEAUTIFUL_QUESTION_INSTRUCTIONS
from .domain_analysis import DomainAnalysisAgent, DOMAIN_ANALYSIS_INSTRUCTIONS
from .csio import CSIOAgent, CSIO_INSTRUCTIONS
from .gemini_deep_research import (
    GeminiDeepResearchAgent,
    DeepResearchConfig,
    deep_research,
    register_with_handoff_manager,
)
from .reverse_salient import (
    ReverseSalientAgent,
    REVERSE_SALIENT_INSTRUCTIONS,
    create_reverse_salient_agent,
)

__all__ = [
    # Beautiful Question
    "BeautifulQuestionAgent",
    "BEAUTIFUL_QUESTION_INSTRUCTIONS",
    # Domain Analysis
    "DomainAnalysisAgent",
    "DOMAIN_ANALYSIS_INSTRUCTIONS",
    # CSIO
    "CSIOAgent",
    "CSIO_INSTRUCTIONS",
    # Gemini Deep Research
    "GeminiDeepResearchAgent",
    "DeepResearchConfig",
    "deep_research",
    "register_with_handoff_manager",
    # Reverse Salient Discovery
    "ReverseSalientAgent",
    "REVERSE_SALIENT_INSTRUCTIONS",
    "create_reverse_salient_agent",
]
