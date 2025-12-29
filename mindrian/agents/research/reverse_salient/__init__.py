"""
Reverse Salient Discovery Agent

Discovers breakthrough innovation opportunities by detecting reverse salients—
unexpected complementarities between research domains where structural and
semantic similarities diverge significantly.

Uses dual similarity analysis (LSA + BERT) to identify high-potential
opportunities where methods from one domain can solve problems in another.
"""

from .agent import (
    ReverseSalientAgent,
    REVERSE_SALIENT_INSTRUCTIONS,
    create_reverse_salient_agent,
)
from .tools import (
    search_research_documents,
    clean_documents,
    compute_lsa_similarity,
    compute_bert_similarity,
    detect_reverse_salients,
    generate_opportunity_report,
)

__all__ = [
    # Agent
    "ReverseSalientAgent",
    "REVERSE_SALIENT_INSTRUCTIONS",
    "create_reverse_salient_agent",
    # Tools
    "search_research_documents",
    "clean_documents",
    "compute_lsa_similarity",
    "compute_bert_similarity",
    "detect_reverse_salients",
    "generate_opportunity_report",
]
