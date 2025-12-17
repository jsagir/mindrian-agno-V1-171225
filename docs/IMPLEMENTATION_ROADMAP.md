# Mindrian Implementation Roadmap

> What to build, in what order, based on dependencies.

---

## Implementation Layers (Bottom-Up)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: UI & API                    [NOT STARTED]                         │
│  ═══════════════════                                                        │
│  FastAPI, Streamlit, WebSocket                                              │
│  DEPENDS ON: Everything below                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 4: Orchestration               [PARTIAL - Router/Orchestrator stubs] │
│  ═══════════════════════                                                    │
│  Teams, Router, Main Workflow                                               │
│  DEPENDS ON: Agents + Handoff + Intelligence                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 3: Agents                      [PARTIAL - Research agents only]      │
│  ════════════════                                                           │
│  Framework Agents, Conversational Agents                                    │
│  DEPENDS ON: Handoff + Tools + Intelligence                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 2: Handoff Protocol            [IMPLEMENTED]                         │
│  ══════════════════════════                                                 │
│  HandoffContext, HandoffResult, HandoffManager                              │
│  DEPENDS ON: Tools                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 1: Intelligence & Tools        [PARTIAL - Stubs only]                │
│  ══════════════════════════════                                             │
│  Neo4j MCP, Supabase Memory, Pinecone                                       │
│  DEPENDS ON: Nothing (foundation)                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Intelligence Layer)

**Goal:** Make the three brains actually work.

### 1.1 Wire Neo4j MCP (Priority: CRITICAL)

```
STATUS: MCP server exists, wrapper is stub
EFFORT: 2-3 hours
BLOCKS: Framework selection, insight storage, graph queries

TASKS:
├── Create actual MCP tool wrappers (not print statements)
├── Test read_neo4j_cypher via MCP
├── Test write_neo4j_cypher via MCP
├── Create framework registration function
└── Create framework selection query
```

**Files to modify:**
- `mindrian/tools/neo4j_tools.py` - Wire to actual MCP
- `mindrian/builder/agent_builder.py` - Replace print with MCP call

### 1.2 Implement Supabase Conversation Memory (Priority: HIGH)

```
STATUS: Not started
EFFORT: 4-5 hours
BLOCKS: Context retrieval, session continuity

TASKS:
├── Create Supabase tables (conversations, sessions)
├── Implement embedding generation (OpenAI or local)
├── Implement store_turn() method
├── Implement retrieve_context() with pgvector
├── Implement session management
└── Test RAG retrieval
```

**Files to create:**
- `mindrian/memory/__init__.py`
- `mindrian/memory/conversation_memory.py`
- `mindrian/memory/session_manager.py`

**Schema:**
```sql
-- Supabase tables
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id TEXT,
    created_at TIMESTAMP,
    last_active TIMESTAMP,
    problem_clarity JSONB,
    metadata JSONB
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    embedding VECTOR(1536),
    agent_id TEXT,
    created_at TIMESTAMP
);

CREATE INDEX ON conversations USING ivfflat (embedding vector_cosine_ops);
```

### 1.3 Wire Pinecone MCP (Priority: MEDIUM)

```
STATUS: MCP server exists, wrapper is stub
EFFORT: 1-2 hours
BLOCKS: PWS Brain retrieval

TASKS:
├── Wire search_records to actual MCP
├── Test PWS brain retrieval
└── Integrate with Larry's context enhancement
```

**Files to modify:**
- `mindrian/tools/pinecone_tools.py`
- `mindrian/tools/pws_brain.py`

---

## Phase 2: First Framework Agent

**Goal:** Prove the Agent Builder works end-to-end.

### 2.1 Build Minto Pyramid Agent (Priority: HIGH)

```
STATUS: SKILL.md exists in mindrian-platform
EFFORT: 2-3 hours
BLOCKS: Proof that builder works

TASKS:
├── Run Agent Builder on Minto SKILL.md
├── Verify generated code compiles
├── Test direct execution (agent.run())
├── Test handoff execution (process_handoff())
├── Register in Neo4j
└── Write integration test
```

**Files created by builder:**
- `mindrian/agents/frameworks/minto_pyramid/__init__.py`
- `mindrian/agents/frameworks/minto_pyramid/agent.py`
- `mindrian/agents/frameworks/minto_pyramid/schema.cypher`
- `mindrian/agents/frameworks/minto_pyramid/tests/test_agent.py`

### 2.2 Build PWS Validation Agent (Priority: HIGH)

```
STATUS: SKILL.md exists
EFFORT: 2-3 hours

TASKS:
├── Run Agent Builder on PWS SKILL.md
├── Add scoring logic (4 pillars)
├── Add decision output (GO/PIVOT/NO-GO)
├── Test with sample opportunities
└── Register in Neo4j
```

### 2.3 Build JTBD Agent (Priority: MEDIUM)

```
STATUS: SKILL.md exists
EFFORT: 2-3 hours

TASKS:
├── Run Agent Builder on JTBD SKILL.md
├── Add job mapping output
├── Add opportunity scoring formula
└── Register in Neo4j
```

---

## Phase 3: Teams & Routing

**Goal:** Coordinate multiple agents intelligently.

### 3.1 Implement Problem Router (Priority: HIGH)

```
STATUS: Shell exists
EFFORT: 3-4 hours
BLOCKS: Intelligent framework selection

TASKS:
├── Implement problem type classification
├── Wire to Neo4j framework selection query
├── Add confidence scoring
├── Test routing decisions
└── Add fallback logic
```

**Files to modify:**
- `mindrian/workflow/router.py`

**Routing Logic:**
```python
async def route(self, problem_clarity: ProblemClarity) -> List[str]:
    # 1. Classify problem type
    problem_type = await self._classify(problem_clarity)

    # 2. Extract keywords/triggers
    triggers = self._extract_triggers(problem_clarity.what)

    # 3. Query Neo4j for best frameworks
    frameworks = await self._query_neo4j(
        problem_type=problem_type,
        triggers=triggers,
        limit=5
    )

    # 4. Return ranked list
    return [f['id'] for f in frameworks]
```

### 3.2 Implement Clarification Team (Priority: HIGH)

```
STATUS: Not started
EFFORT: 2-3 hours
BLOCKS: Entry point coordination

TASKS:
├── Create team with Larry + Devil
├── Set coordinate mode (sequential)
├── Define success criteria (clarity >= 0.6)
├── Test team execution
└── Add exit conditions
```

**Files to create:**
- `mindrian/teams/clarification.py`

### 3.3 Implement Analysis Team (Priority: MEDIUM)

```
STATUS: Not started
EFFORT: 2-3 hours

TASKS:
├── Create team with framework agents
├── Set collaborate mode (parallel)
├── Define synthesis strategy
└── Test parallel execution
```

**Files to create:**
- `mindrian/teams/analysis.py`

---

## Phase 4: Main Workflow

**Goal:** End-to-end user experience.

### 4.1 Implement Session Manager (Priority: HIGH)

```
STATUS: Not started
EFFORT: 3-4 hours
BLOCKS: User experience

TASKS:
├── Create/resume sessions
├── Load context from Supabase
├── Track problem clarity across turns
├── Handle session timeouts
└── Store session metadata
```

**Files to create:**
- `mindrian/state/session.py`

### 4.2 Implement Main Orchestrator (Priority: HIGH)

```
STATUS: Shell exists
EFFORT: 4-5 hours
BLOCKS: Full workflow

TASKS:
├── Wire session management
├── Wire Larry as entry point
├── Wire problem router
├── Wire team dispatch
├── Wire synthesis
├── Wire memory storage
└── End-to-end test
```

**Files to modify:**
- `mindrian/workflow/orchestrator.py`

### 4.3 Implement Synthesizer Agent (Priority: MEDIUM)

```
STATUS: Not started
EFFORT: 2-3 hours

TASKS:
├── Create synthesis agent
├── Define combination strategies
├── Add conflict resolution
├── Format user-friendly output
└── Store insights
```

**Files to create:**
- `mindrian/agents/synthesis/synthesizer.py`

---

## Phase 5: API & UI

**Goal:** User-accessible interface.

### 5.1 FastAPI Backend (Priority: HIGH after Phase 4)

```
STATUS: Not started
EFFORT: 4-6 hours

TASKS:
├── Create FastAPI app
├── POST /chat endpoint
├── GET /sessions endpoint
├── WebSocket for streaming
├── Authentication (optional)
└── Error handling
```

**Files to create:**
- `api/main.py`
- `api/routes/chat.py`
- `api/routes/sessions.py`

### 5.2 Streamlit UI (Priority: MEDIUM)

```
STATUS: Not started
EFFORT: 3-4 hours

TASKS:
├── Chat interface
├── Session management
├── Framework visualization
├── Living document display
└── Debug panel (optional)
```

**Files to create:**
- `ui/streamlit_app.py`

---

## Implementation Order (Critical Path)

```
WEEK 1: Foundation
────────────────────────────────────────────────────────
Day 1-2: Wire Neo4j MCP + Framework registration
Day 3-4: Implement Supabase conversation memory
Day 5:   Wire Pinecone + Test intelligence layer

WEEK 2: Agents
────────────────────────────────────────────────────────
Day 1:   Build Minto agent with Agent Builder
Day 2:   Build PWS agent with Agent Builder
Day 3:   Build JTBD agent with Agent Builder
Day 4:   Test all agents individually
Day 5:   Register all in Neo4j + Test selection

WEEK 3: Orchestration
────────────────────────────────────────────────────────
Day 1-2: Implement Problem Router
Day 3:   Implement Clarification Team
Day 4:   Implement Analysis Team
Day 5:   Test team coordination

WEEK 4: Integration
────────────────────────────────────────────────────────
Day 1-2: Implement Session Manager
Day 3-4: Implement Main Orchestrator
Day 5:   End-to-end testing

WEEK 5: UI
────────────────────────────────────────────────────────
Day 1-2: FastAPI backend
Day 3-4: Streamlit UI
Day 5:   Integration testing + polish
```

---

## Dependency Graph

```
                              ┌─────────────┐
                              │   UI/API    │
                              │  (Week 5)   │
                              └──────┬──────┘
                                     │
                              ┌──────┴──────┐
                              │ Orchestrator│
                              │  (Week 4)   │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
             ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
             │   Router    │  │   Teams     │  │  Session    │
             │  (Week 3)   │  │  (Week 3)   │  │  Manager    │
             └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                              ┌──────┴──────┐
                              │   Agents    │
                              │  (Week 2)   │
                              └──────┬──────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
       ┌──────┴──────┐       ┌───────┴──────┐       ┌──────┴──────┐
       │   Neo4j     │       │   Supabase   │       │  Pinecone   │
       │   (Day 1)   │       │   (Day 3)    │       │   (Day 5)   │
       └─────────────┘       └──────────────┘       └─────────────┘
              │                      │                      │
              └──────────────────────┴──────────────────────┘
                                     │
                              ┌──────┴──────┐
                              │ MCP Servers │
                              │  (Exist)    │
                              └─────────────┘
```

---

## Quick Wins (Can Do Now)

| Task | Effort | Impact | Dependencies |
|------|--------|--------|--------------|
| Wire Neo4j MCP calls | 2 hrs | HIGH | None |
| Build Minto with Agent Builder | 1 hr | HIGH | Neo4j |
| Test existing research agents | 1 hr | MEDIUM | None |
| Add more framework SKILL.md | 30 min each | MEDIUM | None |
| Write architecture tests | 2 hrs | MEDIUM | None |

---

## Risk Areas

| Risk | Mitigation |
|------|------------|
| MCP tool failures | Add fallback mock modes |
| Supabase pgvector performance | Add caching layer |
| Agent Builder edge cases | More SKILL.md test cases |
| Team coordination complexity | Start with 2-agent teams |
| Token costs | Add token budgets per agent |

---

*Mindrian Implementation Roadmap v1.0*
