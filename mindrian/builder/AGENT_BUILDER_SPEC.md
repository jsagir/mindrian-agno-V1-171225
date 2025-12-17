# Mindrian Agent Builder Specification

> Unified specification for building intelligent agents in Mindrian.
> Combines: Mindrian Handoff Protocol + Agent Workflow Builder + Specification Schema

---

## Overview

The Mindrian Agent Builder is a **meta-agent factory** that transforms framework definitions (SKILL.md files) into complete, production-ready agents with:
- All required tools and MCP integrations
- Proper handoff protocol support (receive context, return results)
- Neo4j schema for framework selection intelligence
- Sub-agent coordination capabilities
- Quality validation and testing

---

## Core Concepts

### Agent Types (from Mindrian Ontology)

| Type | Description | Handoff Pattern | Example |
|------|-------------|-----------------|---------|
| `ROLE` | Conversational persona | TRANSFER, RETURN | Larry, Devil |
| `OPERATOR` | Single-purpose framework | DELEGATE, RETURN | Minto, PWS |
| `COLLABORATIVE` | Multi-agent coordination | DELEGATE parallel | De Bono Hats |
| `PIPELINE` | Sequential processing | DELEGATE sequential | Clarify-Analyze-Validate |
| `GUIDED` | Interactive step-by-step | DELEGATE/RETURN iterative | Canvas-style tools |

### Handoff Types (from Mindrian Protocol)

```python
class HandoffType(Enum):
    DELEGATE = "delegate"   # Assign work, expect results back
    TRANSFER = "transfer"   # Full control passes to agent
    RETURN = "return"       # Complete and return to caller
    ESCALATE = "escalate"   # Need human input
```

### Handoff Modes

```python
class HandoffMode(Enum):
    SEQUENTIAL = "sequential"   # A -> B -> C (each builds on previous)
    PARALLEL = "parallel"       # A + B + C (all work simultaneously)
    SELECTIVE = "selective"     # A OR B OR C (router chooses one)
    DEBATE = "debate"           # A vs B (opposing positions)
```

---

## Agent Specification Schema

### Complete Field Reference

```yaml
# ============================================================================
# AGENT IDENTITY
# ============================================================================
agent:
  name: string                    # Human-readable name (e.g., "Minto Pyramid")
  id: string                      # Machine identifier (e.g., "minto-pyramid")
  type: enum                      # ROLE | OPERATOR | COLLABORATIVE | PIPELINE | GUIDED
  version: semver                 # Semantic version (e.g., "1.0.0")
  description: string             # What this agent does (1-2 sentences)
  tags: [string]                  # Searchable tags

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
model:
  provider: enum                  # anthropic | google | openai
  id: string                      # Model ID (e.g., "claude-sonnet-4-20250514")
  temperature: float              # 0.0-1.0 (default: 0.7)
  max_tokens: int                 # Max output tokens
  thinking:                       # Extended thinking configuration
    enabled: bool                 # Enable extended thinking
    budget_tokens: int            # Max thinking tokens (0-10000)

# ============================================================================
# INSTRUCTIONS (Core Agent Behavior)
# ============================================================================
instructions:
  system: string                  # Base system prompt
  methodology: string             # Framework methodology (if OPERATOR)
  output_template: string         # Expected output format
  quality_criteria: [string]      # What makes output "good"
  behavioral_rules: [string]      # Constraints (if ROLE)
  tone: string                    # Communication style

# ============================================================================
# HANDOFF PROTOCOL (Mindrian Integration)
# ============================================================================
handoff:
  # What this agent receives
  receives:
    problem_clarity:              # From Larry's clarification
      what: bool                  # Requires problem definition
      who: bool                   # Requires stakeholder definition
      success: bool               # Requires success criteria
      min_clarity: float          # Minimum clarity score (0.0-1.0)

    previous_analyses: [string]   # Which prior frameworks to accept
    focus_areas: bool             # Accepts focus area constraints
    conversation_context: bool    # Needs conversation history

  # How this agent returns results
  returns:
    output_format: enum           # markdown | json | structured
    key_findings: bool            # Include key findings list
    recommendations: bool         # Include recommendations
    confidence_score: bool        # Include confidence (0.0-1.0)
    scores: [string]              # Named scores to return
    suggested_next: [string]      # Agents to suggest next
    open_questions: bool          # Questions remaining

  # Routing configuration
  routing:
    can_delegate_to: [string]     # Agents this can delegate to
    can_be_called_by: [string]    # Agents that can call this
    default_return_to: string     # Default return target
    return_behavior: enum         # SYNTHESIZE | PASSTHROUGH | ITERATE

  # Handoff type support
  supports:
    delegate: bool                # Can receive DELEGATE
    transfer: bool                # Can receive TRANSFER
    return: bool                  # Can send RETURN
    escalate: bool                # Can ESCALATE to human

# ============================================================================
# TOOLS & MCP INTEGRATION
# ============================================================================
tools:
  # MCP servers to connect
  mcp_servers:
    - server: string              # MCP server name (e.g., "neo4j", "pinecone")
      tools: [string]             # Specific tools to use (or "*" for all)
      required: bool              # Fail if unavailable?

  # Custom tools (Python functions)
  custom_tools:
    - name: string                # Tool name
      description: string         # What it does
      function: string            # Python function path
      parameters:                 # Parameter schema
        type: object
        properties: {}
        required: []

  # Global actions (available in all phases)
  global_actions:
    - action: string              # Action name
      description: string         # When to use
      tool: string                # Tool to invoke

# ============================================================================
# SUB-AGENTS (For COLLABORATIVE/PIPELINE types)
# ============================================================================
sub_agents:
  - id: string                    # Sub-agent ID
    role: string                  # Role in parent agent
    model: string                 # Model (can differ from parent)
    instructions: string          # Sub-agent instructions
    tools: [string]               # Tools available to sub-agent

# ============================================================================
# WORKFLOW PHASES (For complex agents)
# ============================================================================
phases:
  - id: string                    # Phase ID (e.g., "parse_input")
    name: string                  # Human name
    description: string           # What happens in this phase

    # Phase inputs/outputs
    inputs: [string]              # What this phase needs
    outputs: [string]             # What this phase produces

    # Validation
    checkpoint:
      criteria: [string]          # What must be true to proceed
      on_fail: enum               # retry | skip | abort | ask_user
      max_retries: int            # Retries before escalating

    # Phase-specific tools
    tools: [string]               # Tools available in this phase

# ============================================================================
# NEO4J SCHEMA (For framework selection intelligence)
# ============================================================================
neo4j:
  node_label: string              # e.g., "Framework"
  properties:
    - name: string                # Property name
      type: string                # Property type
      indexed: bool               # Create index?

  relationships:
    - type: string                # e.g., "CHAINS_TO", "GOOD_FOR"
      target_label: string        # Target node label
      properties: [string]        # Relationship properties

  # Cypher for self-registration
  register_cypher: string         # MERGE query to add to graph

# ============================================================================
# TRIGGERS & ACTIVATION
# ============================================================================
triggers:
  # Keyword triggers
  keywords: [string]              # Words that activate this agent

  # Context triggers (when to auto-activate)
  contexts:
    - condition: string           # Condition expression
      priority: int               # Priority when multiple match

  # Problem type mapping
  problem_types:
    - type: string                # un-defined | ill-defined | well-defined
      confidence: float           # Confidence for this type

# ============================================================================
# CHAINING & DEPENDENCIES
# ============================================================================
chaining:
  # What this agent should follow
  follows: [string]               # Agents that should run before

  # What should follow this agent
  precedes: [string]              # Agents that should run after

  # Alternatives
  alternatives: [string]          # Agents that solve similar problems

  # Enhances
  enhances: [string]              # Agents this adds value to

# ============================================================================
# VALIDATION & QUALITY
# ============================================================================
validation:
  # Input validation
  input_schema:                   # JSON Schema for inputs
    type: object
    properties: {}
    required: []

  # Output validation
  output_schema:                  # JSON Schema for outputs
    type: object
    properties: {}
    required: []

  # Quality gates
  quality_gates:
    - name: string                # Gate name
      check: string               # What to check
      threshold: float            # Minimum score
      action: enum                # warn | fail | retry

# ============================================================================
# MEMORY & STATE
# ============================================================================
memory:
  # Session memory (Agno built-in)
  session:
    enabled: bool                 # Enable session memory
    history_depth: int            # Messages to remember

  # Long-term memory (Supabase)
  supabase:
    enabled: bool                 # Enable Supabase memory
    table: string                 # Table name
    embedding_field: string       # Field for embeddings
    retrieval_top_k: int          # Results to retrieve

  # Graph memory (Neo4j)
  neo4j:
    enabled: bool                 # Enable Neo4j memory
    store_outputs: bool           # Store agent outputs
    store_decisions: bool         # Store routing decisions

# ============================================================================
# METADATA
# ============================================================================
metadata:
  author: string                  # Creator
  created: datetime               # Creation date
  modified: datetime              # Last modification
  source: string                  # Path to source SKILL.md
  documentation: string           # Link to docs
```

---

## Builder Workflow

The Agent Builder follows a **7-phase workflow**:

### Phase 1: SKILL Analysis

**Input:** SKILL.md file path or raw YAML
**Output:** Parsed SkillDefinition

```python
class Phase1_SkillAnalysis:
    """Parse and analyze source SKILL.md"""

    def execute(self, skill_path: str) -> SkillDefinition:
        # 1. Load SKILL.md
        # 2. Parse frontmatter (YAML)
        # 3. Extract sections (methodology, template, criteria)
        # 4. Validate required fields
        # 5. Return structured definition
```

**Checkpoint:**
- [ ] All required fields present
- [ ] Type is valid enum value
- [ ] Triggers defined
- [ ] Output format specified

### Phase 2: Agent Architecture

**Input:** SkillDefinition
**Output:** AgentSpec with type, model, tools

```python
class Phase2_Architecture:
    """Determine agent architecture"""

    def execute(self, skill: SkillDefinition) -> AgentSpec:
        # 1. Determine agent type (ROLE, OPERATOR, etc.)
        # 2. Select model based on complexity
        # 3. Identify required MCP servers
        # 4. Design sub-agent structure (if needed)
        # 5. Define handoff protocol
```

**Checkpoint:**
- [ ] Agent type determined
- [ ] Model selected
- [ ] Tools identified
- [ ] Handoff protocol defined

### Phase 3: Handoff Protocol Design

**Input:** AgentSpec, SkillDefinition
**Output:** Complete handoff configuration

```python
class Phase3_HandoffProtocol:
    """Design handoff integration"""

    def execute(self, spec: AgentSpec, skill: SkillDefinition) -> HandoffConfig:
        # 1. Define receives (ProblemClarity requirements)
        # 2. Define returns (output structure)
        # 3. Set routing (can_delegate_to, can_be_called_by)
        # 4. Configure return_behavior
        # 5. Map to HandoffManager patterns
```

**Checkpoint:**
- [ ] Receives matches HandoffContext fields
- [ ] Returns matches HandoffResult structure
- [ ] Routing is valid (agents exist)
- [ ] Return behavior appropriate for type

### Phase 4: Tool Assembly

**Input:** AgentSpec with tool requirements
**Output:** Complete tool configuration

```python
class Phase4_ToolAssembly:
    """Assemble tools from MCPs and custom functions"""

    def execute(self, spec: AgentSpec) -> ToolConfig:
        # 1. Connect to required MCP servers
        # 2. Create custom tool wrappers
        # 3. Define global actions
        # 4. Set phase-specific tool access
        # 5. Validate tool availability
```

**Checkpoint:**
- [ ] All MCP servers reachable
- [ ] Custom tools importable
- [ ] Global actions mapped
- [ ] No tool conflicts

### Phase 5: Neo4j Schema Generation

**Input:** AgentSpec, SkillDefinition
**Output:** Neo4j schema and Cypher queries

```python
class Phase5_Neo4jSchema:
    """Generate Neo4j schema for framework intelligence"""

    def execute(self, spec: AgentSpec, skill: SkillDefinition) -> Neo4jConfig:
        # 1. Define node label and properties
        # 2. Define relationships (CHAINS_TO, GOOD_FOR, etc.)
        # 3. Generate MERGE query for registration
        # 4. Generate selection queries
        # 5. Create index statements
```

**Cypher Templates:**

```cypher
// Register framework
MERGE (f:Framework {id: $id})
SET f.name = $name,
    f.type = $type,
    f.triggers = $triggers,
    f.problem_types = $problem_types,
    f.version = $version,
    f.updated_at = datetime()

// Create relationships
MATCH (f:Framework {id: $id})
MATCH (target:Framework {id: $chains_to})
MERGE (f)-[:CHAINS_TO {weight: $weight}]->(target)

// Framework selection query
MATCH (f:Framework)
WHERE ANY(t IN $triggers WHERE t IN f.triggers)
   OR ANY(pt IN $problem_types WHERE pt IN f.problem_types)
WITH f,
     CASE WHEN ANY(t IN $triggers WHERE t IN f.triggers) THEN 0.6 ELSE 0 END +
     CASE WHEN ANY(pt IN $problem_types WHERE pt IN f.problem_types) THEN 0.4 ELSE 0 END
     AS score
ORDER BY score DESC
LIMIT 5
RETURN f, score
```

**Checkpoint:**
- [ ] Node schema valid
- [ ] Relationships defined
- [ ] MERGE query generates
- [ ] Selection query works

### Phase 6: Code Generation

**Input:** Complete AgentSpec
**Output:** Python agent class, test file

```python
class Phase6_CodeGeneration:
    """Generate Python agent implementation"""

    def execute(self, spec: AgentSpec) -> GeneratedCode:
        # 1. Generate agent class
        # 2. Generate handoff methods
        # 3. Generate tool wrappers
        # 4. Generate test suite
        # 5. Generate __init__.py exports
```

**Generated Structure:**
```
mindrian/agents/{category}/{agent_id}/
├── __init__.py          # Exports
├── agent.py             # Main agent class
├── handoff.py           # Handoff protocol implementation
├── tools.py             # Custom tool definitions
├── schema.cypher        # Neo4j schema
└── tests/
    ├── test_agent.py    # Unit tests
    └── test_handoff.py  # Integration tests
```

**Checkpoint:**
- [ ] Agent class compiles
- [ ] Handoff methods match protocol
- [ ] Tests pass
- [ ] Imports resolve

### Phase 7: Registration & Validation

**Input:** Generated agent
**Output:** Registered, validated agent

```python
class Phase7_Registration:
    """Register agent and validate end-to-end"""

    def execute(self, agent_path: str) -> ValidationResult:
        # 1. Import generated agent
        # 2. Register with HandoffManager
        # 3. Register in Neo4j
        # 4. Run validation suite
        # 5. Generate documentation
```

**Checkpoint:**
- [ ] Agent imports successfully
- [ ] HandoffManager accepts registration
- [ ] Neo4j node created
- [ ] Sample handoff succeeds

---

## Generated Agent Template

```python
"""
{agent_name} - Auto-generated by Mindrian Agent Builder
Version: {version}
Type: {agent_type}
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from mindrian.handoff.context import HandoffContext, HandoffResult
from mindrian.handoff.types import HandoffType, HandoffMode, ReturnBehavior


{AGENT_INSTRUCTIONS}


class {AgentClassName}:
    """
    {description}

    Type: {agent_type}
    Handoff: receives {receives}, returns {returns}
    Tools: {tools}

    Usage:
        agent = {AgentClassName}()

        # Direct use
        result = await agent.run("Input message")

        # With handoff
        result = await agent.process_handoff(context)
    """

    def __init__(
        self,
        model: str = "{model_id}",
        enable_tools: bool = True,
    ):
        self._model = model
        self._db = SqliteDb(db_file="tmp/mindrian.db")

        # Build agent
        self._agent = Agent(
            name="{agent_name}",
            agent_id="{agent_id}",
            model=Claude(id=model),
            description="{description}",
            instructions={INSTRUCTIONS_VAR},
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    @property
    def agent(self) -> Agent:
        return self._agent

    async def run(self, message: str) -> str:
        """Direct execution"""
        response = await self._agent.arun(message)
        return response.content if hasattr(response, 'content') else str(response)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """
        Process handoff from orchestrator.

        Receives:
            - ProblemClarity (what, who, success)
            - Previous analyses
            - Task description

        Returns:
            - Structured output
            - Key findings
            - Recommendations
            - Suggested next agents
        """
        import time
        start_time = time.time()

        # Build prompt from handoff context
        prompt = self._build_handoff_prompt(context)

        try:
            response = await self._agent.arun(prompt)
            output = response.content if hasattr(response, 'content') else str(response)

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="{agent_id}",
                to_agent=context.return_to,
                success=True,
                output=output,
                key_findings={key_findings_extraction},
                recommendations={recommendations_extraction},
                confidence={confidence_score},
                scores={scores_dict},
                suggested_next_agents={suggested_next},
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="{agent_id}",
                to_agent=context.return_to,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def _build_handoff_prompt(self, context: HandoffContext) -> str:
        """Build prompt from handoff context"""
        sections = [context.to_prompt()]

        # Add previous analyses
        if context.previous_analyses:
            sections.append("\\n## Previous Analyses")
            for pa in context.previous_analyses:
                sections.append(f"### {pa.framework_name}\\n{pa.output[:1000]}...")

        # Add agent-specific instructions
        sections.append(f"""
## Your Task

Apply the {agent_name} methodology to this challenge.
Use the problem clarity provided (What/Who/Success).
Build on any previous analyses.

{task_specific_instructions}
""")

        return "\\n\\n".join(sections)

    def create_handoff_context(
        self,
        challenge: str,
        problem_clarity: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
    ) -> HandoffContext:
        """Create handoff context for this agent"""
        from mindrian.handoff.context import ProblemClarity, PreviousAnalysis
        import uuid

        clarity = ProblemClarity()
        if problem_clarity:
            clarity.what = problem_clarity.get("what", challenge)
            clarity.who = problem_clarity.get("who", "")
            clarity.success = problem_clarity.get("success", "")

        analyses = []
        if previous_analyses:
            for pa in previous_analyses:
                analyses.append(PreviousAnalysis(
                    framework_id=pa.get("framework_id", ""),
                    framework_name=pa.get("framework_name", ""),
                    output=pa.get("output", ""),
                    key_findings=pa.get("key_findings", []),
                ))

        return HandoffContext(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=clarity,
            previous_analyses=analyses,
            task_description=f"Apply {agent_name} to: {challenge}",
            expected_output="{expected_output}",
            from_agent="orchestrator",
            to_agent="{agent_id}",
            return_to="orchestrator",
            handoff_type=HandoffType.DELEGATE,
        )


# Neo4j registration query
NEO4J_REGISTER = """
MERGE (f:Framework {id: '{agent_id}'})
SET f.name = '{agent_name}',
    f.type = '{agent_type}',
    f.triggers = {triggers},
    f.problem_types = {problem_types},
    f.version = '{version}',
    f.updated_at = datetime()
"""
```

---

## Integration with HandoffManager

The generated agents integrate seamlessly with Mindrian's HandoffManager:

```python
from mindrian.handoff.manager import handoff_manager
from mindrian.agents.frameworks.minto_pyramid import MintoPyramidAgent

# 1. Create agent
minto = MintoPyramidAgent()

# 2. Register with HandoffManager
handoff_manager.register_agent("minto-pyramid", minto.agent)

# 3. Create delegation
context = handoff_manager.create_delegation(
    from_agent="larry",
    to_agent="minto-pyramid",
    task="Structure this problem using SCQA",
    problem_clarity={
        "what": "Customer churn is increasing",
        "who": "SaaS startup",
        "success": "Reduce churn to under 5%"
    }
)

# 4. Execute handoff
result = await handoff_manager.execute(context)

# 5. Result is a HandoffResult
print(result.output)           # Structured SCQA analysis
print(result.key_findings)     # Key findings list
print(result.suggested_next)   # ["pws-validation", "jtbd"]
```

---

## Quality Gates

Each generated agent must pass these quality gates:

### Gate 1: Schema Compliance
- [ ] All required fields present
- [ ] Types match schema
- [ ] Enums are valid values

### Gate 2: Handoff Protocol
- [ ] `process_handoff()` method exists
- [ ] Returns valid HandoffResult
- [ ] Handles errors gracefully

### Gate 3: Tool Integration
- [ ] All MCP tools reachable
- [ ] Custom tools callable
- [ ] No import errors

### Gate 4: Neo4j Registration
- [ ] Node creates successfully
- [ ] Relationships valid
- [ ] Selection query works

### Gate 5: End-to-End Test
- [ ] Sample handoff completes
- [ ] Output format correct
- [ ] Confidence reasonable

---

## Builder Meta-Agent

The Agent Builder itself is a meta-agent:

```yaml
agent:
  name: "Mindrian Agent Builder"
  id: "agent-builder"
  type: PIPELINE
  version: "1.0.0"
  description: "Transforms SKILL.md definitions into production-ready agents"

sub_agents:
  - id: skill-analyzer
    role: "Parse and validate SKILL.md"
  - id: architect
    role: "Design agent architecture"
  - id: handoff-designer
    role: "Configure handoff protocol"
  - id: tool-assembler
    role: "Assemble MCP and custom tools"
  - id: neo4j-generator
    role: "Generate Neo4j schema"
  - id: code-generator
    role: "Generate Python code"
  - id: validator
    role: "Validate and register agent"

phases:
  - id: skill_analysis
    sub_agent: skill-analyzer
    checkpoint: ["valid_yaml", "required_fields"]

  - id: architecture
    sub_agent: architect
    checkpoint: ["type_determined", "model_selected"]

  - id: handoff_protocol
    sub_agent: handoff-designer
    checkpoint: ["receives_defined", "returns_defined"]

  - id: tool_assembly
    sub_agent: tool-assembler
    checkpoint: ["mcps_connected", "tools_available"]

  - id: neo4j_schema
    sub_agent: neo4j-generator
    checkpoint: ["schema_valid", "queries_generated"]

  - id: code_generation
    sub_agent: code-generator
    checkpoint: ["compiles", "tests_pass"]

  - id: registration
    sub_agent: validator
    checkpoint: ["registered", "e2e_passes"]
```

---

## Usage Example

```python
from mindrian.builder import AgentBuilder

# Initialize builder
builder = AgentBuilder()

# Build from SKILL.md
agent_spec = await builder.build_from_skill(
    skill_path="/path/to/skills/operators/pws-validation/SKILL.md"
)

# Generated files
print(agent_spec.output_path)
# /home/jsagi/Mindrian/mindrian-agno/mindrian/agents/frameworks/pws_validation/

# Register and use
from mindrian.agents.frameworks.pws_validation import PWSValidationAgent

pws = PWSValidationAgent()
result = await pws.process_handoff(context)
```

---

## Appendix: Standard Capabilities

### Available MCP Tools

| MCP Server | Tools | Use Case |
|------------|-------|----------|
| `neo4j` | read_cypher, write_cypher, get_schema | Knowledge graph |
| `pinecone` | search_records, upsert_records | Vector search |
| `render` | list_services, get_metrics | Deployment |
| `n8n` | create_workflow, get_workflow | Automation |

### Standard Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `markdown` | Structured MD document | Reports, analyses |
| `json` | Structured JSON | API responses |
| `scqa` | Situation-Complication-Question-Answer | Minto |
| `scorecard` | 4-pillar scoring grid | PWS Validation |
| `matrix` | 2x2 or NxN grid | Scenario Analysis |

### Standard Scores

| Score | Range | Meaning |
|-------|-------|---------|
| `confidence` | 0.0-1.0 | Overall confidence |
| `clarity` | 0.0-1.0 | Problem clarity |
| `pillar_*` | 0-10 | PWS pillar scores |
| `csio_score` | 0-100 | Innovation potential |

---

*Generated by Mindrian Agent Builder v1.0.0*
