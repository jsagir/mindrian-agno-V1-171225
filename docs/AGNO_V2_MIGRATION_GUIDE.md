# Agno v2 Migration Guide for Mindrian

> Critical API changes and patterns from the Swarm Architect research

---

## Executive Summary

The Swarm Architect research revealed **significant API changes** in Agno v2 that affect Mindrian's implementation. This document captures the key corrections and updated patterns.

---

## Breaking Changes from v1 → v2

### 1. Team Mode Parameter (CRITICAL)

**v1.x (DEPRECATED):**
```python
# ❌ OLD - mode parameter no longer exists
team = Team(
    mode="coordinate",  # DEPRECATED
    members=[...],
)
```

**v2.0 (CORRECT):**
```python
# ✅ NEW - Boolean flags replace mode
team = Team(
    members=[...],
    respond_directly=False,           # False = synthesize (was "coordinate")
    delegate_to_all_members=False,    # False = sequential, True = parallel
)
```

| v1.x Mode | v2.0 Configuration | Behavior |
|-----------|-------------------|----------|
| `"route"` | `respond_directly=True` | Pass-through: member response returned directly |
| `"coordinate"` | Default (no flags) | Sequential delegation with synthesis |
| `"collaborate"` | `delegate_to_all_members=True` | Parallel execution, aggregated results |

### 2. Memory Architecture (db parameter)

**v1.x (DEPRECATED):**
```python
# ❌ OLD - Separate memory configurations
agent = Agent(
    storage=SqliteStorage(),
    memory=Memory(),
)
```

**v2.0 (CORRECT):**
```python
from agno.db.sqlite import SqliteDb
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

# Session storage
db = SqliteDb(db_file="agent.db")

# Semantic memory (separate)
memory_db = SqliteMemoryDb(
    table_name="user_memories",
    db_file="tmp/agent.db"
)
memory = Memory(
    model=Claude(id="claude-sonnet-4-5"),
    db=memory_db,
)

# ✅ NEW - Consolidated db parameter + separate Memory
agent = Agent(
    db=db,                          # Session storage
    memory=memory,                  # Semantic memory
    enable_user_memories=True,
    enable_agentic_memory=True,
    enable_session_summaries=True,
)
```

### 3. Agent ID Parameter

**v1.x:**
```python
agent = Agent(agent_id="my-agent")
```

**v2.0:**
```python
# ✅ Parameter is now just "id"
agent = Agent(id="my-agent")  # Or omit - auto-generated from name
```

### 4. Extended Thinking Configuration

**Claude Extended Thinking:**
```python
from agno.models.anthropic import Claude

model = Claude(
    id="claude-sonnet-4-20250514",
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    cache_system_prompt=True,
    extended_cache_time=True,  # 1 hour cache
)
```

**Gemini Thinking Budget:**
```python
from agno.models.google import Gemini

model = Gemini(
    id="gemini-2.5-pro",
    thinking_budget=1280,
    include_thoughts=True,
    search=True,  # Google Search grounding
)
```

---

## Updated Agent Constructor Reference

The complete Agent constructor with **42+ parameters**:

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

agent = Agent(
    # ═══════════════════════════════════════════════════════════════════════════
    # IDENTITY
    # ═══════════════════════════════════════════════════════════════════════════
    name="Agent Name",                     # Display name
    id="agent-id",                         # Auto-generated from name if not set
    role="Agent's role description",       # Role context
    description="System prompt text",      # Creates system prompt

    # ═══════════════════════════════════════════════════════════════════════════
    # MODEL CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════
    model=Claude(id="claude-sonnet-4-5"),  # LLM model instance

    # ═══════════════════════════════════════════════════════════════════════════
    # INSTRUCTIONS (list of behavioral guidelines)
    # ═══════════════════════════════════════════════════════════════════════════
    instructions=[
        "Always include sources",
        "Use tables to display data"
    ],

    # ═══════════════════════════════════════════════════════════════════════════
    # TOOLS
    # ═══════════════════════════════════════════════════════════════════════════
    tools=[DuckDuckGoTools(), ReasoningTools(add_instructions=True)],

    # ═══════════════════════════════════════════════════════════════════════════
    # OUTPUT CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════
    markdown=True,                         # Format responses in markdown
    output_schema=PydanticModel,           # Structured output schema

    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    session_id="unique-session-id",        # Session identifier
    user_id="user-identifier",             # User identifier

    # ═══════════════════════════════════════════════════════════════════════════
    # DATABASE/STORAGE (v2 pattern)
    # ═══════════════════════════════════════════════════════════════════════════
    db=SqliteDb(db_file="agent.db"),       # Database for persistence

    # ═══════════════════════════════════════════════════════════════════════════
    # MEMORY CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════
    memory=Memory(db=memory_db),           # Memory instance
    enable_user_memories=True,             # Auto-create user memories
    enable_agentic_memory=True,            # Agent manages its memories
    enable_session_summaries=True,         # Generate session summaries

    # ═══════════════════════════════════════════════════════════════════════════
    # CHAT HISTORY
    # ═══════════════════════════════════════════════════════════════════════════
    add_history_to_context=True,           # Add history to context
    num_history_runs=5,                    # History runs to include
    read_chat_history=True,                # Enable chat history reading
    search_session_history=True,           # Search previous sessions
    num_history_sessions=3,                # Past sessions to search

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTEXT CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════
    add_datetime_to_context=True,          # Include current date/time
    add_datetime_to_instructions=True,     # Date/time in instructions

    # ═══════════════════════════════════════════════════════════════════════════
    # REASONING (chain-of-thought)
    # ═══════════════════════════════════════════════════════════════════════════
    reasoning=True,                        # Enable reasoning mode
    reasoning_min_steps=5,                 # Minimum reasoning steps
    reasoning_max_steps=10,                # Maximum reasoning steps

    # ═══════════════════════════════════════════════════════════════════════════
    # DEBUGGING
    # ═══════════════════════════════════════════════════════════════════════════
    debug_mode=True,                       # Enable debug logging
    show_tool_calls=True,                  # Show tool calls in output
    cache_session=True,                    # Cache session in memory
)
```

---

## Updated Team Constructor Reference

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools

team = Team(
    name="Research Team",
    model=Claude(id="claude-sonnet-4-5"),
    members=[research_agent, analysis_agent, writer_agent],

    # ═══════════════════════════════════════════════════════════════════════════
    # DELEGATION BEHAVIOR (replaces "mode" parameter)
    # ═══════════════════════════════════════════════════════════════════════════
    respond_directly=False,              # False = synthesize, True = passthrough
    delegate_to_all_members=False,       # False = sequential, True = parallel
    determine_input_for_members=True,    # Leader synthesizes input for members

    # ═══════════════════════════════════════════════════════════════════════════
    # INSTRUCTIONS AND SUCCESS CRITERIA
    # ═══════════════════════════════════════════════════════════════════════════
    description="A research team that produces comprehensive reports",
    instructions=[
        "Always include sources",
        "Use tables for data presentation"
    ],
    success_criteria="Comprehensive report with actionable insights",

    # ═══════════════════════════════════════════════════════════════════════════
    # COMMUNICATION OPTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    show_members_responses=True,         # Show member responses in output
    share_member_interactions=True,      # Share interactions between members
    enable_agentic_context=True,         # Enable agentic context sharing

    # ═══════════════════════════════════════════════════════════════════════════
    # MEMORY AND HISTORY
    # ═══════════════════════════════════════════════════════════════════════════
    add_history_to_messages=True,
    num_history_runs=5,

    # ═══════════════════════════════════════════════════════════════════════════
    # TOOLS FOR TEAM LEADER
    # ═══════════════════════════════════════════════════════════════════════════
    tools=[ReasoningTools(add_instructions=True)],

    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY
    # ═══════════════════════════════════════════════════════════════════════════
    markdown=True,
    show_tool_calls=True,
)
```

---

## MCP Integration Patterns

### Basic MCP Tool Integration

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

async def main():
    async with MCPTools(
        transport="streamable-http",
        url="https://docs.agno.com/mcp"
    ) as mcp_tools:
        agent = Agent(
            model=Claude(id="claude-sonnet-4-5"),
            tools=[mcp_tools],
            markdown=True,
        )
        await agent.aprint_response("What tools are available?", stream=True)
```

### Stdio Transport for Local MCP Servers

```python
from agno.tools.mcp import MCPTools

async def neo4j_agent():
    env = {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "NEO4J_READ_ONLY": "true"
    }

    async with MCPTools(
        command="neo4j-mcp",
        env=env,
        timeout_seconds=60
    ) as mcp_tools:
        agent = Agent(
            name="Graph Database Agent",
            model=Claude(id="claude-sonnet-4-5"),
            tools=[mcp_tools],
            instructions=["You are a graph database assistant."],
        )
        await agent.aprint_response("Show me the database schema")
```

### Multiple MCP Servers

```python
from agno.tools.mcp import MultiMCPTools

async def multi_server_agent():
    mcp_servers = {
        "neo4j": {
            "command": "neo4j-mcp",
            "env": {"NEO4J_URI": "bolt://localhost:7687", ...}
        },
        "supabase": {
            "command": "supabase-mcp-server",
            "env": {"SUPABASE_PROJECT_REF": "your-project-ref", ...}
        },
    }

    async with MultiMCPTools(servers=mcp_servers) as tools:
        agent = Agent(
            model=Claude(id="claude-sonnet-4-5"),
            tools=[tools],
        )
        await agent.aprint_response("Query both databases")
```

---

## Mindrian Agent Archetype Templates (Updated)

### ROLE Agent Template (Larry the Clarifier)

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

# Memory configuration
memory_db = SqliteMemoryDb(
    table_name="larry_memories",
    db_file="tmp/mindrian.db"
)

memory = Memory(
    model=Claude(id="claude-sonnet-4-5"),
    db=memory_db,
    delete_memories=True,
    clear_memories=True,
)

larry_clarifier = Agent(
    name="Larry the Clarifier",
    id="larry-clarifier",
    role="Conversational assistant specializing in clarifying user intent",
    description="""You are Larry, a friendly and patient assistant who excels at:
    - Asking clarifying questions to understand user needs
    - Breaking down complex requests into manageable parts
    - Never assuming - always confirming understanding

    The Three Questions:
    1. WHAT is the actual problem?
    2. WHO has this problem?
    3. What does SUCCESS look like?""",

    model=Claude(
        id="claude-sonnet-4-20250514",
        thinking={
            "type": "enabled",
            "budget_tokens": 2000  # ROLE agents: 2,000 tokens
        }
    ),

    instructions=[
        "Keep responses under 100 words",
        "Ask ONE question at a time",
        "Always ask at least one clarifying question before proceeding",
        "Summarize your understanding before taking action",
        "Use warm, approachable language"
    ],

    db=SqliteDb(db_file="tmp/mindrian.db"),
    memory=memory,
    user_id="default_user",

    enable_user_memories=True,
    enable_agentic_memory=True,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=5,

    markdown=True,
)
```

### OPERATOR Agent Template (Framework Specialist)

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

async def create_minto_operator():
    async with MCPTools(
        command="neo4j-mcp",
        env={
            "NEO4J_URI": "bolt://localhost:7687",
            "NEO4J_USERNAME": "neo4j",
            "NEO4J_PASSWORD": "${NEO4J_PASSWORD}",
        }
    ) as neo4j_tools:

        minto_operator = Agent(
            name="Minto Pyramid Operator",
            id="minto-pyramid",
            role="Structure thinking using SCQA framework",
            description="""You apply the Minto Pyramid principle to structure problems:

            ## SCQA Framework
            - **Situation**: Current state (facts everyone agrees on)
            - **Complication**: What changed? Why action needed?
            - **Question**: What must we answer?
            - **Answer**: Recommendation with supporting arguments

            Always produce complete SCQA analysis.""",

            model=Claude(
                id="claude-sonnet-4-20250514",
                thinking={
                    "type": "enabled",
                    "budget_tokens": 8000  # OPERATOR agents: 8,000 tokens
                }
            ),

            tools=[neo4j_tools],

            instructions=[
                "Always produce structured SCQA output",
                "Include confidence scores for each section",
                "Cite sources from knowledge graph when available"
            ],

            show_tool_calls=True,
            markdown=True,
        )

        return minto_operator
```

### COLLABORATIVE Team Template (Analysis Team)

```python
from agno.team import Team
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools

technical_analyst = Agent(
    name="Technical Analyst",
    role="Analyze technical feasibility and implementation details",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Focus on technical constraints", "Identify implementation risks"],
)

business_analyst = Agent(
    name="Business Analyst",
    role="Analyze business value and market opportunity",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Focus on ROI and market fit", "Identify business risks"],
)

risk_analyst = Agent(
    name="Risk Analyst",
    role="Identify and assess risks across all dimensions",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Apply PWS validation framework", "Score risks by severity"],
)

analysis_team = Team(
    name="Multi-Perspective Analysis Team",
    model=Claude(
        id="claude-sonnet-4-5",
        thinking={
            "type": "enabled",
            "budget_tokens": 15000  # COLLABORATIVE: 15,000 tokens
        }
    ),
    members=[technical_analyst, business_analyst, risk_analyst],

    # Parallel execution (was mode="collaborate")
    delegate_to_all_members=True,

    instructions=[
        "Synthesize findings from all perspectives",
        "Highlight areas of agreement and disagreement",
        "Provide balanced recommendations"
    ],
    success_criteria="Comprehensive analysis with actionable recommendations",

    enable_agentic_context=True,
    show_members_responses=True,

    tools=[ReasoningTools(add_instructions=True)],
    markdown=True,
)
```

### PIPELINE Workflow Template

```python
from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.anthropic import Claude

research_agent = Agent(
    name="Researcher",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Gather comprehensive information"],
)

outline_agent = Agent(
    name="Outline Generator",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Create structured outline from research"],
)

writer_agent = Agent(
    name="Writer",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Write polished content from outline"],
)

editor_agent = Agent(
    name="Editor",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=["Review and improve content quality"],
)

# Deterministic pipeline (vs model-driven Team)
content_pipeline = Workflow(
    name="Content Production Pipeline",
    steps=[
        research_agent,      # Phase 1: Research
        outline_agent,       # Phase 2: Structure
        writer_agent,        # Phase 3: Draft
        editor_agent,        # Phase 4: Review
    ],
)

# Execute pipeline
content_pipeline.print_response("Create analysis of AI agent frameworks", markdown=True)
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Free-text handoffs** | Context loss | Structured JSON payloads with versioned schemas |
| **God agent** | Tries to do everything | Specialize by domain (ROLE, OPERATOR, etc.) |
| **Infinite loops** | Agents bounce endlessly | Set iteration limits, explicit termination |
| **Context flooding** | Everything to every agent | Scope by default, request via tools |
| **No checkpointing** | Can't recover from failures | Implement durable checkpoints |
| **Overlapping roles** | Conflicting outputs | Clear capability boundaries |
| **Missing termination** | Runaway behavior | Explicit success criteria |
| **Business logic in prompts** | Non-deterministic rules | Implement as code actions |

---

## Teams vs Workflows Decision Guide

| Feature | Teams | Workflows |
|---------|-------|-----------|
| **Control** | Model-driven delegation | Code-driven execution |
| **Best for** | Complex reasoning, collaboration | Sequential/parallel pipelines |
| **Execution** | Non-deterministic | Deterministic |
| **State** | Shared via context | Explicit `session_state` |
| **Use case** | Multi-domain assistants | ETL pipelines, content generation |

**Mindrian Mapping:**
- **Clarification Team** → Team (coordinate mode)
- **Analysis Team** → Team (collaborate mode)
- **Deep Research Pipeline** → Workflow (deterministic)
- **Content Pipeline** → Workflow (deterministic)

---

## Files to Update

Based on these changes, the following Mindrian files need updates:

1. `mindrian/teams/deep_research_team.py` - Fix Team mode parameter
2. `mindrian/agents/research/*.py` - Update agent_id → id parameter
3. `mindrian/config/settings.py` - Add memory configuration
4. `mindrian/handoff/manager.py` - Ensure structured handoffs

---

*Agno v2 Migration Guide v1.0 - Based on Swarm Architect Research*
