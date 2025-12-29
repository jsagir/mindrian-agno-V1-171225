"""
Mindrian Prompts Package

Contains validated system prompts for all agents.

v3 = Original Larry (asks too many questions)
v4 = Action-oriented Larry (5-question limit, role switching, PWS grounding)
"""

from .larry_system_prompt import (
    get_larry_prompt,
    get_mode_instructions,
    LARRY_SYSTEM_PROMPT,
    LARRY_COMPACT_PROMPT,
    LARRY_IDENTITY,
    LARRY_BEHAVIORAL_RULES,
    LARRY_QUESTION_TECHNIQUES,
    LARRY_PROBLEM_CLASSIFICATION,
    LARRY_TOOL_TRIGGERING,
    LARRY_FRAMEWORK_CHAINS,
)

# v4 - Action-oriented prompts (RECOMMENDED)
from .larry_system_prompt_v4 import (
    get_larry_prompt_v4,
    LARRY_SYSTEM_PROMPT_V4,
    LARRY_COMPACT_PROMPT_V4,
    LARRY_IDENTITY_V4,
    LARRY_BEHAVIORAL_RULES_V4,
)

__all__ = [
    # v3 (legacy)
    "get_larry_prompt",
    "get_mode_instructions",
    "LARRY_SYSTEM_PROMPT",
    "LARRY_COMPACT_PROMPT",
    "LARRY_IDENTITY",
    "LARRY_BEHAVIORAL_RULES",
    "LARRY_QUESTION_TECHNIQUES",
    "LARRY_PROBLEM_CLASSIFICATION",
    "LARRY_TOOL_TRIGGERING",
    "LARRY_FRAMEWORK_CHAINS",
    # v4 (action-oriented)
    "get_larry_prompt_v4",
    "LARRY_SYSTEM_PROMPT_V4",
    "LARRY_COMPACT_PROMPT_V4",
    "LARRY_IDENTITY_V4",
    "LARRY_BEHAVIORAL_RULES_V4",
]
