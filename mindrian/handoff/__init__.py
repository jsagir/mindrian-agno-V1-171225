"""
Mindrian Unified Handoff System

A clear, unified method for agent handoffs in Mindrian's conversational multi-agent architecture.

## Key Concepts

### Handoff Types
1. **DELEGATE** - Larry assigns work to framework(s), expects results back
2. **TRANSFER** - Full control passes to another agent (user talks to them directly)
3. **RETURN** - Agent completes and returns control to orchestrator

### Handoff Context
Every handoff carries structured context:
- Problem clarity (What/Who/Success)
- Conversation history (relevant messages)
- Previous analyses (from other frameworks)
- Expected output format
- Return instructions

### The Flow

```
USER ─────► LARRY (Orchestrator)
              │
              │ DELEGATE (with context)
              ▼
         FRAMEWORK TEAM
         ┌─────────────────┐
         │ Agent 1 ────────┤
         │      │ context  │
         │      ▼          │
         │ Agent 2 ────────┤
         │      │ context  │
         │      ▼          │
         │ Agent 3         │
         └────────┬────────┘
                  │ RETURN (with results)
                  ▼
              LARRY
              │
              │ (synthesizes, may delegate again)
              ▼
            USER
```

## Usage

```python
from mindrian.handoff import HandoffContext, HandoffType, create_handoff

# Create handoff context
context = HandoffContext(
    problem_what="Customer churn in SaaS product",
    problem_who="B2B customers in first 90 days",
    problem_success="Reduce churn from 15% to 8%",
    conversation_summary="User wants to validate anti-churn solution",
    previous_analyses={"larry_clarity": 0.85},
)

# Larry delegates to Validation Team
handoff = create_handoff(
    type=HandoffType.DELEGATE,
    from_agent="larry",
    to_agent="validation-team",
    context=context,
    expected_output="GO/PIVOT/NO-GO recommendation",
    return_to="larry",
)
```
"""

from .context import HandoffContext, HandoffResult
from .types import HandoffType, HandoffMode
from .manager import HandoffManager, handoff_manager
from .tools import create_handoff_tool, create_return_tool

__all__ = [
    "HandoffContext",
    "HandoffResult",
    "HandoffType",
    "HandoffMode",
    "HandoffManager",
    "handoff_manager",
    "create_handoff_tool",
    "create_return_tool",
]
