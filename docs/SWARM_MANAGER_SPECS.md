# Mindrian Swarm Manager Specifications

> Complete technical reference for building and deploying agents.

---

## 1. Agent Spec Schema

The **Agent Spec** is the canonical format that defines an agent. The Swarm Manager consumes this format to instantiate, configure, and coordinate agents.

### 1.1 Complete Schema (YAML)

```yaml
# ═══════════════════════════════════════════════════════════════════════════
# AGENT SPEC SCHEMA v1.0
# This is the exact format the Swarm Manager expects
# ═══════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────
# SECTION 1: IDENTITY
# Required fields that uniquely identify this agent
# ───────────────────────────────────────────────────────────────────────────
agent:
  id: string                      # REQUIRED: Unique identifier (kebab-case)
                                  # Example: "minto-pyramid", "larry-clarifier"
                                  # Used for: routing, Neo4j registration, imports

  name: string                    # REQUIRED: Human-readable name
                                  # Example: "Minto Pyramid", "Larry The Clarifier"
                                  # Used for: UI display, logs

  type: enum                      # REQUIRED: Agent type determines behavior patterns
                                  # Values:
                                  #   - "role"          → Conversational (talks to users)
                                  #   - "operator"      → Framework (processes inputs)
                                  #   - "collaborative" → Multi-agent (coordinates sub-agents)
                                  #   - "pipeline"      → Sequential (multi-phase processing)
                                  #   - "guided"        → Interactive (step-by-step with user)

  version: string                 # REQUIRED: Semantic version
                                  # Format: "MAJOR.MINOR.PATCH"
                                  # Example: "1.0.0", "2.1.3"

  description: string             # REQUIRED: One-line description
                                  # Example: "Structures problems using SCQA methodology"

  category: string                # REQUIRED: Deployment category
                                  # Values: "conversational", "frameworks", "research",
                                  #         "synthesis", "meta"
                                  # Determines: File path in agents/

  tags: [string]                  # OPTIONAL: Searchable tags
                                  # Example: ["strategy", "structuring", "communication"]

# ───────────────────────────────────────────────────────────────────────────
# SECTION 2: MODEL CONFIGURATION
# LLM settings for this agent
# ───────────────────────────────────────────────────────────────────────────
model:
  provider: enum                  # REQUIRED: Model provider
                                  # Values: "anthropic", "google", "openai"

  id: string                      # REQUIRED: Specific model ID
                                  # Examples:
                                  #   - "claude-sonnet-4-20250514"
                                  #   - "claude-opus-4-20250514"
                                  #   - "gemini-2.0-flash"

  temperature: float              # OPTIONAL: Randomness (0.0-1.0)
                                  # Default: 0.7
                                  # Lower = more deterministic
                                  # Higher = more creative

  max_tokens: int                 # OPTIONAL: Max output tokens
                                  # Default: 4096

  thinking:                       # OPTIONAL: Extended thinking config
    enabled: bool                 # Enable extended thinking
    budget_tokens: int            # Max thinking tokens (0-10000)

# ───────────────────────────────────────────────────────────────────────────
# SECTION 3: INSTRUCTIONS
# What the agent knows and how it behaves
# ───────────────────────────────────────────────────────────────────────────
instructions:
  system: string                  # REQUIRED: Base system prompt
                                  # This is the agent's "personality" and knowledge
                                  # Can be multi-line YAML string

  methodology: string             # CONDITIONAL: Required for type="operator"
                                  # The framework's step-by-step process
                                  # Example: "1. Situation\n2. Complication\n3. Question\n4. Answer"

  output_template: string         # OPTIONAL: Expected output format
                                  # Can include markdown templates

  quality_criteria:               # OPTIONAL: What makes output "good"
    - string                      # Example: "Must include all 4 SCQA elements"
    - string                      # Example: "Answer must be actionable"

  behavioral_rules:               # CONDITIONAL: Required for type="role"
    - string                      # Example: "Keep responses under 100 words"
    - string                      # Example: "Ask one question at a time"

  tone: string                    # OPTIONAL: Communication style
                                  # Example: "Direct but supportive"

# ───────────────────────────────────────────────────────────────────────────
# SECTION 4: HANDOFF PROTOCOL
# How this agent communicates with other agents
# ───────────────────────────────────────────────────────────────────────────
handoff:
  receives:                       # What this agent expects to receive
    problem_clarity:              # ProblemClarity requirements
      requires_what: bool         # Must have problem definition?
      requires_who: bool          # Must have stakeholder definition?
      requires_success: bool      # Must have success criteria?
      min_clarity: float          # Minimum overall clarity score (0.0-1.0)
                                  # Default: 0.3 for roles, 0.5 for operators

    accepts_previous: [string]    # Which prior analyses to accept
                                  # Example: ["minto-pyramid", "beautiful-question"]
                                  # Empty = accepts any

    accepts_focus_areas: bool     # Can receive focus constraints?
    accepts_conversation: bool    # Needs conversation history?

  returns:                        # What this agent returns
    output_format: enum           # Output type
                                  # Values: "markdown", "json", "scqa", "scorecard", "matrix"

    includes:                     # What's included in HandoffResult
      key_findings: bool          # List of key findings?
      recommendations: bool       # List of recommendations?
      confidence: bool            # Confidence score (0.0-1.0)?
      open_questions: bool        # Remaining questions?

    scores: [string]              # Named scores to return
                                  # Example: ["problem_score", "solution_score", "total_score"]

    suggests_next: [string]       # Agents to suggest after this one
                                  # Example: ["pws-validation", "jtbd"]

  routing:                        # How handoffs are routed
    can_delegate_to: [string]     # Agents this can delegate to
    can_be_called_by: [string]    # Agents that can call this
                                  # Use ["*"] for any agent

    default_return_to: string     # Where to return results
                                  # Default: "orchestrator"

    return_behavior: enum         # What happens after return
                                  # Values:
                                  #   - "synthesize"  → Orchestrator combines results
                                  #   - "passthrough" → Raw results to user
                                  #   - "iterate"     → Triggers another round

  supports:                       # Handoff types supported
    delegate: bool                # Can receive DELEGATE? (default: true)
    transfer: bool                # Can receive TRANSFER? (default: false)
    return: bool                  # Can send RETURN? (default: true)
    escalate: bool                # Can ESCALATE to human? (default: true)

# ───────────────────────────────────────────────────────────────────────────
# SECTION 5: TOOLS
# External capabilities available to this agent
# ───────────────────────────────────────────────────────────────────────────
tools:
  mcp_servers:                    # MCP server connections
    - server: string              # Server name (must match MCP config)
                                  # Available: "neo4j", "supabase", "render", "n8n"

      tools: [string]             # Specific tools from this server
                                  # Use ["*"] for all tools
                                  # Example: ["read_neo4j_cypher", "write_neo4j_cypher"]

      required: bool              # Fail if server unavailable?
                                  # Default: false

  custom:                         # Custom Python tools
    - name: string                # Tool name (used in function calls)
      description: string         # What this tool does
      module: string              # Python module path
      function: string            # Function name
      parameters:                 # JSON Schema for parameters
        type: object
        properties: {}
        required: []

  global_actions:                 # Actions available in all contexts
    - name: string                # Action name
      description: string         # When to use this action
      tool: string                # Tool to invoke (server.tool_name)
      auto_trigger: string        # OPTIONAL: Condition for auto-triggering

# ───────────────────────────────────────────────────────────────────────────
# SECTION 6: SUB-AGENTS
# For collaborative and pipeline types only
# ───────────────────────────────────────────────────────────────────────────
sub_agents:                       # CONDITIONAL: Required for collaborative/pipeline
  - id: string                    # Sub-agent identifier
    role: string                  # Role within parent agent
                                  # Example: "optimist", "pessimist", "analyst"

    model: string                 # OPTIONAL: Override parent model
    instructions: string          # Sub-agent specific instructions
    tools: [string]               # Tools available to this sub-agent

  coordination:                   # How sub-agents work together
    mode: enum                    # Coordination mode
                                  # Values:
                                  #   - "parallel"   → All run simultaneously
                                  #   - "sequential" → One after another
                                  #   - "debate"     → Opposing positions
                                  #   - "vote"       → Each votes on outcome

    synthesis: string             # How to combine outputs
                                  # Values: "merge", "select_best", "consensus"

# ───────────────────────────────────────────────────────────────────────────
# SECTION 7: WORKFLOW PHASES
# For pipeline types only
# ───────────────────────────────────────────────────────────────────────────
phases:                           # CONDITIONAL: Required for type="pipeline"
  - id: string                    # Phase identifier
    name: string                  # Human-readable name
    description: string           # What happens in this phase

    inputs: [string]              # What this phase needs
    outputs: [string]             # What this phase produces

    agent: string                 # OPTIONAL: Sub-agent for this phase
    tools: [string]               # Tools available in this phase

    checkpoint:                   # Validation before proceeding
      criteria: [string]          # Conditions that must be true
      on_fail: enum               # What to do on failure
                                  # Values: "retry", "skip", "abort", "ask_user"
      max_retries: int            # Max retries before escalating

# ───────────────────────────────────────────────────────────────────────────
# SECTION 8: TRIGGERS
# When this agent should be activated
# ───────────────────────────────────────────────────────────────────────────
triggers:
  keywords: [string]              # Words that activate this agent
                                  # Example: ["structure", "organize", "scqa", "pyramid"]

  problem_types:                  # Problem type mapping
    - type: string                # Problem type
                                  # Values: "un-defined", "ill-defined", "well-defined"
      confidence: float           # Confidence for this type (0.0-1.0)

  contexts:                       # Context-based triggers
    - condition: string           # Condition expression
                                  # Example: "problem_clarity.what_clarity > 0.7"
      priority: int               # Priority when multiple match

# ───────────────────────────────────────────────────────────────────────────
# SECTION 9: CHAINING
# Relationships to other agents
# ───────────────────────────────────────────────────────────────────────────
chaining:
  follows: [string]               # Agents that should run BEFORE this
                                  # Example: ["larry-clarifier", "beautiful-question"]

  precedes: [string]              # Agents that should run AFTER this
                                  # Example: ["pws-validation", "devil-advocate"]

  alternatives: [string]          # Agents that solve similar problems
                                  # Used for: suggestions, fallbacks

  enhances: [string]              # Agents this adds value to
                                  # Used for: combo recommendations

# ───────────────────────────────────────────────────────────────────────────
# SECTION 10: NEO4J REGISTRATION
# How this agent appears in the knowledge graph
# ───────────────────────────────────────────────────────────────────────────
neo4j:
  node_label: string              # Neo4j node label (default: "Framework")

  properties:                     # Additional node properties
    - name: string
      type: string                # "string", "int", "float", "list", "datetime"
      indexed: bool               # Create index?

  relationships:                  # Relationships to create
    - type: string                # Relationship type (e.g., "CHAINS_TO")
      target: string              # Target agent ID or label
      properties: {}              # Relationship properties

# ───────────────────────────────────────────────────────────────────────────
# SECTION 11: MEMORY
# How this agent remembers things
# ───────────────────────────────────────────────────────────────────────────
memory:
  session:                        # Within-conversation memory
    enabled: bool                 # Enable session memory
    history_depth: int            # How many turns to remember

  supabase:                       # Long-term conversation memory
    enabled: bool                 # Enable Supabase storage
    table: string                 # Table name
    retrieval_top_k: int          # Results to retrieve for RAG

  neo4j:                          # Graph memory
    enabled: bool                 # Enable Neo4j storage
    store_outputs: bool           # Store agent outputs
    store_decisions: bool         # Store routing decisions

# ───────────────────────────────────────────────────────────────────────────
# SECTION 12: DEPLOYMENT
# How and where this agent is deployed
# ───────────────────────────────────────────────────────────────────────────
deployment:
  auto_register: bool             # Register on startup? (default: true)
  lazy_load: bool                 # Load on first use? (default: true)
  singleton: bool                 # Single instance? (default: false)

  resources:                      # Resource requirements
    max_concurrent: int           # Max concurrent executions
    timeout_seconds: int          # Execution timeout
    token_budget: int             # Max tokens per execution

# ───────────────────────────────────────────────────────────────────────────
# SECTION 13: METADATA
# Administrative information
# ───────────────────────────────────────────────────────────────────────────
metadata:
  author: string                  # Creator
  created: datetime               # Creation timestamp
  modified: datetime              # Last modification
  source: string                  # Path to source SKILL.md (if built from one)
  documentation: string           # Link to documentation
```

### 1.2 Minimal Valid Spec (Required Fields Only)

```yaml
agent:
  id: "my-agent"
  name: "My Agent"
  type: "operator"
  version: "1.0.0"
  description: "Does something useful"
  category: "frameworks"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"

instructions:
  system: |
    You are an agent that does something useful.
    Follow these steps...

handoff:
  receives:
    problem_clarity:
      requires_what: true
      min_clarity: 0.3
  returns:
    output_format: "markdown"
    includes:
      key_findings: true
```

### 1.3 Python Dataclass Equivalent

```python
# This is what the YAML becomes in Python

@dataclass
class AgentSpec:
    # Identity (Required)
    id: str
    name: str
    type: AgentType  # Enum
    version: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)

    # Model (Required)
    model: ModelConfig

    # Instructions (Required)
    instructions: InstructionsConfig

    # Handoff (Required)
    handoff: HandoffConfig

    # Tools (Optional)
    tools: ToolConfig = field(default_factory=ToolConfig)

    # Sub-agents (For collaborative/pipeline)
    sub_agents: List[SubAgentConfig] = field(default_factory=list)

    # Phases (For pipeline)
    phases: List[PhaseConfig] = field(default_factory=list)

    # Triggers (Optional)
    triggers: TriggerConfig = field(default_factory=TriggerConfig)

    # Chaining (Optional)
    chaining: ChainingConfig = field(default_factory=ChainingConfig)

    # Neo4j (Optional)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)

    # Memory (Optional)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    # Deployment (Optional)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)

    # Metadata (Optional)
    metadata: MetadataConfig = field(default_factory=MetadataConfig)
```

---

## 2. Agent Builder Logic

The **Agent Builder** transforms source definitions (SKILL.md or AgentSpec YAML) into deployable Python code.

### 2.1 Transformation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT BUILDER PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT                           OUTPUT                                      │
│  ─────                           ──────                                      │
│                                                                              │
│  ┌──────────────┐               ┌──────────────────────────────────────┐    │
│  │  SKILL.md    │               │  agents/{category}/{agent_id}/       │    │
│  │  (Markdown)  │               │  ├── __init__.py                     │    │
│  └──────┬───────┘               │  ├── agent.py      (Main class)      │    │
│         │                       │  ├── spec.yaml     (Frozen spec)     │    │
│         ▼                       │  ├── schema.cypher (Neo4j schema)    │    │
│  ┌──────────────┐               │  └── tests/                          │    │
│  │  AgentSpec   │──────────────►│      └── test_agent.py               │    │
│  │  (YAML)      │               └──────────────────────────────────────┘    │
│  └──────────────┘                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Phase-by-Phase Transformation

```python
# The 7 phases of agent building

class AgentBuilder:
    """
    Transforms AgentSpec → Deployable Agent
    """

    def build(self, source: str | AgentSpec) -> BuildResult:
        """
        Main entry point.

        Args:
            source: Path to SKILL.md, YAML content, or AgentSpec object

        Returns:
            BuildResult with generated files
        """

        # PHASE 1: PARSE
        # ─────────────────────────────────────────────────────────────
        # Input:  SKILL.md path or raw content
        # Output: SkillDefinition (parsed frontmatter + body)
        # Logic:
        #   - Extract YAML frontmatter between --- markers
        #   - Parse methodology section
        #   - Extract output template
        #   - Extract quality criteria
        skill = self._parse_skill(source)

        # PHASE 2: ARCHITECTURE
        # ─────────────────────────────────────────────────────────────
        # Input:  SkillDefinition
        # Output: AgentSpec (partial - identity + model)
        # Logic:
        #   - Map skill.type → AgentType enum
        #   - Select model based on complexity
        #   - Generate agent ID from name
        #   - Set category based on type
        spec = self._design_architecture(skill)

        # PHASE 3: HANDOFF PROTOCOL
        # ─────────────────────────────────────────────────────────────
        # Input:  AgentSpec (partial)
        # Output: AgentSpec with handoff config
        # Logic:
        #   - Determine receives requirements from type
        #   - Determine returns format from outputs
        #   - Set routing based on chaining
        #   - Configure supported handoff types
        spec = self._configure_handoff(spec, skill)

        # PHASE 4: TOOL ASSEMBLY
        # ─────────────────────────────────────────────────────────────
        # Input:  AgentSpec
        # Output: AgentSpec with tools config
        # Logic:
        #   - Always add Neo4j (for framework registration)
        #   - Add Supabase if memory enabled
        #   - Add custom tools from skill
        #   - Define global actions
        spec = self._assemble_tools(spec, skill)

        # PHASE 5: NEO4J SCHEMA
        # ─────────────────────────────────────────────────────────────
        # Input:  AgentSpec
        # Output: AgentSpec with neo4j config + cypher
        # Logic:
        #   - Define node properties
        #   - Define relationships (CHAINS_TO, GOOD_FOR, etc.)
        #   - Generate MERGE query for registration
        #   - Generate selection query
        spec = self._generate_neo4j_schema(spec)

        # PHASE 6: CODE GENERATION
        # ─────────────────────────────────────────────────────────────
        # Input:  Complete AgentSpec
        # Output: Dict of filename → code content
        # Logic:
        #   - Generate agent.py from template
        #   - Generate __init__.py
        #   - Generate spec.yaml (frozen)
        #   - Generate schema.cypher
        #   - Generate test_agent.py
        code_files = self._generate_code(spec)

        # PHASE 7: REGISTRATION
        # ─────────────────────────────────────────────────────────────
        # Input:  Code files + AgentSpec
        # Output: BuildResult
        # Logic:
        #   - Write files to disk
        #   - Import and validate agent
        #   - Register in Neo4j
        #   - Run basic tests
        result = self._register_agent(spec, code_files)

        return result
```

### 2.3 Code Generation Templates

```python
# Template for agent.py

AGENT_TEMPLATE = '''
"""
{name} Agent
Auto-generated by Mindrian Agent Builder

Type: {type}
Version: {version}
"""

from typing import Optional, List, Dict, Any
import time

from agno.agent import Agent
from agno.models.anthropic import Claude

from mindrian.handoff.context import HandoffContext, HandoffResult
from mindrian.handoff.types import HandoffType


# Agent Instructions
INSTRUCTIONS = """
{instructions}
"""


class {class_name}:
    """
    {description}

    Handoff Protocol:
        Receives: {receives_summary}
        Returns: {returns_summary}

    Usage:
        agent = {class_name}()
        result = await agent.run("input")
        # or
        result = await agent.process_handoff(context)
    """

    def __init__(self, model: str = "{model_id}"):
        self._agent = Agent(
            name="{name}",
            agent_id="{id}",
            model=Claude(id=model),
            instructions=INSTRUCTIONS,
            markdown=True,
        )

    @property
    def agent(self) -> Agent:
        """Underlying Agno agent"""
        return self._agent

    @property
    def spec(self) -> dict:
        """Agent specification"""
        return {spec_dict}

    async def run(self, message: str) -> str:
        """Direct execution without handoff"""
        response = await self._agent.arun(message)
        return response.content if hasattr(response, "content") else str(response)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """Process handoff from orchestrator"""
        start_time = time.time()

        # Validate receives requirements
        {validation_code}

        # Build prompt from context
        prompt = self._build_prompt(context)

        try:
            response = await self._agent.arun(prompt)
            output = response.content if hasattr(response, "content") else str(response)

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="{id}",
                to_agent=context.return_to,
                success=True,
                output=output,
                output_format="{output_format}",
                key_findings=self._extract_findings(output),
                recommendations=self._extract_recommendations(output),
                confidence={confidence},
                scores={scores},
                suggested_next_agents={suggests_next},
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="{id}",
                to_agent=context.return_to,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def _build_prompt(self, context: HandoffContext) -> str:
        """Build prompt from handoff context"""
        sections = [context.to_prompt()]

        # Add previous analyses
        if context.previous_analyses:
            sections.append("\\n## Previous Analyses")
            for pa in context.previous_analyses:
                sections.append(f"### {{pa.framework_name}}\\n{{pa.output[:1500]}}...")

        # Add task-specific instructions
        sections.append("""
## Your Task
{task_instructions}
""")
        return "\\n\\n".join(sections)

    def _extract_findings(self, output: str) -> List[str]:
        """Extract key findings from output"""
        # Implementation depends on output format
        return {findings_extraction}

    def _extract_recommendations(self, output: str) -> List[str]:
        """Extract recommendations from output"""
        return {recommendations_extraction}
'''
```

### 2.4 Build Result Structure

```python
@dataclass
class BuildResult:
    """What the builder returns"""

    success: bool                           # Did build complete?
    spec: AgentSpec                         # Final specification
    output_path: str                        # Where files were written

    files: Dict[str, str]                   # filename → content
    # Example:
    # {
    #     "agent.py": "...",
    #     "__init__.py": "...",
    #     "spec.yaml": "...",
    #     "schema.cypher": "...",
    #     "tests/test_agent.py": "..."
    # }

    neo4j_registered: bool                  # Registered in graph?
    neo4j_cypher: str                       # Registration query used

    errors: List[str]                       # Build errors
    warnings: List[str]                     # Build warnings

    duration_seconds: float                 # Build time
```

---

## 3. Tool Integration Layer

How agents connect to external capabilities (MCPs, APIs, custom functions).

### 3.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TOOL INTEGRATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         AGENT                                        │    │
│  │                           │                                          │    │
│  │                           │ calls                                    │    │
│  │                           ▼                                          │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                    TOOL ROUTER                               │    │    │
│  │  │  Decides: MCP tool? Custom tool? Global action?              │    │    │
│  │  └────────────────────────┬────────────────────────────────────┘    │    │
│  │                           │                                          │    │
│  │         ┌─────────────────┼─────────────────┐                       │    │
│  │         ▼                 ▼                 ▼                        │    │
│  │  ┌────────────┐   ┌────────────┐   ┌────────────┐                  │    │
│  │  │ MCP Tools  │   │Custom Tools│   │Global Acts │                  │    │
│  │  └─────┬──────┘   └─────┬──────┘   └─────┬──────┘                  │    │
│  │        │                │                │                          │    │
│  └────────┼────────────────┼────────────────┼──────────────────────────┘    │
│           │                │                │                                │
│           ▼                ▼                ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       MCP MANAGER                                    │    │
│  │  Maintains connections to MCP servers                               │    │
│  │  Translates tool calls → MCP protocol                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       MCP SERVERS                                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │    │
│  │  │  Neo4j   │  │ Supabase │  │  Render  │  │   n8n    │            │    │
│  │  │   MCP    │  │   MCP    │  │   MCP    │  │   MCP    │            │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 MCP Tool Configuration

```yaml
# In .claude.json or mcp_config.yaml

mcp_servers:
  neo4j:
    command: "npx"
    args: ["-y", "@anthropics/mcp-neo4j"]
    env:
      NEO4J_URI: "${NEO4J_URI}"
      NEO4J_USER: "${NEO4J_USER}"
      NEO4J_PASSWORD: "${NEO4J_PASSWORD}"
    tools:
      - read_neo4j_cypher    # Execute read queries
      - write_neo4j_cypher   # Execute write queries
      - get_neo4j_schema     # Get graph schema

  supabase:
    command: "npx"
    args: ["-y", "@anthropics/mcp-supabase"]
    env:
      SUPABASE_URL: "${SUPABASE_URL}"
      SUPABASE_KEY: "${SUPABASE_KEY}"
    tools:
      - query               # Execute SQL
      - insert              # Insert rows
      - update              # Update rows
      - rpc                 # Call functions

  render:
    command: "npx"
    args: ["-y", "@anthropics/mcp-render"]
    env:
      RENDER_API_KEY: "${RENDER_API_KEY}"
    tools:
      - list_services
      - get_service
      - list_deploys
      - get_metrics

  n8n:
    command: "npx"
    args: ["-y", "@anthropics/mcp-n8n"]
    env:
      N8N_URL: "${N8N_URL}"
      N8N_API_KEY: "${N8N_API_KEY}"
    tools:
      - create_workflow
      - get_workflow
      - validate_workflow
      - execute_workflow
```

### 3.3 Tool Integration Code

```python
# mindrian/tools/mcp_manager.py

from typing import Dict, List, Any, Callable
from dataclasses import dataclass


@dataclass
class MCPTool:
    """Represents an MCP tool"""
    server: str           # MCP server name
    name: str             # Tool name
    description: str      # What it does
    parameters: dict      # JSON Schema


class MCPManager:
    """
    Manages MCP server connections and tool invocations.
    """

    def __init__(self, config_path: str = ".claude.json"):
        self._config = self._load_config(config_path)
        self._connections: Dict[str, Any] = {}
        self._tools: Dict[str, MCPTool] = {}

    def connect(self, server_name: str) -> bool:
        """Connect to an MCP server"""
        if server_name in self._connections:
            return True

        config = self._config.get("mcp_servers", {}).get(server_name)
        if not config:
            raise ValueError(f"Unknown MCP server: {server_name}")

        # Connection happens via Claude's MCP protocol
        # The actual connection is managed by Claude Code
        self._connections[server_name] = True
        return True

    def get_tools(self, server_name: str) -> List[MCPTool]:
        """Get available tools from a server"""
        # Tools are discovered via MCP protocol
        pass

    def invoke(self, server: str, tool: str, **params) -> Any:
        """
        Invoke an MCP tool.

        This is called by agents when they need external data.
        """
        # Format: mcp__{server}__{tool}
        # Example: mcp__neo4j__read_neo4j_cypher

        tool_name = f"mcp__{server}__{tool}"

        # The actual invocation happens via Agno's tool system
        # which delegates to Claude's MCP protocol
        pass

    def create_tool_functions(self, tools_config: List[dict]) -> Dict[str, Callable]:
        """
        Create callable functions for MCP tools.

        Used by agents to get tools they can call.
        """
        functions = {}

        for tool_cfg in tools_config:
            server = tool_cfg["server"]
            tool_names = tool_cfg.get("tools", ["*"])

            if tool_names == ["*"]:
                # Get all tools from server
                tool_names = [t.name for t in self.get_tools(server)]

            for tool_name in tool_names:
                func_name = f"{server}_{tool_name}"

                # Create wrapper function
                def make_wrapper(s, t):
                    async def wrapper(**params):
                        return await self.invoke(s, t, **params)
                    wrapper.__name__ = f"{s}_{t}"
                    wrapper.__doc__ = f"Invoke {t} on {s} MCP server"
                    return wrapper

                functions[func_name] = make_wrapper(server, tool_name)

        return functions
```

### 3.4 Custom Tool Definition

```python
# mindrian/tools/custom/insight_store.py

from typing import Dict, Any


def store_insight(
    content: str,
    insight_type: str,
    source_agent: str,
    confidence: float,
    session_id: str,
) -> Dict[str, Any]:
    """
    Store an insight in Neo4j.

    This is a custom tool that wraps Neo4j MCP calls.

    Args:
        content: The insight text
        insight_type: Type of insight (finding, recommendation, question)
        source_agent: Agent that generated it
        confidence: Confidence score (0.0-1.0)
        session_id: Current session ID

    Returns:
        Dict with insight ID and status
    """
    from mindrian.tools.mcp_manager import mcp_manager

    cypher = """
    CREATE (i:Insight {
        id: randomUUID(),
        content: $content,
        type: $type,
        source: $source,
        confidence: $confidence,
        created_at: datetime()
    })
    WITH i
    MATCH (s:Session {id: $session_id})
    CREATE (i)-[:DISCOVERED_IN]->(s)
    RETURN i.id AS id
    """

    result = mcp_manager.invoke(
        "neo4j",
        "write_neo4j_cypher",
        query=cypher,
        params={
            "content": content,
            "type": insight_type,
            "source": source_agent,
            "confidence": confidence,
            "session_id": session_id,
        }
    )

    return {"id": result[0]["id"], "status": "stored"}


# Tool registration
CUSTOM_TOOLS = [
    {
        "name": "store_insight",
        "description": "Store an insight in the knowledge graph",
        "module": "mindrian.tools.custom.insight_store",
        "function": "store_insight",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Insight text"},
                "insight_type": {"type": "string", "enum": ["finding", "recommendation", "question"]},
                "source_agent": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "session_id": {"type": "string"},
            },
            "required": ["content", "insight_type", "source_agent", "confidence", "session_id"]
        }
    }
]
```

### 3.5 How Agents Get Tools

```python
# In agent initialization

class MyAgent:
    def __init__(self, spec: AgentSpec):
        # 1. Get MCP tools
        mcp_tools = []
        for mcp_cfg in spec.tools.mcp_servers:
            tools = mcp_manager.create_tool_functions([mcp_cfg])
            mcp_tools.extend(tools.values())

        # 2. Get custom tools
        custom_tools = []
        for tool_cfg in spec.tools.custom:
            module = importlib.import_module(tool_cfg["module"])
            func = getattr(module, tool_cfg["function"])
            custom_tools.append(func)

        # 3. Combine all tools
        all_tools = mcp_tools + custom_tools

        # 4. Create Agno agent with tools
        self._agent = Agent(
            name=spec.name,
            model=Claude(id=spec.model.id),
            instructions=spec.instructions.system,
            tools=all_tools,  # Agent can now call these
        )
```

---

## 4. Handoff Protocol Definitions

Complete specification of state transfer between agents.

### 4.1 Core Types

```python
# mindrian/handoff/types.py

from enum import Enum


class HandoffType(str, Enum):
    """
    Type of handoff between agents.

    DELEGATE: "Do this task and return results to me"
        - Sender maintains control
        - Expects results back
        - Most common pattern

    TRANSFER: "Take over the conversation"
        - Receiver takes full control
        - User talks to new agent
        - Sender exits

    RETURN: "Here are my results"
        - Task complete
        - Returning to caller
        - Includes results

    ESCALATE: "I need help"
        - Can't complete task
        - Needs human input
        - Includes blocker explanation
    """
    DELEGATE = "delegate"
    TRANSFER = "transfer"
    RETURN = "return"
    ESCALATE = "escalate"


class HandoffMode(str, Enum):
    """
    How work is distributed when delegating.

    SEQUENTIAL: A → B → C
        - Each agent builds on previous
        - Output of A is input to B
        - Order matters

    PARALLEL: A + B + C
        - All work simultaneously
        - Same input to all
        - Results combined

    SELECTIVE: A OR B OR C
        - Router chooses one
        - Based on problem type
        - Others not invoked

    DEBATE: A vs B
        - Opposing positions
        - Multiple rounds
        - Synthesis resolves
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SELECTIVE = "selective"
    DEBATE = "debate"


class ReturnBehavior(str, Enum):
    """
    What happens when results come back.

    SYNTHESIZE: Orchestrator interprets
        - Combines multiple results
        - Adds context
        - Formats for user

    PASSTHROUGH: Raw results
        - Direct to user
        - No interpretation
        - For structured outputs

    ITERATE: Another round
        - Results trigger new delegation
        - Continues until done
        - For exploratory work
    """
    SYNTHESIZE = "synthesize"
    PASSTHROUGH = "passthrough"
    ITERATE = "iterate"
```

### 4.2 Context Structure

```python
# mindrian/handoff/context.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ProblemClarity:
    """
    Larry's assessment of problem understanding.

    This is THE foundation for all downstream work.
    Every handoff includes this.
    """

    # The Three Questions (from Larry)
    what: Optional[str] = None      # What is the actual problem?
    who: Optional[str] = None       # Who has this problem?
    success: Optional[str] = None   # What does success look like?

    # Clarity scores (0.0 = unknown, 1.0 = crystal clear)
    what_clarity: float = 0.0
    who_clarity: float = 0.0
    success_clarity: float = 0.0

    # Additional context
    assumptions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    @property
    def overall_clarity(self) -> float:
        """Average clarity across all dimensions"""
        return (self.what_clarity + self.who_clarity + self.success_clarity) / 3

    @property
    def is_ready_for_analysis(self) -> bool:
        """Can we proceed to framework analysis?"""
        return self.overall_clarity >= 0.6


@dataclass
class PreviousAnalysis:
    """
    Output from a previously run agent.

    Used to build on prior work.
    """
    framework_id: str           # Agent that produced this
    framework_name: str         # Human-readable name
    output: str                 # The actual output
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationSummary:
    """
    Compressed conversation history.

    We don't pass full history - we pass RELEVANT history.
    """
    key_points: List[str] = field(default_factory=list)
    user_goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    turn_count: int = 0


@dataclass
class HandoffContext:
    """
    THE COMPLETE CONTEXT FOR A HANDOFF.

    This is what travels from one agent to another.
    Everything an agent needs to do its job.
    """

    # ═══ IDENTITY ═══
    handoff_id: str                         # Unique tracking ID
    timestamp: datetime = field(default_factory=datetime.now)

    # ═══ PROBLEM DEFINITION ═══
    problem_clarity: ProblemClarity = field(default_factory=ProblemClarity)

    # ═══ CONVERSATION STATE ═══
    conversation: ConversationSummary = field(default_factory=ConversationSummary)
    session_id: Optional[str] = None

    # ═══ PREVIOUS WORK ═══
    previous_analyses: List[PreviousAnalysis] = field(default_factory=list)

    # ═══ TASK INSTRUCTIONS ═══
    task_description: str = ""              # What to do
    expected_output: str = ""               # What format
    focus_areas: List[str] = field(default_factory=list)
    ignore_areas: List[str] = field(default_factory=list)

    # ═══ ROUTING ═══
    from_agent: str = ""                    # Sender
    to_agent: str = ""                      # Receiver
    return_to: str = ""                     # Where results go
    return_behavior: ReturnBehavior = ReturnBehavior.SYNTHESIZE

    # ═══ HANDOFF TYPE ═══
    handoff_type: HandoffType = HandoffType.DELEGATE
    handoff_mode: HandoffMode = HandoffMode.SEQUENTIAL
    priority: int = 1                       # 1=normal, 2=high, 3=urgent
    timeout_seconds: int = 300

    # ═══ CUSTOM DATA ═══
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt(self) -> str:
        """
        Generate prompt for receiving agent.

        This is what the agent sees.
        """
        sections = []

        # Header
        sections.append(f"# Handoff from {self.from_agent}")
        sections.append(f"*ID: {self.handoff_id}*\n")

        # Task
        sections.append("## Your Task")
        sections.append(self.task_description)
        if self.expected_output:
            sections.append(f"\n**Expected Output:** {self.expected_output}")

        # Problem clarity
        sections.append("\n" + self.problem_clarity.to_prompt())

        # Previous work
        if self.previous_analyses:
            sections.append("\n## Previous Analyses")
            for pa in self.previous_analyses:
                sections.append(f"\n### {pa.framework_name}")
                sections.append(f"*Confidence: {pa.confidence:.0%}*\n")
                if pa.key_findings:
                    sections.append("**Findings:**")
                    for f in pa.key_findings:
                        sections.append(f"- {f}")
                sections.append(f"\n{pa.output[:1500]}...")

        # Focus
        if self.focus_areas:
            sections.append("\n## Focus On")
            for f in self.focus_areas:
                sections.append(f"- {f}")

        # Return instructions
        sections.append(f"\n---\n*Return to: {self.return_to}*")

        return "\n".join(sections)


@dataclass
class HandoffResult:
    """
    What comes back from a completed handoff.

    Structured output for synthesis and chaining.
    """

    # ═══ IDENTITY ═══
    handoff_id: str                         # Matches original
    from_agent: str                         # Who did the work
    to_agent: str                           # Who receives results

    # ═══ STATUS ═══
    success: bool = True
    error: Optional[str] = None

    # ═══ OUTPUT ═══
    output: str = ""                        # Main content
    output_format: str = "markdown"

    # ═══ STRUCTURED DATA ═══
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    scores: Dict[str, float] = field(default_factory=dict)

    # ═══ FOLLOW-UP ═══
    suggested_next_agents: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    needs_human_input: bool = False
    human_input_reason: str = ""

    # ═══ METADATA ═══
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_analysis(self) -> PreviousAnalysis:
        """Convert to PreviousAnalysis for chaining"""
        return PreviousAnalysis(
            framework_id=self.from_agent,
            framework_name=self.from_agent,
            output=self.output,
            key_findings=self.key_findings,
            recommendations=self.recommendations,
            confidence=self.confidence,
        )
```

### 4.3 Handoff Manager

```python
# mindrian/handoff/manager.py

class HandoffManager:
    """
    Central coordinator for all agent handoffs.

    Responsibilities:
    1. Create handoff contexts
    2. Execute handoffs
    3. Track history
    4. Handle errors
    5. Synthesize results
    """

    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._active: Dict[str, HandoffContext] = {}
        self._history: List[HandoffResult] = []

    # ═══ AGENT REGISTRATION ═══

    def register(self, agent_id: str, agent: Agent):
        """Register an agent for handoffs"""
        self._agents[agent_id] = agent

    # ═══ HANDOFF CREATION ═══

    def create_delegation(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        problem_clarity: dict,
        **kwargs
    ) -> HandoffContext:
        """Create a DELEGATE handoff"""
        pass

    def create_transfer(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        context: HandoffContext,
    ) -> HandoffContext:
        """Create a TRANSFER handoff"""
        pass

    # ═══ EXECUTION ═══

    async def execute(self, context: HandoffContext) -> HandoffResult:
        """Execute a single handoff"""
        pass

    async def execute_sequential(
        self,
        contexts: List[HandoffContext]
    ) -> List[HandoffResult]:
        """Execute handoffs in sequence, passing context forward"""
        pass

    async def execute_parallel(
        self,
        contexts: List[HandoffContext]
    ) -> List[HandoffResult]:
        """Execute all handoffs simultaneously"""
        pass

    async def execute_debate(
        self,
        contexts: List[HandoffContext],
        rounds: int = 2
    ) -> List[HandoffResult]:
        """Execute as debate with multiple rounds"""
        pass

    # ═══ SYNTHESIS ═══

    async def synthesize(
        self,
        results: List[HandoffResult],
        context: HandoffContext
    ) -> str:
        """Combine multiple results into coherent output"""
        pass
```

---

## 5. Orchestration Configuration

How agents coordinate through teams and workflows.

### 5.1 Team Definition

```yaml
# mindrian/teams/clarification.yaml

team:
  id: "clarification-team"
  name: "Clarification Team"
  description: "Clarifies problems before analysis"

  members:
    - agent: "larry-clarifier"
      role: "primary"              # Leads the conversation

    - agent: "devil-advocate"
      role: "challenger"           # Challenges assumptions

  coordination:
    mode: "coordinate"             # Sequential, Larry then Devil
    handoff_between: true          # Members can handoff to each other

    sequence:
      - agent: "larry-clarifier"
        until: "problem_clarity.overall >= 0.6"
        max_turns: 10

      - agent: "devil-advocate"
        until: "assumptions_validated"
        max_turns: 3

  success_criteria:
    - "problem_clarity.what_clarity >= 0.7"
    - "problem_clarity.who_clarity >= 0.5"
    - "assumptions.length >= 1"

  on_success: "return_to_orchestrator"
  on_failure: "escalate_to_human"
```

### 5.2 Team Implementation

```python
# mindrian/teams/team.py

from dataclasses import dataclass
from typing import List, Optional, Callable
from enum import Enum


class TeamMode(str, Enum):
    COORDINATE = "coordinate"      # Sequential with handoffs
    COLLABORATE = "collaborate"    # Parallel execution
    DEBATE = "debate"              # Opposing positions
    VOTE = "vote"                  # Each votes on outcome


@dataclass
class TeamMember:
    agent_id: str
    role: str
    until_condition: Optional[str] = None
    max_turns: int = 10


@dataclass
class TeamConfig:
    id: str
    name: str
    members: List[TeamMember]
    mode: TeamMode
    success_criteria: List[str]
    on_success: str
    on_failure: str


class Team:
    """
    Coordinates multiple agents working together.
    """

    def __init__(self, config: TeamConfig):
        self.config = config
        self._handoff_manager = HandoffManager()

    async def execute(self, context: HandoffContext) -> HandoffResult:
        """Execute team workflow"""

        if self.config.mode == TeamMode.COORDINATE:
            return await self._execute_coordinate(context)
        elif self.config.mode == TeamMode.COLLABORATE:
            return await self._execute_collaborate(context)
        elif self.config.mode == TeamMode.DEBATE:
            return await self._execute_debate(context)
        else:
            raise ValueError(f"Unknown team mode: {self.config.mode}")

    async def _execute_coordinate(self, context: HandoffContext) -> HandoffResult:
        """Sequential execution with handoffs"""
        current_context = context
        results = []

        for member in self.config.members:
            # Create handoff to this member
            handoff = self._handoff_manager.create_delegation(
                from_agent=current_context.from_agent,
                to_agent=member.agent_id,
                task=current_context.task_description,
                problem_clarity=current_context.problem_clarity,
            )

            # Execute until condition met or max turns
            turn = 0
            while turn < member.max_turns:
                result = await self._handoff_manager.execute(handoff)
                results.append(result)

                # Check exit condition
                if self._evaluate_condition(member.until_condition, result):
                    break

                turn += 1

            # Update context for next member
            current_context.previous_analyses.append(result.to_analysis())

        # Check success criteria
        success = self._evaluate_success(results)

        return self._combine_results(results, success)

    async def _execute_collaborate(self, context: HandoffContext) -> HandoffResult:
        """Parallel execution"""
        # Create handoffs for all members
        handoffs = [
            self._handoff_manager.create_delegation(
                from_agent=context.from_agent,
                to_agent=member.agent_id,
                task=context.task_description,
                problem_clarity=context.problem_clarity,
            )
            for member in self.config.members
        ]

        # Execute in parallel
        results = await self._handoff_manager.execute_parallel(handoffs)

        # Synthesize
        return self._combine_results(results, True)

    async def _execute_debate(self, context: HandoffContext) -> HandoffResult:
        """Debate execution"""
        handoffs = [
            self._handoff_manager.create_delegation(
                from_agent=context.from_agent,
                to_agent=member.agent_id,
                task=f"[{member.role.upper()}] {context.task_description}",
                problem_clarity=context.problem_clarity,
            )
            for member in self.config.members
        ]

        results = await self._handoff_manager.execute_debate(handoffs, rounds=2)
        return self._combine_results(results, True)
```

### 5.3 Router Configuration

```yaml
# mindrian/workflow/router.yaml

router:
  id: "problem-router"
  name: "Problem Router"
  description: "Routes problems to appropriate teams/agents"

  # Classification rules
  classification:
    method: "hybrid"               # rule + llm
    confidence_threshold: 0.7

    rules:
      - condition: "problem_clarity.overall < 0.3"
        route_to: "clarification-team"
        priority: 100

      - condition: "'validate' in triggers OR 'score' in triggers"
        route_to: "pws-validation"
        priority: 80

      - condition: "'structure' in triggers OR 'organize' in triggers"
        route_to: "minto-pyramid"
        priority: 70

    llm_fallback:
      enabled: true
      model: "claude-sonnet-4-20250514"
      prompt: |
        Given this problem, which framework is best?
        Problem: {problem}
        Available: {frameworks}
        Return JSON: {"framework": "id", "confidence": 0.0-1.0}

  # Neo4j integration
  neo4j:
    enabled: true
    selection_query: |
      MATCH (f:Framework)
      WHERE ANY(t IN $triggers WHERE t IN f.triggers)
      WITH f,
           size([t IN $triggers WHERE t IN f.triggers]) AS match_count
      ORDER BY match_count DESC, f.success_rate DESC
      LIMIT 5
      RETURN f.id, f.name, match_count
```

### 5.4 Main Workflow Configuration

```yaml
# mindrian/workflow/main_workflow.yaml

workflow:
  id: "mindrian-main"
  name: "Mindrian Main Workflow"
  description: "End-to-end problem solving workflow"

  entry_point: "larry-clarifier"

  steps:
    - id: "clarify"
      type: "team"
      team: "clarification-team"
      required: true

    - id: "route"
      type: "router"
      router: "problem-router"
      inputs:
        - "clarify.problem_clarity"
        - "clarify.triggers"

    - id: "analyze"
      type: "dynamic"              # Determined by router
      from_step: "route"

    - id: "synthesize"
      type: "agent"
      agent: "synthesizer"
      inputs:
        - "analyze.results"

    - id: "store"
      type: "action"
      action: "store_insights"
      inputs:
        - "synthesize.key_findings"

  error_handling:
    on_agent_failure: "retry_once"
    on_team_failure: "escalate"
    on_timeout: "return_partial"

  memory:
    store_conversation: true
    store_insights: true
    store_decisions: true
```

---

## 6. Deployment Manifests

What gets deployed and where.

### 6.1 Agent Deployment Manifest

```yaml
# mindrian/deploy/agents.yaml

deployment:
  name: "mindrian-agents"
  version: "1.0.0"

  # Agent deployments
  agents:
    # ═══ CONVERSATIONAL ═══
    - id: "larry-clarifier"
      path: "mindrian.agents.conversational.larry"
      class: "LarryAgent"
      auto_register: true
      singleton: true              # One instance
      resources:
        max_concurrent: 10
        timeout: 300

    - id: "devil-advocate"
      path: "mindrian.agents.conversational.devil"
      class: "DevilAgent"
      auto_register: true
      singleton: true

    # ═══ FRAMEWORKS ═══
    - id: "minto-pyramid"
      path: "mindrian.agents.frameworks.minto_pyramid"
      class: "MintoPyramidAgent"
      auto_register: true
      lazy_load: true              # Load on first use
      resources:
        max_concurrent: 5
        timeout: 180

    - id: "pws-validation"
      path: "mindrian.agents.frameworks.pws_validation"
      class: "PWSValidationAgent"
      auto_register: true
      lazy_load: true

    # ═══ RESEARCH ═══
    - id: "beautiful-question"
      path: "mindrian.agents.research.beautiful_question"
      class: "BeautifulQuestionAgent"
      auto_register: true

    - id: "csio"
      path: "mindrian.agents.research.csio"
      class: "CSIOAgent"
      auto_register: true

  # Team deployments
  teams:
    - id: "clarification-team"
      config: "mindrian/teams/clarification.yaml"
      members:
        - "larry-clarifier"
        - "devil-advocate"

    - id: "analysis-team"
      config: "mindrian/teams/analysis.yaml"
      members:
        - "minto-pyramid"
        - "pws-validation"
        - "beautiful-question"

  # Workflow deployment
  workflows:
    - id: "mindrian-main"
      config: "mindrian/workflow/main_workflow.yaml"
      entry_point: "larry-clarifier"
```

### 6.2 Infrastructure Manifest

```yaml
# mindrian/deploy/infrastructure.yaml

infrastructure:
  name: "mindrian-infra"
  version: "1.0.0"

  # MCP Servers (external dependencies)
  mcp_servers:
    - name: "neo4j"
      required: true
      health_check: "get_neo4j_schema"
      env:
        - NEO4J_URI
        - NEO4J_USER
        - NEO4J_PASSWORD

    - name: "supabase"
      required: true
      health_check: "query SELECT 1"
      env:
        - SUPABASE_URL
        - SUPABASE_KEY

  # Database initialization
  databases:
    neo4j:
      schema: "mindrian/neo4j/schema.cypher"
      seed: "mindrian/neo4j/seed.cypher"
      indexes:
        - "CREATE INDEX framework_id IF NOT EXISTS FOR (f:Framework) ON (f.id)"
        - "CREATE INDEX session_id IF NOT EXISTS FOR (s:Session) ON (s.id)"

    supabase:
      migrations: "mindrian/supabase/migrations/"
      tables:
        - sessions
        - conversations
        - insights

  # API deployment
  api:
    framework: "fastapi"
    entry: "api/main.py"
    port: 8000
    workers: 4
    routes:
      - "/chat"
      - "/sessions"
      - "/agents"

  # UI deployment (optional)
  ui:
    framework: "streamlit"
    entry: "ui/streamlit_app.py"
    port: 8501
```

### 6.3 Startup Sequence

```python
# mindrian/startup.py

async def startup():
    """
    Mindrian startup sequence.

    Order matters - dependencies must initialize first.
    """

    # ═══ PHASE 1: Infrastructure ═══
    print("Phase 1: Infrastructure")

    # Connect to MCP servers
    await mcp_manager.connect("neo4j")
    await mcp_manager.connect("supabase")

    # Verify connections
    await mcp_manager.health_check("neo4j")
    await mcp_manager.health_check("supabase")

    # ═══ PHASE 2: Database Setup ═══
    print("Phase 2: Database Setup")

    # Run Neo4j schema
    await neo4j.run_schema("mindrian/neo4j/schema.cypher")

    # Run Supabase migrations
    await supabase.run_migrations("mindrian/supabase/migrations/")

    # ═══ PHASE 3: Agent Registration ═══
    print("Phase 3: Agent Registration")

    # Load deployment manifest
    manifest = load_yaml("mindrian/deploy/agents.yaml")

    # Register agents
    for agent_config in manifest["deployment"]["agents"]:
        if agent_config.get("auto_register", True):
            agent = load_agent(agent_config)
            handoff_manager.register(agent_config["id"], agent)

            # Register in Neo4j
            if hasattr(agent, "neo4j_register"):
                await agent.neo4j_register()

    # ═══ PHASE 4: Team Registration ═══
    print("Phase 4: Team Registration")

    for team_config in manifest["deployment"]["teams"]:
        team = load_team(team_config)
        team_registry.register(team_config["id"], team)

    # ═══ PHASE 5: Workflow Registration ═══
    print("Phase 5: Workflow Registration")

    for workflow_config in manifest["deployment"]["workflows"]:
        workflow = load_workflow(workflow_config)
        workflow_registry.register(workflow_config["id"], workflow)

    # ═══ PHASE 6: Ready ═══
    print("Mindrian ready!")

    return {
        "agents": handoff_manager.list_agents(),
        "teams": team_registry.list_teams(),
        "workflows": workflow_registry.list_workflows(),
    }
```

### 6.4 File System Layout (What Gets Deployed)

```
mindrian-agno/
├── mindrian/
│   ├── agents/
│   │   ├── conversational/
│   │   │   ├── larry/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.py
│   │   │   │   ├── spec.yaml
│   │   │   │   └── schema.cypher
│   │   │   └── devil/
│   │   │       └── ...
│   │   ├── frameworks/
│   │   │   ├── minto_pyramid/
│   │   │   ├── pws_validation/
│   │   │   └── jobs_to_be_done/
│   │   └── research/
│   │       ├── beautiful_question/
│   │       ├── domain_analysis/
│   │       └── csio/
│   │
│   ├── teams/
│   │   ├── clarification.yaml
│   │   ├── analysis.yaml
│   │   └── team.py
│   │
│   ├── workflow/
│   │   ├── main_workflow.yaml
│   │   ├── router.yaml
│   │   └── orchestrator.py
│   │
│   ├── handoff/
│   │   ├── types.py
│   │   ├── context.py
│   │   └── manager.py
│   │
│   ├── tools/
│   │   ├── mcp_manager.py
│   │   └── custom/
│   │
│   ├── memory/
│   │   ├── conversation.py
│   │   └── session.py
│   │
│   ├── builder/
│   │   ├── agent_builder.py
│   │   ├── schema.py
│   │   └── phases.py
│   │
│   ├── neo4j/
│   │   ├── schema.cypher
│   │   └── seed.cypher
│   │
│   ├── supabase/
│   │   └── migrations/
│   │
│   └── deploy/
│       ├── agents.yaml
│       ├── infrastructure.yaml
│       └── startup.py
│
├── api/
│   ├── main.py
│   └── routes/
│
├── ui/
│   └── streamlit_app.py
│
└── tests/
```

---

## Summary

| Component | Format | Location | Purpose |
|-----------|--------|----------|---------|
| **Agent Spec** | YAML/Python | `agents/{category}/{id}/spec.yaml` | Defines everything about an agent |
| **Builder** | Python | `builder/agent_builder.py` | Transforms specs → deployable code |
| **Tools** | Python + YAML | `tools/` | MCP and custom tool integration |
| **Handoff** | Python | `handoff/` | State transfer protocol |
| **Orchestration** | YAML + Python | `teams/`, `workflow/` | Agent coordination |
| **Deployment** | YAML | `deploy/` | What runs where |

---

*Mindrian Swarm Manager Specifications v1.0*
