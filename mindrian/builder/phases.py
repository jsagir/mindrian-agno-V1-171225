"""
Agent Builder Phases - The 7-phase workflow for building agents

Each phase is a separate class that transforms inputs to outputs.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
import re
import yaml

from .schema import (
    AgentSpec, AgentType, ModelConfig, InstructionsConfig,
    HandoffConfig, ReceivesConfig, ReturnsConfig, RoutingConfig,
    ToolConfig, MCPServerConfig, CustomToolConfig, GlobalAction,
    Neo4jConfig, Neo4jProperty, Neo4jRelationship,
    TriggerConfig, ProblemTypeTrigger, ChainingConfig,
    ValidationConfig, QualityGate, MemoryConfig, MetadataConfig,
    OutputFormat, ReturnBehavior,
)


@dataclass
class PhaseResult:
    """Result from a builder phase"""
    success: bool
    output: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BuilderPhase(ABC):
    """Base class for builder phases"""

    @property
    @abstractmethod
    def phase_id(self) -> str:
        """Phase identifier"""
        pass

    @property
    @abstractmethod
    def phase_name(self) -> str:
        """Human-readable phase name"""
        pass

    @abstractmethod
    def execute(self, input_data: Any) -> PhaseResult:
        """Execute the phase"""
        pass

    def validate_checkpoint(self, result: PhaseResult, criteria: List[str]) -> Tuple[bool, List[str]]:
        """Validate checkpoint criteria"""
        failures = []
        for criterion in criteria:
            if not self._check_criterion(result.output, criterion):
                failures.append(f"Checkpoint failed: {criterion}")
        return len(failures) == 0, failures

    def _check_criterion(self, output: Any, criterion: str) -> bool:
        """Check a single criterion"""
        # Simple attribute check for now
        if hasattr(output, criterion):
            return bool(getattr(output, criterion))
        return False


# ============================================================================
# PHASE 1: SKILL ANALYSIS
# ============================================================================

@dataclass
class SkillDefinition:
    """Parsed SKILL.md definition"""
    # Frontmatter
    name: str
    type: str
    version: str = "1.0.0"
    triggers: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    chaining: List[str] = field(default_factory=list)
    behavioral_rules: List[str] = field(default_factory=list)
    tone: str = ""

    # Body sections
    methodology: str = ""
    output_template: str = ""
    quality_criteria: List[str] = field(default_factory=list)

    # Raw content
    raw_content: str = ""
    source_path: str = ""


class SkillAnalysisPhase(BuilderPhase):
    """
    Phase 1: Parse and analyze SKILL.md files

    Input: Path to SKILL.md or raw YAML content
    Output: SkillDefinition
    """

    @property
    def phase_id(self) -> str:
        return "skill_analysis"

    @property
    def phase_name(self) -> str:
        return "SKILL Analysis"

    def execute(self, input_data: str) -> PhaseResult:
        """Parse SKILL.md file"""
        errors = []
        warnings = []

        try:
            # Determine if input is path or content
            if Path(input_data).exists():
                content = Path(input_data).read_text()
                source_path = input_data
            else:
                content = input_data
                source_path = ""

            # Parse frontmatter
            frontmatter, body = self._parse_frontmatter(content)
            if not frontmatter:
                errors.append("No YAML frontmatter found")
                return PhaseResult(success=False, output=None, errors=errors)

            # Extract sections from body
            sections = self._parse_sections(body)

            # Build SkillDefinition
            skill = SkillDefinition(
                name=frontmatter.get("name", "Unknown"),
                type=frontmatter.get("type", "operator"),
                version=frontmatter.get("version", "1.0.0"),
                triggers=frontmatter.get("triggers", []),
                inputs=frontmatter.get("inputs", []),
                outputs=frontmatter.get("outputs", ["markdown"]),
                chaining=frontmatter.get("chaining", []),
                behavioral_rules=frontmatter.get("behavioral_rules", []),
                tone=frontmatter.get("tone", ""),
                methodology=sections.get("methodology", ""),
                output_template=sections.get("output_template", ""),
                quality_criteria=sections.get("quality_criteria", []),
                raw_content=content,
                source_path=source_path,
            )

            # Validate required fields
            if not skill.name:
                errors.append("Missing required field: name")
            if not skill.type:
                errors.append("Missing required field: type")

            # Warnings for optional but recommended fields
            if not skill.triggers:
                warnings.append("No triggers defined - agent won't auto-activate")
            if not skill.methodology and skill.type != "role":
                warnings.append("No methodology defined for operator-type skill")

            return PhaseResult(
                success=len(errors) == 0,
                output=skill,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            return PhaseResult(
                success=False,
                output=None,
                errors=[f"Failed to parse SKILL.md: {str(e)}"],
            )

    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter from markdown"""
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)

        if match:
            frontmatter_str = match.group(1)
            body = match.group(2)
            try:
                frontmatter = yaml.safe_load(frontmatter_str)
                return frontmatter or {}, body
            except yaml.YAMLError:
                return {}, content

        return {}, content

    def _parse_sections(self, body: str) -> Dict[str, Any]:
        """Parse body sections by headers"""
        sections = {}

        # Find methodology section
        methodology_match = re.search(
            r'##\s*(?:Core\s+)?Methodology\s*\n(.*?)(?=\n##|\Z)',
            body, re.IGNORECASE | re.DOTALL
        )
        if methodology_match:
            sections["methodology"] = methodology_match.group(1).strip()

        # Find output template
        template_match = re.search(
            r'##\s*Output\s*(?:Template|Format)\s*\n(.*?)(?=\n##|\Z)',
            body, re.IGNORECASE | re.DOTALL
        )
        if template_match:
            sections["output_template"] = template_match.group(1).strip()

        # Find quality criteria
        criteria_match = re.search(
            r'##\s*(?:Quality\s+)?Criteria\s*\n(.*?)(?=\n##|\Z)',
            body, re.IGNORECASE | re.DOTALL
        )
        if criteria_match:
            # Extract bullet points
            criteria_text = criteria_match.group(1)
            criteria = re.findall(r'[-*]\s*(.+)', criteria_text)
            sections["quality_criteria"] = criteria

        return sections


# ============================================================================
# PHASE 2: ARCHITECTURE
# ============================================================================

class ArchitecturePhase(BuilderPhase):
    """
    Phase 2: Determine agent architecture

    Input: SkillDefinition
    Output: Partial AgentSpec with type, model, basic config
    """

    @property
    def phase_id(self) -> str:
        return "architecture"

    @property
    def phase_name(self) -> str:
        return "Agent Architecture"

    def execute(self, input_data: SkillDefinition) -> PhaseResult:
        """Determine agent architecture from skill"""
        skill = input_data
        errors = []
        warnings = []

        # Map skill type to agent type
        type_mapping = {
            "role": AgentType.ROLE,
            "operator": AgentType.OPERATOR,
            "collaborative": AgentType.COLLABORATIVE,
            "pipeline": AgentType.PIPELINE,
            "guided": AgentType.GUIDED,
        }
        agent_type = type_mapping.get(skill.type.lower(), AgentType.OPERATOR)

        # Select model based on complexity
        model = self._select_model(skill, agent_type)

        # Build initial spec
        spec = AgentSpec(
            name=skill.name,
            id=self._generate_id(skill.name),
            type=agent_type,
            version=skill.version,
            description=f"{skill.name} agent",
            model=model,
            instructions=InstructionsConfig(
                system=self._build_system_prompt(skill, agent_type),
                methodology=skill.methodology,
                output_template=skill.output_template,
                quality_criteria=skill.quality_criteria,
                behavioral_rules=skill.behavioral_rules,
                tone=skill.tone,
            ),
            triggers=TriggerConfig(
                keywords=skill.triggers,
                problem_types=[
                    ProblemTypeTrigger(type="ill-defined", confidence=0.5)
                ],
            ),
            chaining=ChainingConfig(
                precedes=skill.chaining,
            ),
            metadata=MetadataConfig(
                source=skill.source_path,
            ),
        )

        return PhaseResult(
            success=len(errors) == 0,
            output=spec,
            errors=errors,
            warnings=warnings,
        )

    def _generate_id(self, name: str) -> str:
        """Generate agent ID from name"""
        return name.lower().replace(" ", "-").replace("_", "-")

    def _select_model(self, skill: SkillDefinition, agent_type: AgentType) -> ModelConfig:
        """Select appropriate model based on skill complexity"""
        # Complex types need stronger model
        if agent_type in (AgentType.COLLABORATIVE, AgentType.PIPELINE):
            return ModelConfig(
                provider="anthropic",
                id="claude-sonnet-4-20250514",
                temperature=0.7,
                thinking_enabled=True,
                thinking_budget=5000,
            )
        # Roles need good conversation
        elif agent_type == AgentType.ROLE:
            return ModelConfig(
                provider="anthropic",
                id="claude-sonnet-4-20250514",
                temperature=0.8,
            )
        # Operators can be more deterministic
        else:
            return ModelConfig(
                provider="anthropic",
                id="claude-sonnet-4-20250514",
                temperature=0.5,
            )

    def _build_system_prompt(self, skill: SkillDefinition, agent_type: AgentType) -> str:
        """Build system prompt from skill"""
        parts = [f"# {skill.name}"]

        if skill.methodology:
            parts.append(f"\n## Methodology\n{skill.methodology}")

        if skill.output_template:
            parts.append(f"\n## Output Format\n{skill.output_template}")

        if skill.quality_criteria:
            parts.append("\n## Quality Criteria")
            for c in skill.quality_criteria:
                parts.append(f"- {c}")

        if skill.behavioral_rules:
            parts.append("\n## Behavioral Rules")
            for r in skill.behavioral_rules:
                parts.append(f"- {r}")

        return "\n".join(parts)


# ============================================================================
# PHASE 3: HANDOFF PROTOCOL
# ============================================================================

class HandoffProtocolPhase(BuilderPhase):
    """
    Phase 3: Design handoff integration

    Input: AgentSpec from Phase 2
    Output: AgentSpec with complete handoff configuration
    """

    @property
    def phase_id(self) -> str:
        return "handoff_protocol"

    @property
    def phase_name(self) -> str:
        return "Handoff Protocol Design"

    def execute(self, input_data: AgentSpec) -> PhaseResult:
        """Configure handoff protocol"""
        spec = input_data
        errors = []
        warnings = []

        # Configure receives based on agent type
        receives = self._configure_receives(spec)

        # Configure returns based on outputs
        returns = self._configure_returns(spec)

        # Configure routing based on chaining
        routing = self._configure_routing(spec)

        # Update spec
        spec.handoff = HandoffConfig(
            receives=receives,
            returns=returns,
            routing=routing,
            supports_delegate=True,
            supports_transfer=(spec.type == AgentType.ROLE),
            supports_return=True,
            supports_escalate=True,
        )

        return PhaseResult(
            success=len(errors) == 0,
            output=spec,
            errors=errors,
            warnings=warnings,
        )

    def _configure_receives(self, spec: AgentSpec) -> ReceivesConfig:
        """Configure what the agent receives"""
        # All agents should receive problem clarity
        receives = ReceivesConfig(
            requires_what=True,
            requires_who=(spec.type != AgentType.OPERATOR),
            requires_success=(spec.type in (AgentType.COLLABORATIVE, AgentType.PIPELINE)),
            min_clarity=0.3 if spec.type == AgentType.ROLE else 0.5,
            accepts_focus_areas=True,
            accepts_conversation=(spec.type == AgentType.ROLE),
        )

        # Add previous analyses from chaining
        if spec.chaining.follows:
            receives.accepts_previous = spec.chaining.follows

        return receives

    def _configure_returns(self, spec: AgentSpec) -> ReturnsConfig:
        """Configure what the agent returns"""
        # Map output formats
        output_format = OutputFormat.MARKDOWN

        returns = ReturnsConfig(
            output_format=output_format,
            includes_key_findings=True,
            includes_recommendations=True,
            includes_confidence=True,
            score_names=[],
            suggested_next=spec.chaining.precedes,
            includes_open_questions=(spec.type == AgentType.ROLE),
        )

        return returns

    def _configure_routing(self, spec: AgentSpec) -> RoutingConfig:
        """Configure handoff routing"""
        return RoutingConfig(
            can_delegate_to=spec.chaining.precedes,
            can_be_called_by=["larry", "orchestrator"] + spec.chaining.follows,
            default_return_to="orchestrator",
            return_behavior=ReturnBehavior.SYNTHESIZE,
        )


# ============================================================================
# PHASE 4: TOOL ASSEMBLY
# ============================================================================

class ToolAssemblyPhase(BuilderPhase):
    """
    Phase 4: Assemble tools from MCPs and custom functions

    Input: AgentSpec from Phase 3
    Output: AgentSpec with complete tool configuration
    """

    # Known MCP servers and their tools
    MCP_CATALOG = {
        "neo4j": ["read_neo4j_cypher", "write_neo4j_cypher", "get_neo4j_schema"],
        "pinecone": ["search_records", "upsert_records", "list_indexes"],
        "render": ["list_services", "get_metrics", "list_logs"],
        "n8n": ["create_workflow", "get_workflow", "validate_workflow"],
    }

    @property
    def phase_id(self) -> str:
        return "tool_assembly"

    @property
    def phase_name(self) -> str:
        return "Tool Assembly"

    def execute(self, input_data: AgentSpec) -> PhaseResult:
        """Assemble tools for agent"""
        spec = input_data
        errors = []
        warnings = []

        mcp_servers = []
        custom_tools = []
        global_actions = []

        # Add Neo4j for all agents (framework storage)
        mcp_servers.append(MCPServerConfig(
            server="neo4j",
            tools=["read_neo4j_cypher", "get_neo4j_schema"],
            required=False,
        ))

        # Add type-specific tools
        if spec.type == AgentType.COLLABORATIVE:
            # Collaborative agents might need research
            mcp_servers.append(MCPServerConfig(
                server="tavily",
                tools=["*"],
                required=False,
            ))

        # Add global actions
        global_actions.append(GlobalAction(
            action="store_insight",
            description="Store key insight in knowledge graph",
            tool="neo4j.write_neo4j_cypher",
        ))

        spec.tools = ToolConfig(
            mcp_servers=mcp_servers,
            custom_tools=custom_tools,
            global_actions=global_actions,
        )

        return PhaseResult(
            success=len(errors) == 0,
            output=spec,
            errors=errors,
            warnings=warnings,
        )


# ============================================================================
# PHASE 5: NEO4J SCHEMA
# ============================================================================

class Neo4jSchemaPhase(BuilderPhase):
    """
    Phase 5: Generate Neo4j schema for framework intelligence

    Input: AgentSpec from Phase 4
    Output: AgentSpec with Neo4j configuration
    """

    @property
    def phase_id(self) -> str:
        return "neo4j_schema"

    @property
    def phase_name(self) -> str:
        return "Neo4j Schema Generation"

    def execute(self, input_data: AgentSpec) -> PhaseResult:
        """Generate Neo4j schema"""
        spec = input_data
        errors = []
        warnings = []

        # Define properties
        properties = [
            Neo4jProperty(name="id", type="string", indexed=True),
            Neo4jProperty(name="name", type="string", indexed=True),
            Neo4jProperty(name="type", type="string", indexed=True),
            Neo4jProperty(name="version", type="string"),
            Neo4jProperty(name="description", type="string"),
            Neo4jProperty(name="triggers", type="list"),
            Neo4jProperty(name="problem_types", type="list"),
            Neo4jProperty(name="updated_at", type="datetime"),
        ]

        # Define relationships
        relationships = [
            Neo4jRelationship(
                type="CHAINS_TO",
                target_label="Framework",
                properties=["weight", "reason"],
            ),
            Neo4jRelationship(
                type="GOOD_FOR",
                target_label="ProblemType",
                properties=["confidence"],
            ),
            Neo4jRelationship(
                type="USED_BY",
                target_label="Session",
                properties=["timestamp", "success"],
            ),
        ]

        # Generate Cypher
        register_cypher = spec.get_neo4j_register_cypher()

        selection_cypher = """
MATCH (f:Framework)
WHERE ANY(t IN $triggers WHERE t IN f.triggers)
   OR ANY(pt IN $problem_types WHERE pt IN f.problem_types)
WITH f,
     CASE WHEN ANY(t IN $triggers WHERE t IN f.triggers) THEN 0.6 ELSE 0 END +
     CASE WHEN ANY(pt IN $problem_types WHERE pt IN f.problem_types) THEN 0.4 ELSE 0 END
     AS score
WHERE score > 0
ORDER BY score DESC
LIMIT 5
RETURN f.id AS id, f.name AS name, score
"""

        spec.neo4j = Neo4jConfig(
            node_label="Framework",
            properties=properties,
            relationships=relationships,
            register_cypher=register_cypher,
            selection_cypher=selection_cypher,
        )

        return PhaseResult(
            success=len(errors) == 0,
            output=spec,
            errors=errors,
            warnings=warnings,
        )


# ============================================================================
# PHASE 6: CODE GENERATION
# ============================================================================

class CodeGenerationPhase(BuilderPhase):
    """
    Phase 6: Generate Python agent implementation

    Input: Complete AgentSpec
    Output: Dict with generated code files
    """

    @property
    def phase_id(self) -> str:
        return "code_generation"

    @property
    def phase_name(self) -> str:
        return "Code Generation"

    def execute(self, input_data: AgentSpec) -> PhaseResult:
        """Generate Python code"""
        spec = input_data
        errors = []
        warnings = []

        # Generate main agent class
        agent_code = self._generate_agent_class(spec)

        # Generate __init__.py
        init_code = self._generate_init(spec)

        # Generate test file
        test_code = self._generate_tests(spec)

        # Generate Neo4j schema file
        schema_cypher = spec.neo4j.register_cypher

        output = {
            "agent.py": agent_code,
            "__init__.py": init_code,
            "tests/test_agent.py": test_code,
            "schema.cypher": schema_cypher,
        }

        return PhaseResult(
            success=len(errors) == 0,
            output=output,
            errors=errors,
            warnings=warnings,
        )

    def _generate_agent_class(self, spec: AgentSpec) -> str:
        """Generate the main agent class"""
        class_name = self._to_class_name(spec.name)

        return f'''"""
{spec.name} - Auto-generated by Mindrian Agent Builder
Version: {spec.version}
Type: {spec.type.value}
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from mindrian.handoff.context import HandoffContext, HandoffResult
from mindrian.handoff.types import HandoffType, HandoffMode, ReturnBehavior


AGENT_INSTRUCTIONS = """
{spec.instructions.system}
"""


class {class_name}:
    """
    {spec.description}

    Type: {spec.type.value}
    Triggers: {spec.triggers.keywords}

    Usage:
        agent = {class_name}()

        # Direct use
        result = await agent.run("Input message")

        # With handoff
        result = await agent.process_handoff(context)
    """

    def __init__(
        self,
        model: str = "{spec.model.id}",
        enable_tools: bool = True,
    ):
        self._model = model
        self._db = SqliteDb(db_file="tmp/mindrian.db")

        self._agent = Agent(
            name="{spec.name}",
            agent_id="{spec.id}",
            model=Claude(id=model),
            description="{spec.description}",
            instructions=AGENT_INSTRUCTIONS,
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
        """Process handoff from orchestrator"""
        import time
        start_time = time.time()

        prompt = self._build_handoff_prompt(context)

        try:
            response = await self._agent.arun(prompt)
            output = response.content if hasattr(response, 'content') else str(response)

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="{spec.id}",
                to_agent=context.return_to,
                success=True,
                output=output,
                key_findings=self._extract_findings(output),
                recommendations=self._extract_recommendations(output),
                confidence=0.75,
                suggested_next_agents={spec.handoff.returns.suggested_next},
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent="{spec.id}",
                to_agent=context.return_to,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def _build_handoff_prompt(self, context: HandoffContext) -> str:
        """Build prompt from handoff context"""
        sections = [context.to_prompt()]

        if context.previous_analyses:
            sections.append("\\n## Previous Analyses")
            for pa in context.previous_analyses:
                sections.append(f"### {{pa.framework_name}}\\n{{pa.output[:1000]}}...")

        sections.append(f"""
## Your Task

Apply {spec.name} methodology to this challenge.
Use the problem clarity provided.
Build on any previous analyses.
""")

        return "\\n\\n".join(sections)

    def _extract_findings(self, output: str) -> List[str]:
        """Extract key findings from output"""
        # Simple extraction - would be more sophisticated in production
        findings = []
        if "Key Finding" in output or "## Finding" in output:
            # Extract bullet points after findings header
            pass
        return findings or ["Analysis completed"]

    def _extract_recommendations(self, output: str) -> List[str]:
        """Extract recommendations from output"""
        recommendations = []
        if "Recommend" in output:
            pass
        return recommendations or ["Review analysis"]

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
            task_description=f"Apply {spec.name} to: {{challenge}}",
            expected_output="{spec.handoff.returns.output_format.value}",
            from_agent="orchestrator",
            to_agent="{spec.id}",
            return_to="orchestrator",
            handoff_type=HandoffType.DELEGATE,
        )


# Neo4j registration
NEO4J_REGISTER = """
{spec.neo4j.register_cypher}
"""
'''

    def _generate_init(self, spec: AgentSpec) -> str:
        """Generate __init__.py"""
        class_name = self._to_class_name(spec.name)
        return f'''"""
{spec.name} Agent
"""

from .agent import {class_name}

__all__ = ["{class_name}"]
'''

    def _generate_tests(self, spec: AgentSpec) -> str:
        """Generate test file"""
        class_name = self._to_class_name(spec.name)
        return f'''"""
Tests for {spec.name} Agent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ..agent import {class_name}


class Test{class_name}:
    """Test suite for {spec.name}"""

    def test_initialization(self):
        """Test agent initializes correctly"""
        agent = {class_name}()
        assert agent.agent is not None
        assert agent.agent.name == "{spec.name}"

    @pytest.mark.asyncio
    async def test_run(self):
        """Test direct execution"""
        agent = {class_name}()
        # Mock the agent response
        agent._agent.arun = AsyncMock(return_value=MagicMock(content="Test output"))

        result = await agent.run("Test input")
        assert result == "Test output"

    @pytest.mark.asyncio
    async def test_process_handoff(self):
        """Test handoff processing"""
        from mindrian.handoff.context import HandoffContext, ProblemClarity

        agent = {class_name}()
        agent._agent.arun = AsyncMock(return_value=MagicMock(content="Analysis result"))

        context = HandoffContext(
            handoff_id="test-123",
            problem_clarity=ProblemClarity(what="Test problem"),
            task_description="Test task",
            from_agent="orchestrator",
            to_agent="{spec.id}",
            return_to="orchestrator",
        )

        result = await agent.process_handoff(context)

        assert result.success is True
        assert result.from_agent == "{spec.id}"
        assert "Analysis result" in result.output

    def test_create_handoff_context(self):
        """Test handoff context creation"""
        agent = {class_name}()

        context = agent.create_handoff_context(
            challenge="Test challenge",
            problem_clarity={{"what": "Problem", "who": "User"}}
        )

        assert context.to_agent == "{spec.id}"
        assert context.problem_clarity.what == "Problem"
'''

    def _to_class_name(self, name: str) -> str:
        """Convert name to PascalCase class name"""
        # Remove special chars, split on spaces/hyphens/underscores
        parts = re.split(r'[\s\-_]+', name)
        return ''.join(part.capitalize() for part in parts) + 'Agent'


# ============================================================================
# PHASE 7: REGISTRATION
# ============================================================================

class RegistrationPhase(BuilderPhase):
    """
    Phase 7: Register and validate agent

    Input: Dict with generated code files
    Output: ValidationResult
    """

    @property
    def phase_id(self) -> str:
        return "registration"

    @property
    def phase_name(self) -> str:
        return "Registration & Validation"

    def execute(self, input_data: Dict[str, Any]) -> PhaseResult:
        """Register and validate agent"""
        errors = []
        warnings = []

        code_files = input_data.get("code_files", {})
        spec = input_data.get("spec")
        output_path = input_data.get("output_path")

        # Write files
        if output_path:
            from pathlib import Path
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            for filename, content in code_files.items():
                file_path = output_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)

        # Validation would happen here
        validation_results = {
            "files_written": list(code_files.keys()),
            "spec_valid": len(spec.validate()) == 0 if spec else False,
            "output_path": str(output_path) if output_path else None,
        }

        return PhaseResult(
            success=len(errors) == 0,
            output=validation_results,
            errors=errors,
            warnings=warnings,
        )
