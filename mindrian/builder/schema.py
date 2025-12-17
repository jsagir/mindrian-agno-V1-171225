"""
Agent Builder Schema - Data structures for agent specifications

Defines the complete schema for Mindrian agents as dataclasses.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    """Types of Mindrian agents"""
    ROLE = "role"                     # Conversational persona (Larry, Devil)
    OPERATOR = "operator"             # Single-purpose framework (Minto, PWS)
    COLLABORATIVE = "collaborative"   # Multi-agent coordination (De Bono)
    PIPELINE = "pipeline"             # Sequential processing
    GUIDED = "guided"                 # Interactive step-by-step


class OutputFormat(str, Enum):
    """Standard output formats"""
    MARKDOWN = "markdown"
    JSON = "json"
    SCQA = "scqa"
    SCORECARD = "scorecard"
    MATRIX = "matrix"
    STRUCTURED = "structured"


class ReturnBehavior(str, Enum):
    """How results are returned"""
    SYNTHESIZE = "synthesize"       # Orchestrator interprets
    PASSTHROUGH = "passthrough"     # Raw results to user
    ITERATE = "iterate"             # Triggers another round


class CheckpointAction(str, Enum):
    """What to do on checkpoint failure"""
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    ASK_USER = "ask_user"


class QualityGateAction(str, Enum):
    """What to do on quality gate failure"""
    WARN = "warn"
    FAIL = "fail"
    RETRY = "retry"


# ============================================================================
# HANDOFF CONFIGURATION
# ============================================================================

@dataclass
class ReceivesConfig:
    """What an agent receives in handoffs"""
    # Problem clarity requirements
    requires_what: bool = True
    requires_who: bool = False
    requires_success: bool = False
    min_clarity: float = 0.3

    # Previous analyses
    accepts_previous: List[str] = field(default_factory=list)  # Framework IDs

    # Other context
    accepts_focus_areas: bool = True
    accepts_conversation: bool = True


@dataclass
class ReturnsConfig:
    """What an agent returns in handoffs"""
    output_format: OutputFormat = OutputFormat.MARKDOWN
    includes_key_findings: bool = True
    includes_recommendations: bool = True
    includes_confidence: bool = True
    score_names: List[str] = field(default_factory=list)
    suggested_next: List[str] = field(default_factory=list)
    includes_open_questions: bool = False


@dataclass
class RoutingConfig:
    """Handoff routing configuration"""
    can_delegate_to: List[str] = field(default_factory=list)
    can_be_called_by: List[str] = field(default_factory=list)
    default_return_to: str = "orchestrator"
    return_behavior: ReturnBehavior = ReturnBehavior.SYNTHESIZE


@dataclass
class HandoffConfig:
    """Complete handoff protocol configuration"""
    receives: ReceivesConfig = field(default_factory=ReceivesConfig)
    returns: ReturnsConfig = field(default_factory=ReturnsConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)

    # Supported handoff types
    supports_delegate: bool = True
    supports_transfer: bool = False
    supports_return: bool = True
    supports_escalate: bool = True


# ============================================================================
# TOOL CONFIGURATION
# ============================================================================

@dataclass
class MCPServerConfig:
    """MCP server connection configuration"""
    server: str                         # Server name (neo4j, pinecone, etc.)
    tools: List[str] = field(default_factory=list)  # Specific tools or ["*"]
    required: bool = True               # Fail if unavailable?


@dataclass
class CustomToolConfig:
    """Custom Python tool configuration"""
    name: str
    description: str
    function_path: str                  # e.g., "mindrian.tools.my_tool"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GlobalAction:
    """Action available in all phases"""
    action: str
    description: str
    tool: str


@dataclass
class ToolConfig:
    """Complete tool configuration"""
    mcp_servers: List[MCPServerConfig] = field(default_factory=list)
    custom_tools: List[CustomToolConfig] = field(default_factory=list)
    global_actions: List[GlobalAction] = field(default_factory=list)


# ============================================================================
# WORKFLOW PHASES
# ============================================================================

@dataclass
class Checkpoint:
    """Phase checkpoint validation"""
    criteria: List[str]                 # What must be true
    on_fail: CheckpointAction = CheckpointAction.RETRY
    max_retries: int = 2


@dataclass
class Phase:
    """Workflow phase definition"""
    id: str
    name: str
    description: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    checkpoint: Optional[Checkpoint] = None
    tools: List[str] = field(default_factory=list)


# ============================================================================
# NEO4J CONFIGURATION
# ============================================================================

@dataclass
class Neo4jProperty:
    """Neo4j node property"""
    name: str
    type: str
    indexed: bool = False


@dataclass
class Neo4jRelationship:
    """Neo4j relationship definition"""
    type: str                           # CHAINS_TO, GOOD_FOR, etc.
    target_label: str                   # Target node label
    properties: List[str] = field(default_factory=list)


@dataclass
class Neo4jConfig:
    """Neo4j schema configuration"""
    node_label: str = "Framework"
    properties: List[Neo4jProperty] = field(default_factory=list)
    relationships: List[Neo4jRelationship] = field(default_factory=list)
    register_cypher: str = ""
    selection_cypher: str = ""


# ============================================================================
# VALIDATION
# ============================================================================

@dataclass
class QualityGate:
    """Quality gate definition"""
    name: str
    check: str
    threshold: float = 0.0
    action: QualityGateAction = QualityGateAction.WARN


@dataclass
class ValidationConfig:
    """Validation configuration"""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    quality_gates: List[QualityGate] = field(default_factory=list)


# ============================================================================
# MEMORY CONFIGURATION
# ============================================================================

@dataclass
class SessionMemoryConfig:
    """Agno session memory configuration"""
    enabled: bool = True
    history_depth: int = 10


@dataclass
class SupabaseMemoryConfig:
    """Supabase vector memory configuration"""
    enabled: bool = False
    table: str = "agent_memory"
    embedding_field: str = "embedding"
    retrieval_top_k: int = 5


@dataclass
class Neo4jMemoryConfig:
    """Neo4j graph memory configuration"""
    enabled: bool = False
    store_outputs: bool = True
    store_decisions: bool = True


@dataclass
class MemoryConfig:
    """Complete memory configuration"""
    session: SessionMemoryConfig = field(default_factory=SessionMemoryConfig)
    supabase: SupabaseMemoryConfig = field(default_factory=SupabaseMemoryConfig)
    neo4j: Neo4jMemoryConfig = field(default_factory=Neo4jMemoryConfig)


# ============================================================================
# SUB-AGENTS
# ============================================================================

@dataclass
class SubAgentConfig:
    """Sub-agent configuration for COLLABORATIVE/PIPELINE types"""
    id: str
    role: str
    model: Optional[str] = None         # Defaults to parent model
    instructions: str = ""
    tools: List[str] = field(default_factory=list)


# ============================================================================
# TRIGGERS & CHAINING
# ============================================================================

@dataclass
class ContextTrigger:
    """Context-based trigger"""
    condition: str
    priority: int = 1


@dataclass
class ProblemTypeTrigger:
    """Problem type trigger"""
    type: str                           # un-defined, ill-defined, well-defined
    confidence: float = 0.5


@dataclass
class TriggerConfig:
    """Trigger configuration"""
    keywords: List[str] = field(default_factory=list)
    contexts: List[ContextTrigger] = field(default_factory=list)
    problem_types: List[ProblemTypeTrigger] = field(default_factory=list)


@dataclass
class ChainingConfig:
    """Framework chaining configuration"""
    follows: List[str] = field(default_factory=list)      # Should run before
    precedes: List[str] = field(default_factory=list)     # Should run after
    alternatives: List[str] = field(default_factory=list) # Similar frameworks
    enhances: List[str] = field(default_factory=list)     # Adds value to


# ============================================================================
# COMPLETE AGENT SPECIFICATION
# ============================================================================

@dataclass
class ModelConfig:
    """Model configuration"""
    provider: str = "anthropic"
    id: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    thinking_enabled: bool = False
    thinking_budget: int = 0


@dataclass
class InstructionsConfig:
    """Agent instructions configuration"""
    system: str = ""
    methodology: str = ""
    output_template: str = ""
    quality_criteria: List[str] = field(default_factory=list)
    behavioral_rules: List[str] = field(default_factory=list)
    tone: str = ""


@dataclass
class MetadataConfig:
    """Agent metadata"""
    author: str = ""
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    source: str = ""                    # Path to source SKILL.md
    documentation: str = ""


@dataclass
class AgentSpec:
    """
    Complete Agent Specification

    This is the master dataclass that defines everything about an agent.
    Used by the Agent Builder to generate Python code.
    """

    # Identity
    name: str
    id: str
    type: AgentType
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)

    # Configuration sections
    model: ModelConfig = field(default_factory=ModelConfig)
    instructions: InstructionsConfig = field(default_factory=InstructionsConfig)
    handoff: HandoffConfig = field(default_factory=HandoffConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    sub_agents: List[SubAgentConfig] = field(default_factory=list)
    phases: List[Phase] = field(default_factory=list)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    triggers: TriggerConfig = field(default_factory=TriggerConfig)
    chaining: ChainingConfig = field(default_factory=ChainingConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    metadata: MetadataConfig = field(default_factory=MetadataConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSpec":
        """Create from dictionary"""
        # This would need proper nested dataclass instantiation
        # Simplified for now
        return cls(
            name=data.get("name", ""),
            id=data.get("id", ""),
            type=AgentType(data.get("type", "operator")),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
        )

    def validate(self) -> List[str]:
        """Validate specification, return list of errors"""
        errors = []

        if not self.name:
            errors.append("Agent name is required")
        if not self.id:
            errors.append("Agent ID is required")
        if not self.instructions.system and not self.instructions.methodology:
            errors.append("Agent needs instructions (system or methodology)")

        return errors

    def get_neo4j_register_cypher(self) -> str:
        """Generate Neo4j registration Cypher"""
        triggers_list = str(self.triggers.keywords)
        problem_types = str([pt.type for pt in self.triggers.problem_types])

        return f"""
MERGE (f:Framework {{id: '{self.id}'}})
SET f.name = '{self.name}',
    f.type = '{self.type.value}',
    f.triggers = {triggers_list},
    f.problem_types = {problem_types},
    f.version = '{self.version}',
    f.description = '{self.description}',
    f.updated_at = datetime()
RETURN f
"""
