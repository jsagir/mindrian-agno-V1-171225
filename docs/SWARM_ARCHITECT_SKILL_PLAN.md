# Multi-Agent Swarm Orchestration System Architect
## Mindrian-Specific Research & Skill Plan

> This plan is customized for the Mindrian architecture. All clarification blocks have been filled with actual project specifications.

---

## CRITICAL: Agno v2 API Updates (December 2025)

Based on Swarm Architect research, the following API changes are **BREAKING**:

### 1. Team Mode Parameter DEPRECATED

```python
# ❌ OLD (v1.x) - mode parameter no longer exists
team = Team(mode="coordinate", members=[...])

# ✅ NEW (v2.0) - Boolean flags replace mode
team = Team(
    members=[...],
    respond_directly=False,           # False = synthesize (was "coordinate")
    delegate_to_all_members=False,    # False = sequential, True = parallel
)
```

| v1.x Mode | v2.0 Configuration |
|-----------|-------------------|
| `"route"` | `respond_directly=True` |
| `"coordinate"` | Default (no flags) |
| `"collaborate"` | `delegate_to_all_members=True` |

### 2. Agent ID Parameter Changed

```python
# ❌ OLD
Agent(agent_id="my-agent", ...)

# ✅ NEW
Agent(id="my-agent", ...)
```

### 3. Instructions Parameter Now List

```python
# ❌ OLD
Agent(instructions="Single string instruction")

# ✅ NEW
Agent(instructions=["First instruction", "Second instruction"])
```

### 4. Memory Architecture Changed

```python
# ✅ NEW - Separate db and memory parameters
from agno.db.sqlite import SqliteDb
from agno.memory.v2.memory import Memory

agent = Agent(
    db=SqliteDb(db_file="agent.db"),  # Session storage
    memory=Memory(db=memory_db),       # Semantic memory
    enable_user_memories=True,
    enable_agentic_memory=True,
)
```

See `docs/AGNO_V2_MIGRATION_GUIDE.md` for complete reference.

---

## Executive Summary

This skill will enable Claude to architect, review, and build multi-agent swarm systems specifically for Mindrian's cognitive orchestration platform. The skill draws from:

- **Agno Framework** - Agent, Team, and Workflow primitives
- **Mindrian Handoff Protocol** - HandoffContext/HandoffResult for structured agent communication
- **Neo4j Intelligence** - Graph-based framework selection and routing
- **Larry Supervisor Pattern** - Human-in-the-loop via conversational clarification

---

## Phase 1: Foundation Research

### 1.1 Agno Framework Deep Dive

**Research Questions:**
- What is Agno's core architecture for multi-agent orchestration?
- How does Agno handle agent state management and persistence?
- What are Agno's native patterns for agent-to-agent communication?
- How does Agno compare to other orchestration frameworks (CrewAI, AutoGen, LangGraph)?

**Sources to Investigate:**
- Agno official documentation: https://docs.agno.com
- Agno GitHub repository
- Agno example implementations and cookbooks
- Community discussions and issue threads

**Expected Outputs:**
- Agno architecture diagram
- List of core primitives (Agent, Team, Workflow, Memory)
- Documented best practices for production deployments

```
[MINDRIAN CLARIFICATION - UPDATED FOR AGNO v2.0]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Agno version in use: agno>=1.0.0 (pyproject.toml)

Existing Agno implementations in project:
  - mindrian/agents/research/beautiful_question.py
  - mindrian/agents/research/csio.py
  - mindrian/agents/research/domain_analysis.py
  - mindrian/agents/research/gemini_deep_research.py (NEW - Interactions API)
  - mindrian/teams/deep_research_team.py

Known Agno v2 API patterns (UPDATED):
  - Agent(id="agent-id", model=Claude(...), instructions=[...], db=SqliteDb(...))
  - Team(members=[...], delegate_to_all_members=True)  # parallel/collaborate
  - Team(members=[...], respond_directly=False)  # coordinate (default)
  - Workflow for deterministic pipelines

Agno v2.0 key changes:
  - agent_id → id parameter
  - instructions string → instructions list
  - mode="coordinate"|"collaborate" → delegate_to_all_members boolean
  - Memory v2: db + memory + enable_user_memories + enable_agentic_memory

Integration points with existing systems:
  - Agno Agent wraps Claude/Gemini via agno.models.anthropic.Claude/agno.models.google.Gemini
  - MCP tools via MCPTools() and MultiMCPTools() async context managers
  - Session storage via SqliteDb/PostgresDb to db parameter
  - Semantic memory via Memory from agno.memory.v2.memory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 1.2 MCP Protocol Mastery

**Research Questions:**
- What is the current MCP specification for tool definition and invocation?
- How do MCP servers handle authentication and session management?
- What are the patterns for MCP server composition (chaining multiple MCPs)?
- How do handoff protocols work between MCP-enabled agents?

**Sources to Investigate:**
- Anthropic's MCP specification documentation
- Existing MCP server implementations
- MCP SDK source code (Python)

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MCP servers currently deployed (from mcp_servers.json):
  - neo4j: read_neo4j_cypher, write_neo4j_cypher, get_neo4j_schema
  - supabase: query, insert, update, delete, rpc
  - (Pinecone REMOVED per user request)
  - render: list_services, get_service, list_deploys, get_metrics
  - n8n: create_workflow, get_workflow, validate_workflow

Custom MCP protocols implemented:
  - None yet - using standard MCP via Claude Code
  - Planning: Custom tool wrappers in mindrian/tools/

Known MCP handoff patterns in use:
  - MCP tools passed to Agno agents via tools parameter
  - Tool invocation format: mcp__{server}__{tool_name}

MCP authentication approach:
  - Environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
  - Environment variables: SUPABASE_URL, SUPABASE_SERVICE_KEY
  - Credentials NOT embedded in agents - pulled from settings

MCP server hosting infrastructure:
  - Neo4j: Cloud (neo4j+s://xxx.databases.neo4j.io) or local Docker
  - Supabase: Cloud (xxx.supabase.co)
  - All via npx @anthropic/mcp-{server}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 1.3 Neo4j Integration Patterns

**Research Questions:**
- How should agent state and conversation history be modeled in Neo4j?
- What graph patterns best represent agent relationships and capabilities?
- How can Neo4j support dynamic agent discovery and routing?
- What are optimal Cypher patterns for swarm coordination queries?

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Existing Neo4j schema elements relevant to agents:

Node Labels:
  - (:Framework {id, name, type, triggers[], problem_types[], version})
  - (:Session {id, user_id, created_at, last_active})
  - (:Insight {id, content, type, confidence, created_at})
  - (:Topic {name})
  - (:ProblemType {name})  # un-defined, ill-defined, well-defined

Relationship Types:
  - (Framework)-[:CHAINS_TO {weight}]->(Framework)
  - (Framework)-[:GOOD_FOR {confidence}]->(ProblemType)
  - (Framework)-[:USED_BY {success: bool}]->(Session)
  - (Insight)-[:DISCOVERED_BY]->(Framework)
  - (Insight)-[:RELATES_TO]->(Topic)
  - (Insight)-[:IN_SESSION]->(Session)

Query performance constraints:
  - Use indexes on id fields (Framework.id, Session.id)
  - Keep triggers[] and problem_types[] arrays small (<20 items)
  - Limit framework selection queries to top 5-10 results

Data volume expectations:
  - Frameworks: 50-100 agents
  - Sessions: Thousands
  - Insights: Tens of thousands

Framework Selection Query (CRITICAL):
```cypher
MATCH (f:Framework)
WHERE ANY(t IN $triggers WHERE t IN f.triggers)
   OR ANY(pt IN $problem_types WHERE pt IN f.problem_types)
WITH f,
     CASE WHEN ANY(t IN $triggers WHERE t IN f.triggers) THEN 0.6 ELSE 0 END +
     CASE WHEN ANY(pt IN $problem_types WHERE pt IN f.problem_types) THEN 0.4 ELSE 0 END
     AS score
ORDER BY score DESC
LIMIT 5
RETURN f.id, f.name, score
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 2: Stateful Conversation & Human-in-the-Loop Research

### 2.1 Stateful Conversational Interaction Architecture

**State Management Components:**

| Component | Mindrian Implementation | Storage |
|-----------|------------------------|---------|
| Session State | ProblemClarity + ConversationSummary | HandoffContext |
| Agent Memory | Agno built-in + SqlAgentStorage | tmp/mindrian.db |
| Shared State | HandoffContext.previous_analyses | In-memory → Supabase |
| User Profile | Session metadata | Supabase sessions table |
| Task State | HandoffResult chain | HandoffManager._history |

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current state persistence approach:
  - Session state: Agno SqlAgentStorage → tmp/mindrian.db
  - Conversation history: Supabase → conversations table
  - Problem clarity: Passed in HandoffContext (in-memory during session)
  - Insights: Neo4j (graph relationships)

Existing memory/vector store implementations:
  - Supabase pgvector for conversation embeddings (EMBEDDING_DIMENSIONS=768)
  - Google text-embedding-004 for embeddings
  - RAG retrieval via pgvector cosine similarity

Context window limits being worked with:
  - Claude: 200K tokens
  - Gemini: 1M tokens
  - Strategy: Compress via ConversationSummary, pass only relevant history

State serialization formats in use:
  - HandoffContext: Python dataclass → to_prompt() for agent consumption
  - AgentSpec: YAML file
  - Session: JSON in Supabase JSONB columns

Known state management pain points:
  - State branching not yet implemented (multiple agents same conversation)
  - No automatic state compression/summarization
  - Session resume requires full context reload from Supabase

Conversation history storage:
  - Table: conversations (id, session_id, role, content, embedding, agent_id, created_at)
  - Index: ivfflat on embedding vector for fast similarity search
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.2 Human-in-the-Loop: The "Larry" Supervisor Pattern

**CRITICAL MINDRIAN DISTINCTION:**

In Mindrian, "Larry" is NOT a human supervisor - Larry IS an AI agent (The Clarifier) who serves as the **always-on entry point** for users. The human-in-the-loop pattern works differently:

```
┌─────────────────────────────────────────────────────────────────────┐
│                 MINDRIAN HUMAN-IN-THE-LOOP PATTERN                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐                        ┌─────────────┐            │
│  │    USER     │ ◄────────────────────► │   LARRY     │            │
│  │  (Human)    │    Conversation        │ (AI Agent)  │            │
│  └─────────────┘                        └──────┬──────┘            │
│                                                │                    │
│                                    DELEGATE    │                    │
│                                    (HandoffContext)                │
│                                                │                    │
│                                                ▼                    │
│                                   ┌────────────────────┐           │
│                                   │  Framework Agents  │           │
│                                   │  (Minto, PWS, etc) │           │
│                                   └────────────────────┘           │
│                                                │                    │
│                                     RETURN     │                    │
│                                   (HandoffResult)                   │
│                                                │                    │
│                                                ▼                    │
│  ESCALATION TRIGGERS (via HandoffResult.needs_human_input):        │
│  ─────────────────────────────────────────────────────────         │
│  • Agent confidence < 0.5                                          │
│  • HandoffResult.needs_human_input = true                          │
│  • Multiple conflicting recommendations                            │
│  • Task outside agent capabilities                                 │
│  • User explicitly requests human review                           │
│                                                                     │
│  ESCALATION PATH:                                                  │
│  Larry presents findings to USER with "needs_human_input" flag     │
│  User decides: approve / modify / reject / consult expert          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Who is "Larry" in the actual project context?
  Larry is an AI ROLE agent (The Clarifier), NOT a human supervisor.
  Larry is the ALWAYS-ON entry point that users interact with.
  Larry's job: Clarify problems using the Three Questions (What/Who/Success)

What decisions currently require human approval?
  - HandoffResult.needs_human_input = true triggers user review
  - Low confidence results (< 0.5) are flagged for user consideration
  - User can always interrupt to redirect/clarify
  - NO hard blocking - user receives output with recommendations

Existing escalation mechanisms:
  - HandoffType.ESCALATE (defined in mindrian/handoff/types.py)
  - HandoffResult.needs_human_input: bool
  - HandoffResult.human_input_reason: str
  - Returns to Larry who presents to user

Human interface tools in use:
  - Streamlit chat UI (planned)
  - Chainlit chat UI (planned)
  - FastAPI REST + WebSocket for integrations

Response time expectations for human decisions:
  - Async: User can respond whenever (session persists)
  - No hard timeouts on user responses
  - Agents continue or pause based on workflow configuration

How should rejected decisions be handled?
  - User can redirect to different framework
  - User can provide additional clarification
  - Larry re-engages to refine problem understanding

Is there a hierarchy of human supervisors?
  - NO - single user model for MVP
  - Future: Team collaboration with role-based permissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.3 Interaction Flow Modeling

**Mindrian Interaction Types:**

| Interaction Type | Participants | Mindrian Implementation | Example |
|-----------------|--------------|------------------------|---------|
| **Single Agent** | User ↔ Larry | ConversationSummary | Problem clarification |
| **Sequential Handoff** | Larry → Minto → Larry | HandoffMode.SEQUENTIAL | Structure then validate |
| **Parallel Consultation** | Larry → [Minto, PWS, JTBD] | HandoffMode.PARALLEL | Multi-framework analysis |
| **Debate Mode** | Agent vs Devil | HandoffMode.DEBATE | Challenge assumptions |
| **Team Collaboration** | Clarification Team | Team with coordinate mode | Larry + Devil |

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current interaction flows in the project:

1. CLARIFICATION FLOW:
   User → Larry (clarify) → [clarity >= 0.6?] → Router → Agents → Synthesize → User

2. SEQUENTIAL ANALYSIS:
   Larry → Minto → PWS → JTBD (each builds on previous via previous_analyses)

3. PARALLEL ANALYSIS:
   Larry → [Minto + PWS + JTBD] simultaneously → Synthesizer → User

4. DEBATE FLOW:
   Larry → Framework + Devil → Synthesize opposing views → User

Existing documentation/diagrams to reference:
  - docs/ARCHITECTURE.md - Full system diagram
  - docs/SWARM_MANAGER_SPECS.md - Handoff protocol details
  - docs/AGENT_ONTOLOGY.md - Agent type definitions

Common failure scenarios encountered:
  - Agent timeout (default 300 seconds)
  - Low confidence results requiring user input
  - Missing problem clarity (< 0.6)
  - Tool/MCP connection failures

Priority handling requirements:
  - HandoffContext.priority: 1=normal, 2=high, 3=urgent
  - Not yet implemented in execution order

Interrupt scenarios that must be supported:
  - User cancellation mid-workflow
  - User redirect to different framework
  - Session timeout (configurable, default 60 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 3: Agent Team & Community Architecture

### 3.1 Agent Team Creation Patterns

**Mindrian Team Architecture:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MINDRIAN TEAM STRUCTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TEAM DEFINITION (from teams/*.yaml):                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ team:                                                        │   │
│  │   id: "clarification-team"                                   │   │
│  │   name: "Clarification Team"                                 │   │
│  │   members:                                                   │   │
│  │     - agent: "larry-clarifier"    role: "primary"           │   │
│  │     - agent: "devil-advocate"     role: "challenger"        │   │
│  │   coordination:                                              │   │
│  │     mode: "coordinate"   # sequential                        │   │
│  │     sequence:                                                │   │
│  │       - agent: "larry" until: "problem_clarity >= 0.6"      │   │
│  │       - agent: "devil" until: "assumptions_validated"       │   │
│  │   success_criteria:                                          │   │
│  │     - "problem_clarity.what_clarity >= 0.7"                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  MINDRIAN ROLE TYPES (from docs/AGENT_ONTOLOGY.md):                │
│  ──────────────────────────────────────────────────                │
│  • ROLE       - Conversational (Larry, Devil) - talks to users     │
│  • OPERATOR   - Framework (Minto, PWS) - processes inputs          │
│  • COLLABORATIVE - Multi-perspective (De Bono) - sub-agents        │
│  • PIPELINE   - Sequential (Deep Research) - phased execution      │
│  • GUIDED     - Interactive (Wizards) - step-by-step with user     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agent teams currently defined in project:
  - clarification-team (planned): Larry + Devil
  - analysis-team (planned): Framework agents in parallel
  - deep-research-team (implemented): mindrian/teams/deep_research_team.py

Team composition approach:
  - STATIC teams for known workflows (clarification, analysis, validation)
  - DYNAMIC selection of frameworks via Neo4j router

Existing role definitions (from AGENT_ONTOLOGY.md):
  - ROLE agents: conversational/ folder - Larry, Devil, Expert, Mentor
  - OPERATOR agents: frameworks/ folder - Minto, PWS, JTBD, etc.
  - RESEARCH agents: research/ folder - Beautiful Question, CSIO, Domain

Team communication mechanisms:
  - HandoffContext passed between agents
  - previous_analyses accumulates outputs
  - No direct agent-to-agent messaging (always via HandoffManager)

How are new teams created?
  - YAML definition in teams/*.yaml
  - Team class instantiation with member agents
  - Registration with workflow registry

Team performance metrics tracked (planned):
  - Total execution time
  - Individual agent durations
  - Success rate per team
  - Average confidence scores
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3.2 Agent Community Architecture

**Mindrian Community = Neo4j Knowledge Graph**

```
┌─────────────────────────────────────────────────────────────────────┐
│                 MINDRIAN AGENT COMMUNITY (Neo4j)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ Clarification│    │   Analysis   │    │  Validation  │          │
│  │    Team      │    │    Team      │    │    Team      │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         └───────────────────┼───────────────────┘                   │
│                             │                                       │
│                    ┌────────▼────────┐                             │
│                    │    NEO4J        │                             │
│                    │ AGENT REGISTRY  │                             │
│                    │ ─────────────── │                             │
│                    │ (:Framework)    │                             │
│                    │ (:Session)      │                             │
│                    │ (:Insight)      │                             │
│                    └────────┬────────┘                             │
│                             │                                       │
│         ┌───────────────────┼───────────────────┐                   │
│         │                   │                   │                   │
│  ┌──────▼───────┐    ┌──────▼───────┐    ┌──────▼───────┐          │
│  │  Capability  │    │   Problem    │    │    Usage     │          │
│  │  Discovery   │    │   Router     │    │   Tracking   │          │
│  │ ──────────── │    │ ──────────── │    │ ──────────── │          │
│  │ f.triggers   │    │ MATCH query  │    │ USED_BY rel  │          │
│  │ f.problem_   │    │ by triggers  │    │ success rate │          │
│  │ types        │    │ & types      │    │ per session  │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scale of agent community anticipated:
  - Initial: 10-20 framework agents
  - Target: 50-100 specialized agents
  - No hard limit - Neo4j scales horizontally

Existing agent registry approach:
  - Neo4j (:Framework) nodes
  - Registration on agent build via Agent Builder
  - Auto-registration on startup (deployment.auto_register: true)

How is agent discovery currently handled?
  - Neo4j query by triggers[] and problem_types[]
  - Router queries top 5 matching frameworks
  - No runtime agent discovery - all pre-registered

Governance requirements (compliance, audit):
  - All interactions logged in Supabase conversations
  - Insights stored in Neo4j with source agent
  - No PII stored in agent memory (user profile separate)

Resource constraints to consider:
  - Token budgets per agent (deployment.resources.token_budget)
  - Max concurrent executions per agent
  - Timeouts (default 300 seconds)

Trust/reputation tracking (planned):
  - Framework success rate: USED_BY relationship with success: true/false
  - Confidence accumulation from HandoffResult.confidence
  - Not yet implemented in router weighting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 4: Swarm Architecture Research

### 4.1 Multi-Agent Orchestration Patterns

**Mindrian Patterns (Already Defined):**

| Pattern | Mindrian Name | Config | Use Case |
|---------|--------------|--------|----------|
| Hierarchical | Router → Teams → Agents | HandoffMode.SELECTIVE | Main workflow |
| Peer-to-Peer | - | Not used | N/A |
| Blackboard | previous_analyses | HandoffContext | Build on prior work |
| Pipeline | HandoffMode.SEQUENTIAL | Phase definitions | Step-by-step analysis |
| Ensemble | HandoffMode.PARALLEL | Team collaborate mode | Multi-framework analysis |
| Debate | HandoffMode.DEBATE | Team debate mode | Challenge assumptions |

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Orchestration patterns currently in use:
  - HIERARCHICAL: Larry → Router → Team → Agents → Synthesizer
  - BLACKBOARD: previous_analyses accumulates outputs for next agent
  - PIPELINE: Agent Builder's 7-phase transformation

Preferred pattern for new implementations:
  - Default: HIERARCHICAL with Larry as entry
  - Analysis: PARALLEL (multiple frameworks)
  - Validation: SEQUENTIAL (build on each other)

Known limitations of current patterns:
  - No true peer-to-peer negotiation between agents
  - Debate mode needs synthesis agent to resolve
  - Pipeline cannot skip phases dynamically

Performance requirements:
  - Individual agent: < 60 seconds typical, 300 max
  - Full workflow: < 5 minutes for clarify → analyze → synthesize
  - Parallel execution reduces wall-clock time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.2 Handoff Protocol Design (IMPLEMENTED)

**Mindrian HandoffContext Structure:**

```python
@dataclass
class HandoffContext:
    # === IDENTITY ===
    handoff_id: str                    # UUID tracking
    timestamp: datetime

    # === PROBLEM DEFINITION (from Larry) ===
    problem_clarity: ProblemClarity    # what, who, success + clarity scores

    # === CONVERSATION STATE ===
    conversation: ConversationSummary  # key_points, user_goals, constraints
    session_id: Optional[str]

    # === PREVIOUS WORK ===
    previous_analyses: List[PreviousAnalysis]  # Blackboard pattern

    # === HANDOFF INSTRUCTIONS ===
    task_description: str              # What to do
    expected_output: str               # Format expected
    focus_areas: List[str]
    ignore_areas: List[str]

    # === ROUTING INFO ===
    from_agent: str
    to_agent: str
    return_to: str
    return_behavior: ReturnBehavior    # SYNTHESIZE | PASSTHROUGH | ITERATE

    # === METADATA ===
    handoff_type: HandoffType          # DELEGATE | TRANSFER | RETURN | ESCALATE
    handoff_mode: HandoffMode          # SEQUENTIAL | PARALLEL | SELECTIVE | DEBATE
    priority: int                      # 1=normal, 2=high, 3=urgent
    timeout_seconds: int               # Default 300
```

```
[MINDRIAN CLARIFICATION - COMPLETED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current handoff data structure:
  - Fully implemented in mindrian/handoff/context.py
  - HandoffContext + HandoffResult dataclasses
  - to_prompt() method generates agent-readable context

Required context fields:
  - handoff_id (for tracking)
  - problem_clarity (REQUIRED - foundation of all work)
  - task_description (what agent should do)
  - from_agent, to_agent, return_to (routing)

Handoff logging/audit requirements:
  - HandoffResult stored in HandoffManager._history
  - Duration tracked in HandoffResult.duration_seconds
  - Errors captured in HandoffResult.error

Failure recovery procedures:
  - On timeout: return partial results if available
  - On error: HandoffResult.success=False, .error=message
  - Retry logic in HandoffManager (not yet implemented)

Handoff latency requirements:
  - Context serialization: < 100ms
  - to_prompt() generation: < 10ms
  - Network latency: dependent on LLM provider
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 5: Skill Development Specification

### 5.1 Skill Structure (Mindrian-Specific)

```
/mnt/skills/user/mindrian-swarm-architect/
├── SKILL.md                         # Main skill documentation
├── schemas/
│   ├── agent-spec.yaml              # Complete AgentSpec schema
│   ├── handoff-context.yaml         # HandoffContext schema
│   ├── handoff-result.yaml          # HandoffResult schema
│   ├── team-config.yaml             # Team configuration schema
│   ├── workflow-config.yaml         # Workflow configuration schema
│   └── problem-clarity.yaml         # ProblemClarity schema
├── templates/
│   ├── agent-template.py            # Mindrian agent Python template
│   ├── team-template.yaml           # Team YAML template
│   ├── workflow-template.yaml       # Workflow YAML template
│   ├── schema.cypher                # Neo4j registration template
│   └── test-template.py             # Agent test template
├── review/
│   ├── checklist.md                 # Mindrian-specific review checklist
│   ├── anti-patterns.md             # Common Mindrian mistakes
│   └── quality-rubric.md            # Assessment criteria
├── patterns/
│   ├── clarification-team.md        # Larry + Devil pattern
│   ├── parallel-analysis.md         # Multi-framework pattern
│   ├── sequential-pipeline.md       # Build-on-previous pattern
│   ├── debate-mode.md               # Opposing positions pattern
│   └── neo4j-routing.md             # Graph-based selection pattern
└── examples/
    ├── operator-agent/              # Minto/PWS style agent
    ├── role-agent/                  # Larry/Devil style agent
    ├── collaborative-agent/         # De Bono style agent
    └── full-workflow/               # Complete Mindrian workflow
```

### 5.2 SKILL.md Core Sections

1. **When to Use This Skill** - Triggers for Mindrian architecture work
2. **Mindrian Architecture Overview** - 6-layer diagram reference
3. **Agent Creation Guide** - From SKILL.md → deployed agent
4. **Team Composition Guide** - coordinate/collaborate/debate modes
5. **Handoff Protocol Reference** - Context/Result structures
6. **Neo4j Integration Guide** - Schema, queries, registration
7. **Quality Review Checklist** - Mindrian-specific validation

---

## Phase 6: Validation Strategy

### 6.1 Test Cases (Mindrian-Specific)

**Test Case 1: Create Operator Agent**
- Input: SKILL.md for new framework (e.g., "Root Cause Analysis")
- Expected: AgentSpec YAML + Python code + Neo4j schema + tests

**Test Case 2: Design Team Composition**
- Input: "Create team for market validation"
- Expected: Team YAML with appropriate members, mode, success criteria

**Test Case 3: Review Handoff Flow**
- Input: Proposed handoff chain diagram
- Expected: Validation against HandoffContext requirements

**Test Case 4: Neo4j Schema Design**
- Input: "Add agent reputation tracking"
- Expected: Cypher schema + queries + migration plan

**Test Case 5: Full Workflow Design**
- Input: "Design workflow for competitive analysis"
- Expected: Complete workflow YAML with steps, routing, error handling

### 6.2 Success Criteria

- [ ] Can generate valid AgentSpec YAML from requirements
- [ ] Can create Mindrian agent Python code that compiles
- [ ] Can design HandoffContext for any agent chain
- [ ] Can write Neo4j Cypher for framework registration
- [ ] Can compose teams with appropriate modes
- [ ] Can identify Mindrian anti-patterns in reviews
- [ ] Can suggest appropriate agent types for tasks
- [ ] Reviews follow consistent Mindrian structure

---

## Phase 7: Research Execution Tasks

### Immediate Research (Web Search Required)

1. **Agno Framework Documentation**
   - Search: "Agno AI framework documentation agent team"
   - Search: "Agno Python orchestration examples"
   - Fetch: https://docs.agno.com

2. **MCP Best Practices**
   - Search: "Model Context Protocol tool design patterns"
   - Search: "MCP server authentication best practices"

### Internal Research (Codebase Review)

3. **Existing Mindrian Patterns**
   - Read: docs/ARCHITECTURE.md
   - Read: docs/SWARM_MANAGER_SPECS.md
   - Read: docs/AGENT_ONTOLOGY.md
   - Read: mindrian/handoff/context.py

4. **Neo4j Schema Analysis**
   - Query current schema via Neo4j MCP
   - Document existing relationships

---

## Answered Questions

| # | Question | Mindrian Answer |
|---|----------|-----------------|
| 1 | Support multiple orchestration frameworks beyond Agno? | NO - Agno only |
| 2 | Neo4j integration level? | READ + WRITE (full CRUD) |
| 3 | Include deployment config generation? | YES - deploy/agents.yaml |
| 4 | Persistence backends? | Supabase (PostgreSQL + pgvector) + Neo4j |
| 5 | Expected conversation length? | 100 turns max (configurable) |
| 6 | Privacy requirements? | No PII in agent memory, user profile separate |
| 7 | Who is "Larry"? | AI ROLE agent (The Clarifier), NOT human |
| 8 | Communication channels for escalation? | Streamlit/Chainlit UI, FastAPI WebSocket |
| 9 | Acceptable human response latency? | Async, no hard timeout |
| 10 | Multiple supervisor roles? | NO - single user model for MVP |
| 11 | Agent community scale? | 50-100 agents target |
| 12 | Teams static or dynamic? | STATIC teams, DYNAMIC framework selection |
| 13 | Governance requirements? | Audit logs in Supabase, insights in Neo4j |
| 14 | Include cost estimation? | YES via token_budget per agent |
| 15 | Generate test suites? | YES - test_agent.py per agent |
| 16 | Output formats? | Markdown (primary), YAML (configs), Python (code) |
| 17 | Existing Agno deployments? | YES - research agents, deep research team |
| 18 | Integrate with n8n? | YES - n8n MCP available for workflow automation |
| 19 | Standard MCP servers for handoffs? | neo4j, supabase (NO Pinecone) |

---

## Next Steps

1. **Complete Agno research** - Deep dive into Team and Workflow primitives
2. **Build skill structure** - Create file hierarchy as specified
3. **Write SKILL.md** - Main documentation
4. **Create templates** - Agent, team, workflow templates
5. **Develop examples** - Each agent type example
6. **Test against real Mindrian work** - Validate with actual agent creation

---

*Mindrian Swarm Architect Skill Plan v1.0*
*Customized for Mindrian Architecture*
