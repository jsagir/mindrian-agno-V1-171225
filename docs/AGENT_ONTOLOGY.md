# Mindrian Agent Ontology

> Complete definition of what an agent is in Mindrian, how agents communicate, and how they're built.

---

## 1. What is a Mindrian Agent?

A **Mindrian Agent** is an autonomous cognitive unit that:

1. **Receives structured context** (HandoffContext) from an orchestrator or other agent
2. **Processes that context** using a specific methodology or framework
3. **Returns structured results** (HandoffResult) with findings, recommendations, and suggested next steps
4. **Integrates with tools** (MCPs, custom functions) to extend capabilities
5. **Participates in intelligent routing** via Neo4j knowledge graph

### Agent = Agno Agent + Handoff Protocol + Tool Integration + Graph Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│                      MINDRIAN AGENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Agno Agent     │    │  Handoff Protocol │                   │
│  │  ─────────────   │    │  ───────────────  │                   │
│  │  • Model (LLM)   │    │  • HandoffContext │                   │
│  │  • Instructions  │◄──►│  • HandoffResult  │                   │
│  │  • Memory        │    │  • Routing rules  │                   │
│  │  • Tools         │    │  • Return behavior│                   │
│  └──────────────────┘    └──────────────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Tool Integration │    │ Graph Intelligence│                   │
│  │  ───────────────  │    │  ───────────────  │                   │
│  │  • MCP servers   │    │  • Neo4j schema   │                   │
│  │  • Custom tools  │    │  • Selection query│                   │
│  │  • Global actions│    │  • Relationships  │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Types

Mindrian defines **5 agent types**, each with distinct behavior patterns:

### 2.1 ROLE Agents

**Purpose:** Conversational personas that engage with users

**Examples:** Larry (The Clarifier), Devil (Devil's Advocate)

**Characteristics:**
- Short, focused responses
- Ask questions rather than provide answers
- Track conversation state (problem clarity)
- Support TRANSFER handoffs (can give control to user)
- Use behavioral rules rather than methodologies

**Handoff Pattern:**
```
User ◄──► ROLE Agent ◄──► Framework Agents
            │
            └── Can TRANSFER to other ROLEs
```

### 2.2 OPERATOR Agents

**Purpose:** Single-purpose frameworks that process inputs into structured outputs

**Examples:** Minto Pyramid, PWS Validation, JTBD

**Characteristics:**
- Clear methodology (SCQA, 4 pillars, etc.)
- Structured output templates
- Quality criteria for self-validation
- Accept DELEGATE, return via RETURN
- Can chain to other OPERATORs

**Handoff Pattern:**
```
Orchestrator ──DELEGATE──► OPERATOR ──RETURN──► Orchestrator
                              │
                              └── May suggest next OPERATOR
```

### 2.3 COLLABORATIVE Agents

**Purpose:** Multi-perspective analysis requiring parallel sub-agents

**Examples:** De Bono Hats (6 perspectives), Scenario Analysis

**Characteristics:**
- Contains multiple sub-agents
- Coordinates parallel execution
- Synthesizes diverse outputs
- May use DEBATE mode
- Higher token budgets for thinking

**Handoff Pattern:**
```
Orchestrator ──DELEGATE──► COLLABORATIVE
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          Sub-Agent 1    Sub-Agent 2    Sub-Agent 3
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                          SYNTHESIZE
                              │
                    ──RETURN──► Orchestrator
```

### 2.4 PIPELINE Agents

**Purpose:** Sequential multi-step processing

**Examples:** Deep Research (Clarify → Analyze → Validate), Agent Builder

**Characteristics:**
- Defined phases with checkpoints
- Each phase builds on previous
- Clear input/output contracts per phase
- ITERATE return behavior
- May spawn sub-agents per phase

**Handoff Pattern:**
```
Orchestrator ──DELEGATE──► PIPELINE
                              │
                    Phase 1 (Analyze)
                              ▼
                    Phase 2 (Structure)
                              ▼
                    Phase 3 (Validate)
                              │
                    ──RETURN──► Orchestrator
```

### 2.5 GUIDED Agents

**Purpose:** Interactive step-by-step experiences

**Examples:** Canvas tools, Wizards, Tutorials

**Characteristics:**
- User interaction at each step
- Partial results between steps
- Supports "back" and "skip" operations
- ITERATE return with user feedback
- Stores progress for resume

**Handoff Pattern:**
```
User ◄──► GUIDED Agent (Step 1)
              │
              ▼ ITERATE with partial result
User ◄──► GUIDED Agent (Step 2)
              │
              ▼ ITERATE with partial result
User ◄──► GUIDED Agent (Step 3)
              │
              └──► RETURN final result
```

---

## 3. Handoff Protocol

The **Handoff Protocol** is how agents communicate. It ensures:
- Context is preserved across agent boundaries
- Results are structured and actionable
- Routing decisions are intelligent

### 3.1 HandoffContext (What Agents Receive)

```python
@dataclass
class HandoffContext:
    # Identity
    handoff_id: str
    timestamp: datetime

    # Problem Definition (from Larry)
    problem_clarity: ProblemClarity  # What, Who, Success

    # Conversation State
    conversation: ConversationSummary
    session_id: Optional[str]

    # Previous Work
    previous_analyses: List[PreviousAnalysis]

    # Instructions
    task_description: str
    expected_output: str
    focus_areas: List[str]
    ignore_areas: List[str]

    # Routing
    from_agent: str
    to_agent: str
    return_to: str
    return_behavior: ReturnBehavior

    # Metadata
    handoff_type: HandoffType  # DELEGATE, TRANSFER, RETURN, ESCALATE
    handoff_mode: HandoffMode  # SEQUENTIAL, PARALLEL, SELECTIVE, DEBATE
    priority: int
    timeout_seconds: int
```

### 3.2 ProblemClarity (The Foundation)

Every handoff includes problem clarity from Larry:

```python
@dataclass
class ProblemClarity:
    # The Three Questions
    what: Optional[str]      # What is the problem?
    who: Optional[str]       # Who has this problem?
    success: Optional[str]   # What does success look like?

    # Clarity Scores (0.0 - 1.0)
    what_clarity: float
    who_clarity: float
    success_clarity: float

    # Additional Context
    assumptions: List[str]
    open_questions: List[str]

    @property
    def overall_clarity(self) -> float:
        return (what_clarity + who_clarity + success_clarity) / 3

    @property
    def is_ready_for_analysis(self) -> bool:
        return self.overall_clarity >= 0.6
```

### 3.3 HandoffResult (What Agents Return)

```python
@dataclass
class HandoffResult:
    # Identity
    handoff_id: str
    from_agent: str
    to_agent: str

    # Results
    success: bool
    output: str
    output_format: str  # markdown, json, structured

    # Structured Data
    key_findings: List[str]
    recommendations: List[str]
    confidence: float  # 0.0-1.0
    scores: Dict[str, float]

    # Follow-up
    suggested_next_agents: List[str]
    open_questions: List[str]
    needs_human_input: bool
    human_input_reason: str

    # Metadata
    duration_seconds: float
    error: Optional[str]
```

### 3.4 Handoff Types

| Type | Description | Use Case |
|------|-------------|----------|
| **DELEGATE** | Assign work, expect results back | Larry → Minto → Larry |
| **TRANSFER** | Full control passes to agent | Larry → Expert (user talks to expert) |
| **RETURN** | Complete and return to caller | Minto → Larry |
| **ESCALATE** | Need human help | Any agent → User |

### 3.5 Handoff Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **SEQUENTIAL** | A → B → C (each builds on previous) | Pipeline processing |
| **PARALLEL** | A + B + C (all work simultaneously) | Multiple perspectives |
| **SELECTIVE** | A OR B OR C (router chooses) | Specialized routing |
| **DEBATE** | A vs B (opposing positions) | Decision support |

---

## 4. Tool Integration

Agents access external capabilities through tools:

### 4.1 MCP Tools (Model Context Protocol)

External services exposed as callable tools:

| MCP Server | Tools | Purpose |
|------------|-------|---------|
| `neo4j` | read_cypher, write_cypher, get_schema | Knowledge graph |
| `pinecone` | search_records, upsert_records | Vector search |
| `render` | list_services, get_metrics | Deployment |
| `n8n` | create_workflow, validate_workflow | Automation |
| `tavily` | search, extract | Web research |

**Usage in Agent:**
```python
# Agent spec
tools:
  mcp_servers:
    - server: neo4j
      tools: ["read_neo4j_cypher", "get_neo4j_schema"]
      required: true
```

### 4.2 Custom Tools

Python functions wrapped as tools:

```python
# Custom tool definition
def store_insight(insight: str, category: str) -> str:
    """Store key insight in knowledge graph."""
    # Implementation
    return "Insight stored"

# In agent spec
tools:
  custom_tools:
    - name: store_insight
      description: "Store key insight in knowledge graph"
      function: "mindrian.tools.store_insight"
```

### 4.3 Global Actions

Actions available in all workflow phases:

```python
tools:
  global_actions:
    - action: "save_progress"
      description: "Save current state for resume"
      tool: "supabase.upsert"
    - action: "fetch_context"
      description: "Get additional context from knowledge graph"
      tool: "neo4j.read_cypher"
```

---

## 5. Neo4j Graph Intelligence

Every agent registers in Neo4j for intelligent selection:

### 5.1 Framework Node Schema

```cypher
// Node properties
(:Framework {
  id: "minto-pyramid",
  name: "Minto Pyramid",
  type: "operator",
  triggers: ["structure", "scqa", "communicate"],
  problem_types: ["ill-defined", "well-defined"],
  version: "1.0.0",
  updated_at: datetime()
})
```

### 5.2 Relationships

```cypher
// Chaining relationship
(:Framework {id: "minto"})-[:CHAINS_TO {weight: 0.9}]->(:Framework {id: "pws"})

// Good for problem type
(:Framework {id: "jtbd"})-[:GOOD_FOR {confidence: 0.8}]->(:ProblemType {name: "market"})

// Usage tracking
(:Framework {id: "csio"})-[:USED_BY {success: true}]->(:Session {id: "abc123"})
```

### 5.3 Selection Query

```cypher
// Find best frameworks for context
MATCH (f:Framework)
WHERE ANY(t IN $triggers WHERE t IN f.triggers)
   OR ANY(pt IN $problem_types WHERE pt IN f.problem_types)
WITH f,
     CASE WHEN ANY(t IN $triggers WHERE t IN f.triggers) THEN 0.6 ELSE 0 END +
     CASE WHEN ANY(pt IN $problem_types WHERE pt IN f.problem_types) THEN 0.4 ELSE 0 END
     AS score
WHERE score > 0
OPTIONAL MATCH (f)-[c:CHAINS_TO]->(next:Framework)
WHERE next.id IN $previous_frameworks
WITH f, score + COALESCE(SUM(c.weight), 0) * 0.3 AS final_score
ORDER BY final_score DESC
LIMIT 5
RETURN f.id, f.name, final_score
```

---

## 6. Agent Builder Pipeline

Agents are built through a 7-phase pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT BUILDER PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: SKILL Analysis                                         │
│  ─────────────────────                                           │
│  Input: SKILL.md path                                            │
│  Output: SkillDefinition                                         │
│  Checkpoint: valid_yaml, required_fields                         │
│                         │                                        │
│                         ▼                                        │
│  Phase 2: Architecture                                           │
│  ─────────────────────                                           │
│  Input: SkillDefinition                                          │
│  Output: AgentSpec (partial)                                     │
│  Checkpoint: type_determined, model_selected                     │
│                         │                                        │
│                         ▼                                        │
│  Phase 3: Handoff Protocol                                       │
│  ─────────────────────────                                       │
│  Input: AgentSpec                                                │
│  Output: AgentSpec + HandoffConfig                               │
│  Checkpoint: receives_defined, returns_defined                   │
│                         │                                        │
│                         ▼                                        │
│  Phase 4: Tool Assembly                                          │
│  ─────────────────────                                           │
│  Input: AgentSpec                                                │
│  Output: AgentSpec + ToolConfig                                  │
│  Checkpoint: mcps_connected, tools_available                     │
│                         │                                        │
│                         ▼                                        │
│  Phase 5: Neo4j Schema                                           │
│  ─────────────────────                                           │
│  Input: AgentSpec                                                │
│  Output: AgentSpec + Neo4jConfig                                 │
│  Checkpoint: schema_valid, queries_generated                     │
│                         │                                        │
│                         ▼                                        │
│  Phase 6: Code Generation                                        │
│  ───────────────────────                                         │
│  Input: Complete AgentSpec                                       │
│  Output: Python code files                                       │
│  Checkpoint: compiles, tests_pass                                │
│                         │                                        │
│                         ▼                                        │
│  Phase 7: Registration                                           │
│  ─────────────────────                                           │
│  Input: Code + Spec                                              │
│  Output: Registered agent                                        │
│  Checkpoint: registered, e2e_passes                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Usage Examples

### 7.1 Creating an Agent

```python
from mindrian.builder import AgentBuilder

# Initialize builder
builder = AgentBuilder()

# Build from SKILL.md
result = await builder.build_from_skill(
    "/path/to/skills/operators/pws-validation/SKILL.md"
)

if result.success:
    print(f"Agent created at: {result.output_path}")
    print(f"Files generated: {list(result.code_files.keys())}")
```

### 7.2 Using an Agent Directly

```python
from mindrian.agents.frameworks.pws_validation import PWSValidationAgent

# Create agent
pws = PWSValidationAgent()

# Direct use
result = await pws.run("Evaluate this opportunity: AI-powered pet translator")

# With handoff
context = pws.create_handoff_context(
    challenge="AI-powered pet translator",
    problem_clarity={"what": "Pet translation", "who": "Pet owners"}
)
result = await pws.process_handoff(context)
```

### 7.3 Orchestrated Workflow

```python
from mindrian.handoff.manager import handoff_manager
from mindrian.agents.frameworks import MintoPyramid, PWSValidation
from mindrian.agents.conversational import Larry

# Register agents
handoff_manager.register_agent("larry", Larry().agent)
handoff_manager.register_agent("minto", MintoPyramid().agent)
handoff_manager.register_agent("pws", PWSValidation().agent)

# Larry clarifies, then delegates
clarity = await larry.clarify(user_input)

if clarity.is_ready_for_analysis:
    # Create delegation chain
    contexts = [
        handoff_manager.create_delegation(
            from_agent="larry",
            to_agent="minto",
            task="Structure this problem",
            problem_clarity=clarity.to_dict()
        ),
        handoff_manager.create_delegation(
            from_agent="larry",
            to_agent="pws",
            task="Validate this opportunity",
            problem_clarity=clarity.to_dict()
        ),
    ]

    # Execute in parallel
    results = await handoff_manager.execute_parallel(contexts)

    # Synthesize
    synthesis = await handoff_manager.synthesize(results, contexts[0])
```

---

## 8. Summary

| Concept | Definition |
|---------|------------|
| **Agent** | Autonomous cognitive unit with model + instructions + tools + handoff |
| **HandoffContext** | Structured context passed to agents (problem clarity, task, routing) |
| **HandoffResult** | Structured return from agents (output, findings, recommendations) |
| **Agent Type** | ROLE, OPERATOR, COLLABORATIVE, PIPELINE, GUIDED |
| **Handoff Type** | DELEGATE, TRANSFER, RETURN, ESCALATE |
| **Handoff Mode** | SEQUENTIAL, PARALLEL, SELECTIVE, DEBATE |
| **MCP Tool** | External service exposed as callable tool |
| **Neo4j Intelligence** | Graph-based framework selection and routing |
| **Agent Builder** | 7-phase pipeline transforming SKILL.md → production agent |

---

*Mindrian Agent Ontology v1.0*
