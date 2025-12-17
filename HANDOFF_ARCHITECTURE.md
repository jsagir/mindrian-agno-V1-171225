# Mindrian Handoff Architecture

## The Core Problem

In multi-agent systems, **handoffs are everything**. When Larry (conversational orchestrator) delegates to framework agents:

1. **What context travels?** - Does the framework know What/Who/Success?
2. **How does work return?** - Does Larry get structured results he can synthesize?
3. **What happens on failure?** - Does the conversation break or gracefully recover?

Bad handoffs = confused agents = garbage output = frustrated users.

---

## Mindrian's Solution: The Unified Handoff System

### Key Insight from Research

From [LangGraph](https://docs.langchain.com/oss/python/langchain/multi-agent), [Arize comparison](https://arize.com/blog/orchestrator-worker-agents-a-practical-comparison-of-common-agent-frameworks/), and [Agno docs](https://docs.agno.com):

> "At the heart of multi-agent design is **context engineering** - deciding what information each agent sees."

The best frameworks share these patterns:
- **Structured context passing** (not just "pass full history")
- **Clear handoff types** (delegate vs. transfer vs. return)
- **Execution modes** (sequential, parallel, debate)
- **Return behavior** (synthesize vs. passthrough)

---

## The Three Handoff Types

### 1. DELEGATE (Most Common)

Larry assigns work, expects structured results back.

```
USER: "I want to validate my startup idea"

LARRY: [clarifies problem]
       "So the problem is customer churn in SaaS..."

       [DELEGATE to validation-team]
       Context: What/Who/Success + conversation summary

TEAM:  [PWS → Devil → JTBD execute]

       [RETURN to Larry]
       Results: Score, findings, recommendations

LARRY: [synthesizes]
       "The validation team scored you 72/100 (PIVOT)..."
```

### 2. TRANSFER (Rare)

Full control passes to another agent. User talks directly to them.

```
LARRY: "This requires deep technical expertise.
        I'm transferring you to the Technical Expert."

        [TRANSFER to expert]

EXPERT: [now owns the conversation]
        "Hi, I'm the Technical Expert. Tell me about your architecture..."
```

### 3. RETURN (Always After Work)

Framework completes and sends structured results back.

```
PWS_AGENT: [completes scoring]

           [RETURN to Larry]
           {
             output: "# PWS Scorecard...",
             key_findings: ["Strong problem", "Weak team"],
             recommendations: ["Hire CTO", "Validate market"],
             confidence: 0.75,
             scores: {"problem": 22, "solution": 18, "business": 20, "people": 12}
           }
```

---

## The HandoffContext: What Travels

Every handoff carries structured context. **This is the critical piece.**

```python
@dataclass
class HandoffContext:
    # === PROBLEM DEFINITION (from Larry) ===
    problem_clarity: ProblemClarity  # What/Who/Success + clarity scores

    # === CONVERSATION STATE ===
    conversation: ConversationSummary  # Key points, goals, constraints

    # === PREVIOUS WORK ===
    previous_analyses: List[PreviousAnalysis]  # What other frameworks found

    # === TASK INSTRUCTIONS ===
    task_description: str      # What to do
    expected_output: str       # What format expected
    focus_areas: List[str]     # Where to focus

    # === ROUTING ===
    from_agent: str            # Who's sending
    to_agent: str              # Who's receiving
    return_to: str             # Who gets results
```

### What Larry Sends to Frameworks

```markdown
# Handoff from larry

## Your Task
Validate this opportunity using PWS methodology.

## Problem Clarity Assessment

**What is the problem?**
Customer churn is killing our SaaS business - we lose 15% of customers in first 90 days
Clarity: 85%

**Who has this problem?**
B2B SaaS companies with <$1M ARR, self-serve onboarding
Clarity: 80%

**What does success look like?**
Reduce churn from 15% to 8%, increase trial-to-paid conversion by 20%
Clarity: 75%

## Conversation Context

**User's Goals:**
- Validate anti-churn solution before building
- Get GO/NO-GO recommendation

**Key Points Discussed:**
- User has 3 years SaaS experience
- Budget is $50K for MVP
- Timeline is 6 months

## Return Instructions
Return your results to: **larry**
Return behavior: **synthesize**
```

---

## Execution Modes

### SEQUENTIAL (Pipeline)

Each agent builds on the previous.

```
PWS → Devil → JTBD

PWS scores → Devil challenges the scores → JTBD validates customer jobs
```

**Use when:** Analysis should progressively refine.

### PARALLEL (Fan-out/Fan-in)

All agents work simultaneously, results combined.

```
Cynefin + Scenario + Trends

All three analyze → Results synthesized
```

**Use when:** Multiple independent perspectives needed.

### DEBATE (Adversarial)

Agents take opposing positions, then respond to each other.

```
Round 1: Cynefin position + Bets position + Pre-mortem position
Round 2: Each responds to others
Final: Synthesis of debate
```

**Use when:** Decision support, stress-testing.

---

## The Flow: Complete Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                       │
│                   "I want to build an AI chatbot"                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         LARRY (Clarifier)                               │
│                                                                         │
│  "Woah, step back. What problem are you trying to solve?"               │
│                                                                         │
│  [Multiple turns of clarification...]                                   │
│                                                                         │
│  Problem Clarity:                                                       │
│  - What: Customer support overwhelmed, 4hr response time                │
│  - Who: E-commerce companies with <10 support staff                     │
│  - Success: Response time under 1hr, 50% ticket deflection              │
│  - Clarity Score: 82%                                                   │
│                                                                         │
│  "Ready to validate? I'll deploy the Validation Team."                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ DELEGATE (validation-team)
                                    │ Context: ProblemClarity + ConversationSummary
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    VALIDATION TEAM (Sequential)                         │
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│  │    PWS      │      │   Devil's   │      │    JTBD     │            │
│  │  Validator  │──────│   Advocate  │──────│   Mapper    │            │
│  │             │      │             │      │             │            │
│  │ Score: 76   │      │ Challenges: │      │ Top Jobs:   │            │
│  │ PIVOT       │      │ - Market    │      │ - Faster    │            │
│  │             │      │ - Team      │      │   response  │            │
│  └─────────────┘      └─────────────┘      └─────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ RETURN (results to larry)
                                    │ {score: 76, findings: [...], recommendations: [...]}
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      LARRY (Synthesizer)                                │
│                                                                         │
│  [Receives HandoffResult from team]                                     │
│  [Synthesizes into user-friendly summary]                               │
│                                                                         │
│  "The Validation Team scored your opportunity 76/100 - that's a PIVOT.  │
│                                                                         │
│   **Strengths:**                                                        │
│   - Problem is real and painful (22/25)                                 │
│   - Clear customer need for faster response                             │
│                                                                         │
│   **Concerns:**                                                         │
│   - Market may be smaller than assumed                                  │
│   - Team needs AI/ML expertise                                          │
│                                                                         │
│   **Recommendation:**                                                   │
│   Validate market size before building. Consider technical co-founder.  │
│                                                                         │
│   Would you like me to explore this further with the Strategy Team?"    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                       │
│                       [Receives synthesized output]                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Differences from Other Frameworks

| Aspect | LangGraph | OpenAI Swarm | Agno | **Mindrian** |
|--------|-----------|--------------|------|--------------|
| Context | Full message history | Filtered history | Team state sync | **Structured ProblemClarity** |
| Handoff | Graph edges | Tool calls | Team delegation | **Typed handoffs (DELEGATE/TRANSFER/RETURN)** |
| State | Checkpointed | Session-based | Team-level | **HandoffContext dataclass** |
| Return | Command API | Agent response | Member response | **Structured HandoffResult** |
| Synthesis | Custom reducer | Manual | Leader synthesis | **Orchestrator synthesis step** |

---

## Implementation Files

```
mindrian/handoff/
├── __init__.py          # Exports + overview
├── types.py             # HandoffType, HandoffMode, ReturnBehavior
├── context.py           # HandoffContext, HandoffResult, ProblemClarity
├── manager.py           # HandoffManager - executes handoffs
└── tools.py             # Tools for Larry to use
```

---

## Usage Example

```python
from mindrian.handoff import (
    HandoffManager,
    HandoffContext,
    HandoffType,
    HandoffMode,
)

# Initialize
manager = HandoffManager()

# Register agents
manager.register_agent("larry", larry_agent)
manager.register_agent("pws-validation", pws_agent)
manager.register_agent("devil-advocate", devil_agent)

# Create delegation
context = manager.create_delegation(
    from_agent="larry",
    to_agent="pws-validation",
    task="Validate this opportunity",
    problem_clarity={
        "what": "Customer churn in SaaS",
        "who": "B2B companies <$1M ARR",
        "success": "Reduce churn from 15% to 8%",
        "what_clarity": 0.85,
        "who_clarity": 0.80,
        "success_clarity": 0.75,
    },
    expected_output="PWS Scorecard with GO/PIVOT/NO-GO",
)

# Execute
result = await manager.execute(context)

# Result contains
# - result.output: Full markdown output
# - result.key_findings: List of key findings
# - result.recommendations: List of recommendations
# - result.scores: {"problem": 22, "solution": 18, ...}
# - result.confidence: 0.75
```

---

## Design Principles

1. **Structured context > raw history** - Pass What/Who/Success, not 100 messages
2. **Typed handoffs > implicit routing** - DELEGATE/TRANSFER/RETURN are explicit
3. **Results include metadata** - Not just output, but findings, scores, confidence
4. **Orchestrator synthesizes** - Larry interprets results for user
5. **Fail gracefully** - Errors return to orchestrator, not crash

---

## Sources

- [LangGraph Multi-Agent Docs](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [Arize: Orchestrator-Worker Comparison](https://arize.com/blog/orchestrator-worker-agents-a-practical-comparison-of-common-agent-frameworks/)
- [Agno Team Delegation](https://docs.agno.com/basics/teams/delegation)
- [How Agent Handoffs Work - Towards Data Science](https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/)
