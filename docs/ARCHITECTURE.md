# Mindrian System Architecture

> A thinking architect's view of how Mindrian works, scales, and evolves.

---

## 1. The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Streamlit  │  │   Chainlit  │  │   FastAPI   │  │  WebSocket  │        │
│  │    (Chat)   │  │   (Chat)    │  │    (REST)   │  │  (Stream)   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        SESSION MANAGER                                │   │
│  │  • Creates/resumes sessions                                          │   │
│  │  • Maintains conversation state                                       │   │
│  │  • Routes to appropriate entry point                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      MINDRIAN ORCHESTRATOR                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │   Larry    │  │  Problem   │  │   Team     │  │ Synthesis  │     │   │
│  │  │ (Clarify)  │─►│  Router    │─►│  Dispatch  │─►│   Agent    │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        HANDOFF MANAGER                                │   │
│  │  • Creates HandoffContext                                             │   │
│  │  • Executes handoffs (sequential, parallel, debate)                   │   │
│  │  • Collects HandoffResults                                            │   │
│  │  • Triggers synthesis                                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT LAYER                                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         TEAMS                                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Clarification│  │   Analysis   │  │  Validation  │              │    │
│  │  │    Team      │  │    Team      │  │    Team      │              │    │
│  │  │ ──────────── │  │ ──────────── │  │ ──────────── │              │    │
│  │  │ Larry+Devil  │  │ Frameworks   │  │ Research+PWS │              │    │
│  │  │ (coordinate) │  │ (collaborate)│  │ (coordinate) │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────┴───────────────────────────────────┐    │
│  │                         AGENTS                                       │    │
│  │                                                                      │    │
│  │  CONVERSATIONAL          OPERATORS              RESEARCH             │    │
│  │  ┌──────────┐          ┌──────────┐          ┌──────────┐          │    │
│  │  │  Larry   │          │  Minto   │          │Beautiful │          │    │
│  │  │  Devil   │          │  PWS     │          │ Question │          │    │
│  │  │  Expert  │          │  JTBD    │          │  Domain  │          │    │
│  │  │  Mentor  │          │ Scenario │          │   CSIO   │          │    │
│  │  └──────────┘          │ De Bono  │          │  Tavily  │          │    │
│  │                        │ Systems  │          └──────────┘          │    │
│  │                        │ Trending │                                 │    │
│  │                        └──────────┘                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE LAYER                                 │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   NEO4J GRAPH    │  │ SUPABASE MEMORY  │  │  PINECONE VECTOR │          │
│  │  ──────────────  │  │  ──────────────  │  │  ──────────────  │          │
│  │ • Framework graph│  │ • Conversations  │  │ • PWS Brain      │          │
│  │ • Relationships  │  │ • RAG retrieval  │  │ • Semantic search│          │
│  │ • Selection query│  │ • Session state  │  │ • Embeddings     │          │
│  │ • Breakthroughs  │  │ • User prefs     │  │                  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                        MCP SERVERS                                  │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │     │
│  │  │  Neo4j  │  │Pinecone │  │ Render  │  │   n8n   │  │ Tavily  │ │     │
│  │  │   MCP   │  │   MCP   │  │   MCP   │  │   MCP   │  │   MCP   │ │     │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                      CUSTOM TOOLS                                   │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │     │
│  │  │  PWS Brain   │  │   Handoff    │  │   Session    │             │     │
│  │  │  Retrieval   │  │    Tools     │  │    Tools     │             │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BUILDER LAYER                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        AGENT BUILDER                                  │   │
│  │  SKILL.md ──► Schema ──► Handoff ──► Tools ──► Neo4j ──► Code ──► Register │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        SKILL REGISTRY                                 │   │
│  │  • Loads SKILL.md files from mindrian-platform                        │   │
│  │  • Maintains agent catalog                                            │   │
│  │  • Handles versioning                                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Interaction Patterns

### 2.1 The Main Flow (User → Response)

```
User Input
    │
    ▼
┌─────────────────┐
│ Session Manager │ ── Creates/loads session, retrieves context from Supabase
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Larry       │ ── Clarifies problem (What/Who/Success)
│   (Clarifier)   │    Uses conversation memory for context
└────────┬────────┘
         │
         │ ProblemClarity (score >= 0.6?)
         │
         ▼
┌─────────────────┐
│ Problem Router  │ ── Queries Neo4j for best frameworks
│                 │    Routes based on problem type
└────────┬────────┘
         │
         │ HandoffContext
         │
         ▼
┌─────────────────┐
│ Handoff Manager │ ── Dispatches to Team or Agent
│                 │    Manages execution mode (seq/parallel/debate)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ Agent │ │ Agent │ ── Each agent processes via its methodology
│   A   │ │   B   │    Each returns HandoffResult
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│   Synthesizer   │ ── Combines results into coherent response
│                 │    Stores insights in Neo4j
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Session Manager │ ── Stores conversation turn in Supabase
│                 │    Updates session state
└────────┬────────┘
         │
         ▼
    User Response
```

### 2.2 Handoff Protocol Flow

```
                    ORCHESTRATOR
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ DELEGATE│   │ DELEGATE│   │ DELEGATE│
      │ Context │   │ Context │   │ Context │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
           ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ Agent A │   │ Agent B │   │ Agent C │
      │ (Minto) │   │  (PWS)  │   │ (JTBD)  │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
           ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ RETURN  │   │ RETURN  │   │ RETURN  │
      │ Result  │   │ Result  │   │ Result  │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
           └─────────────┼─────────────┘
                         │
                         ▼
                    SYNTHESIZE
                         │
                         ▼
                   User Response
```

### 2.3 Intelligence Layer Interactions

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUERY FLOW                                    │
│                                                                  │
│  User asks: "Help me with customer churn"                        │
│                                                                  │
│  1. SUPABASE: Retrieve similar past conversations                │
│     SELECT * FROM conversations                                  │
│     WHERE embedding <-> query_embedding < 0.3                    │
│     ──► Returns: Previous churn discussions, preferences         │
│                                                                  │
│  2. PINECONE: Retrieve PWS brain knowledge                       │
│     query("customer churn reduction strategies")                 │
│     ──► Returns: Relevant PWS methodology chunks                 │
│                                                                  │
│  3. NEO4J: Select best frameworks                                │
│     MATCH (f:Framework)                                          │
│     WHERE 'churn' IN f.triggers OR 'retention' IN f.triggers     │
│     ──► Returns: [JTBD (0.9), PWS (0.8), Minto (0.6)]           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE FLOW                                  │
│                                                                  │
│  After analysis completes:                                       │
│                                                                  │
│  1. SUPABASE: Store conversation turn                            │
│     INSERT INTO conversations (session_id, role, content, ...)   │
│                                                                  │
│  2. NEO4J: Store breakthrough insight                            │
│     CREATE (i:Insight {content: "...", confidence: 0.8})         │
│     CREATE (i)-[:DISCOVERED_BY]->(f:Framework {id: "jtbd"})      │
│     CREATE (i)-[:RELATES_TO]->(t:Topic {name: "churn"})          │
│                                                                  │
│  3. NEO4J: Update framework effectiveness                        │
│     MATCH (f:Framework {id: "jtbd"})                             │
│     SET f.success_count = f.success_count + 1                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Taxonomy & Placement

### 3.1 Where Agents Live

```
mindrian/agents/
│
├── conversational/          # ROLE agents - talk to users
│   ├── larry.py            # The Clarifier (entry point)
│   ├── devil.py            # Devil's Advocate (challenger)
│   ├── expert.py           # Domain Expert (deep knowledge)
│   └── mentor.py           # Framework Guide (teaches)
│
├── frameworks/             # OPERATOR agents - process inputs
│   ├── minto_pyramid.py    # SCQA structuring
│   ├── pws_validation.py   # 4-pillar scoring
│   ├── jobs_to_be_done.py  # JTBD mapping
│   ├── scenario_analysis.py# 2x2 matrix
│   ├── debono_hats.py      # 6 perspectives (COLLABORATIVE)
│   ├── systems_thinking.py # Feedback loops
│   └── trending_absurd.py  # Future extrapolation
│
├── research/               # Insight generation agents
│   ├── beautiful_question.py  # Why→What If→How
│   ├── domain_analysis.py     # Domain mapping
│   ├── csio.py               # Cross-sectional innovation
│   └── tavily_research.py    # Web research
│
├── synthesis/              # Combine & conclude agents
│   ├── synthesizer.py      # Combine multiple analyses
│   ├── recommender.py      # Generate recommendations
│   └── living_document.py  # Maintain evolving doc
│
└── meta/                   # Agents that manage agents
    ├── router.py           # Problem classification
    ├── builder.py          # Agent builder
    └── evaluator.py        # Quality assessment
```

### 3.2 Agent Type Decision Tree

```
                        NEW AGENT NEEDED
                              │
                              ▼
                    Does it talk to users?
                    ─────────────────────
                         │           │
                        YES          NO
                         │           │
                         ▼           ▼
                      ROLE      Does it follow
                   (conversational/)  a methodology?
                                ─────────────────
                                   │         │
                                  YES        NO
                                   │         │
                                   ▼         ▼
                            Single output?   What does it do?
                            ─────────────    ───────────────
                               │    │           │    │    │
                              YES   NO      Combine Search Meta
                               │    │           │    │    │
                               ▼    ▼           ▼    ▼    ▼
                           OPERATOR COLLABORATIVE synthesis/ research/ meta/
                          (frameworks/) (frameworks/)
```

### 3.3 Adding a New Framework Agent

**Example: Adding "First Principles" framework**

```
1. CREATE SKILL.md
   /mindrian-platform/skills/operators/first-principles/SKILL.md

   ---
   name: First Principles
   type: operator
   triggers: [first principles, fundamentals, assumptions, basics]
   inputs: [problem_statement]
   outputs: [markdown]
   chaining: [minto-pyramid, scenario-analysis]
   ---

   ## Methodology
   1. Identify the problem
   2. Break down into fundamental truths
   3. Question every assumption
   4. Rebuild from ground up

   ## Output Template
   ...

2. RUN AGENT BUILDER
   builder = AgentBuilder()
   result = await builder.build_from_skill(
       "/path/to/first-principles/SKILL.md"
   )
   # Creates: mindrian/agents/frameworks/first_principles/

3. REGISTER IN NEO4J (automatic)
   MERGE (f:Framework {id: 'first-principles'})
   SET f.name = 'First Principles', ...

4. ADD TO TEAMS (if needed)
   # In teams/analysis.py
   analysis_team.add_member(first_principles_agent)

5. TEST
   pytest tests/agents/test_first_principles.py
```

---

## 4. Feature Addition Workflow

### 4.1 Adding a New Capability

```
┌─────────────────────────────────────────────────────────────────┐
│                  FEATURE: Add sentiment analysis                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: Identify Layer                                          │
│  ─────────────────────                                           │
│  Q: Where does this live?                                        │
│  A: It's a tool that agents use → TOOL LAYER                     │
│                                                                  │
│  STEP 2: Implement Tool                                          │
│  ─────────────────────                                           │
│  # tools/sentiment.py                                            │
│  def analyze_sentiment(text: str) -> dict:                       │
│      # Implementation                                            │
│      return {"sentiment": "positive", "confidence": 0.85}        │
│                                                                  │
│  STEP 3: Register as MCP or Custom Tool                          │
│  ───────────────────────────────────────                         │
│  # If external service → MCP                                     │
│  # If local function → Custom Tool                               │
│  tools:                                                          │
│    custom_tools:                                                 │
│      - name: analyze_sentiment                                   │
│        function: mindrian.tools.sentiment.analyze_sentiment      │
│                                                                  │
│  STEP 4: Add to Agent Specs                                      │
│  ──────────────────────────                                      │
│  # Agents that need sentiment can now use it                     │
│  # Update relevant SKILL.md or AgentSpec                         │
│                                                                  │
│  STEP 5: Update Neo4j Schema (if needed)                         │
│  ───────────────────────────────────────                         │
│  # If sentiment should be stored                                 │
│  CREATE (s:Sentiment {value: $val})-[:OF]->(c:Conversation)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Adding a New Team

```
┌─────────────────────────────────────────────────────────────────┐
│               FEATURE: Add "Innovation Team"                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: Define Team Purpose                                     │
│  ──────────────────────────                                      │
│  Innovation Team: Generate novel solutions                       │
│  Members: CSIO + Trending + Beautiful Question                   │
│  Mode: collaborate (parallel perspectives)                       │
│                                                                  │
│  STEP 2: Create Team Definition                                  │
│  ─────────────────────────────                                   │
│  # teams/innovation.py                                           │
│                                                                  │
│  from agno.team import Team                                      │
│  from ..agents.research import csio, beautiful_question          │
│  from ..agents.frameworks import trending_absurd                 │
│                                                                  │
│  innovation_team = Team(                                         │
│      name="Innovation Team",                                     │
│      members=[                                                   │
│          csio.CSIOAgent().agent,                                 │
│          beautiful_question.BeautifulQuestionAgent().agent,      │
│          trending_absurd.TrendingAbsurdAgent().agent,            │
│      ],                                                          │
│      mode="collaborate",                                         │
│      instructions="Generate innovative solutions...",            │
│  )                                                               │
│                                                                  │
│  STEP 3: Register with Router                                    │
│  ────────────────────────────                                    │
│  # workflow/router.py                                            │
│  problem_router.add_route(                                       │
│      condition="innovation OR creative OR novel",                │
│      team=innovation_team                                        │
│  )                                                               │
│                                                                  │
│  STEP 4: Update Neo4j                                            │
│  ────────────────────                                            │
│  CREATE (t:Team {id: 'innovation', name: 'Innovation Team'})     │
│  MATCH (f:Framework) WHERE f.id IN ['csio', 'trending', 'bq']    │
│  CREATE (t)-[:INCLUDES]->(f)                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Adding a New Memory Type

```
┌─────────────────────────────────────────────────────────────────┐
│            FEATURE: Add "Decision Memory"                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Purpose: Remember past decisions and their outcomes             │
│                                                                  │
│  STEP 1: Choose Storage                                          │
│  ─────────────────────                                           │
│  • Structured data with relationships → Neo4j                    │
│  • Needs semantic search → Supabase pgvector                     │
│  • Decision: BOTH (Neo4j for graph, Supabase for search)         │
│                                                                  │
│  STEP 2: Design Schema                                           │
│  ────────────────────                                            │
│  # Neo4j                                                         │
│  (:Decision {                                                    │
│      id, timestamp, description,                                 │
│      context, outcome, confidence                                │
│  })-[:MADE_FOR]->(:Problem)                                      │
│   -[:USED]->(:Framework)                                         │
│   -[:LED_TO]->(:Outcome)                                         │
│                                                                  │
│  # Supabase                                                      │
│  CREATE TABLE decisions (                                        │
│      id UUID, description TEXT, embedding VECTOR(1536),          │
│      outcome TEXT, success BOOLEAN                               │
│  );                                                              │
│                                                                  │
│  STEP 3: Create Memory Class                                     │
│  ───────────────────────────                                     │
│  # memory/decision_memory.py                                     │
│  class DecisionMemory:                                           │
│      def store(decision, outcome)                                │
│      def recall_similar(context, top_k=5)                        │
│      def get_success_rate(framework_id)                          │
│                                                                  │
│  STEP 4: Integrate with Agents                                   │
│  ────────────────────────────                                    │
│  # Agents can now recall past decisions                          │
│  past_decisions = decision_memory.recall_similar(context)        │
│  # And store new ones                                            │
│  decision_memory.store(decision, outcome)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Patterns

### 5.1 Context Enrichment Pipeline

```
User Input: "Help me reduce customer churn in my SaaS"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CONTEXT ENRICHMENT                           │
│                                                                  │
│  1. SESSION CONTEXT (Supabase)                                   │
│     ├── User preferences: {"industry": "SaaS", "role": "CEO"}    │
│     ├── Past topics: ["growth", "pricing", "churn"]              │
│     └── Conversation style: "direct"                             │
│                                                                  │
│  2. SEMANTIC MEMORY (Supabase pgvector)                          │
│     ├── Similar past conversation: "Discussed churn in Q2..."    │
│     └── Relevant insight: "Identified pricing as key factor"     │
│                                                                  │
│  3. KNOWLEDGE GRAPH (Neo4j)                                      │
│     ├── Related frameworks: [JTBD, PWS, Scenario]                │
│     ├── Past success: "JTBD worked well for retention"           │
│     └── Domain knowledge: "SaaS churn typically 5-7%"            │
│                                                                  │
│  4. PWS BRAIN (Pinecone)                                         │
│     └── Methodology: "For churn, identify jobs-to-be-done..."    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ENRICHED CONTEXT
                    ────────────────
                    • User profile
                    • Relevant history
                    • Framework recommendations
                    • Domain knowledge
                    • Methodology hints
                              │
                              ▼
                         TO LARRY
```

### 5.2 Insight Storage Pipeline

```
Analysis Complete: "Key insight: Churn driven by poor onboarding"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INSIGHT STORAGE                             │
│                                                                  │
│  1. CLASSIFY INSIGHT                                             │
│     Type: "root_cause"                                           │
│     Confidence: 0.85                                             │
│     Source: "JTBD analysis"                                      │
│                                                                  │
│  2. STORE IN NEO4J (Graph)                                       │
│     CREATE (i:Insight {                                          │
│         id: "ins_123",                                           │
│         content: "Churn driven by poor onboarding",              │
│         type: "root_cause",                                      │
│         confidence: 0.85                                         │
│     })                                                           │
│     CREATE (i)-[:DISCOVERED_BY]->(:Framework {id: "jtbd"})       │
│     CREATE (i)-[:ABOUT]->(:Topic {name: "churn"})                │
│     CREATE (i)-[:IN_SESSION]->(:Session {id: "sess_456"})        │
│                                                                  │
│  3. STORE IN SUPABASE (Searchable)                               │
│     INSERT INTO insights (                                       │
│         id, content, embedding, session_id, created_at           │
│     ) VALUES (...)                                               │
│                                                                  │
│  4. UPDATE FRAMEWORK STATS                                       │
│     MATCH (f:Framework {id: "jtbd"})                             │
│     SET f.insights_generated = f.insights_generated + 1          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Scaling Patterns

### 6.1 Adding More Frameworks

```
Current: 7 frameworks
Target: 50+ frameworks

SCALING STRATEGY:
─────────────────

1. CATEGORIZE FRAMEWORKS
   └── By problem type: strategy, operations, innovation, validation
   └── By complexity: simple (single-pass), complex (multi-step)
   └── By output: analysis, decision, recommendation

2. INTELLIGENT SELECTION (Neo4j)
   └── Don't show all 50 to router
   └── Query: "Top 5 for this problem type + context"
   └── Learn from success rates

3. LAZY LOADING
   └── Don't instantiate all agents at startup
   └── Load on-demand when selected
   └── Cache frequently used

4. FRAMEWORK VERSIONING
   └── Same framework, multiple versions
   └── A/B test effectiveness
   └── Gradual rollout
```

### 6.2 Multi-User Scaling

```
                         LOAD BALANCER
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      ┌──────────┐      ┌──────────┐      ┌──────────┐
      │ Worker 1 │      │ Worker 2 │      │ Worker 3 │
      │ ──────── │      │ ──────── │      │ ──────── │
      │ Sessions │      │ Sessions │      │ Sessions │
      │ A, B, C  │      │ D, E, F  │      │ G, H, I  │
      └────┬─────┘      └────┬─────┘      └────┬─────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                    SHARED RESOURCES
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
      ┌──────────┐      ┌──────────┐      ┌──────────┐
      │  Neo4j   │      │ Supabase │      │ Pinecone │
      │ (shared) │      │ (shared) │      │ (shared) │
      └──────────┘      └──────────┘      └──────────┘

KEY PATTERNS:
─────────────
• Session affinity (user stays on same worker)
• Shared intelligence layer (all workers query same DBs)
• Stateless workers (can restart without losing state)
• Agent instances per worker (not shared)
```

---

## 7. Extension Points

### 7.1 Where to Add New Capabilities

| Want to add... | Add it here | Pattern |
|----------------|-------------|---------|
| New framework | `agents/frameworks/` | Create SKILL.md → Build with Agent Builder |
| New conversation style | `agents/conversational/` | New ROLE agent |
| New research method | `agents/research/` | New research agent |
| External service | `tools/` + MCP config | MCP server integration |
| New team composition | `teams/` | Team definition |
| New routing logic | `workflow/router.py` | Add route condition |
| New memory type | `memory/` | Storage class + schema |
| New output format | Agent's output template | Update SKILL.md |
| New UI | `api/` + `ui/` | New endpoint + frontend |

### 7.2 Modification Decision Tree

```
                    WANT TO CHANGE BEHAVIOR?
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         How agent       How agents      How things
          thinks          interact       are stored
              │               │               │
              ▼               ▼               ▼
         Modify          Modify          Modify
        SKILL.md      HandoffProtocol   Neo4j/Supabase
        or AgentSpec   or TeamDefinition  schema
```

---

## 8. Summary: The Mental Model

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   USER speaks to LARRY (always the entry point)                  │
│                           │                                      │
│   LARRY clarifies until PROBLEM is clear                         │
│                           │                                      │
│   ROUTER queries NEO4J for best FRAMEWORKS                       │
│                           │                                      │
│   HANDOFF MANAGER dispatches to TEAM or AGENT                    │
│                           │                                      │
│   AGENTS process using TOOLS (MCPs + Custom)                     │
│                           │                                      │
│   RESULTS return via HANDOFF PROTOCOL                            │
│                           │                                      │
│   SYNTHESIZER combines into coherent RESPONSE                    │
│                           │                                      │
│   MEMORY stores conversation + insights                          │
│                           │                                      │
│   USER receives intelligent, context-aware answer                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

GOLDEN RULES:
─────────────
1. Every agent receives HandoffContext, returns HandoffResult
2. Neo4j decides WHAT frameworks to use
3. Supabase remembers WHAT was said
4. Pinecone provides domain KNOWLEDGE
5. Agent Builder creates new agents from SKILL.md
6. Teams coordinate multiple agents
7. Larry is ALWAYS the user-facing entry point
```

---

*Mindrian Architecture v1.0*
