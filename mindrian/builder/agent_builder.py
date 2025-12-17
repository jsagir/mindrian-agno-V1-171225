"""
Mindrian Agent Builder - Main Builder Class

Meta-agent factory that transforms SKILL.md definitions into production-ready agents.
Implements the 7-phase workflow.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from agno.agent import Agent
from agno.models.anthropic import Claude

from .schema import AgentSpec, AgentType
from .phases import (
    BuilderPhase,
    PhaseResult,
    SkillAnalysisPhase,
    ArchitecturePhase,
    HandoffProtocolPhase,
    ToolAssemblyPhase,
    Neo4jSchemaPhase,
    CodeGenerationPhase,
    RegistrationPhase,
    SkillDefinition,
)


@dataclass
class BuildResult:
    """Result from complete agent build"""
    success: bool
    spec: Optional[AgentSpec] = None
    code_files: Dict[str, str] = field(default_factory=dict)
    output_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    phase_results: Dict[str, PhaseResult] = field(default_factory=dict)
    duration_seconds: float = 0.0


class AgentBuilder:
    """
    Mindrian Agent Builder

    Transforms SKILL.md definitions into production-ready agents through
    a 7-phase workflow:

    1. SKILL Analysis - Parse and validate SKILL.md
    2. Architecture - Determine agent type, model, config
    3. Handoff Protocol - Configure handoff integration
    4. Tool Assembly - Connect MCPs and custom tools
    5. Neo4j Schema - Generate graph schema
    6. Code Generation - Generate Python implementation
    7. Registration - Validate and register agent

    Usage:
        builder = AgentBuilder()

        # From SKILL.md file
        result = await builder.build_from_skill("/path/to/SKILL.md")

        # From raw YAML
        result = await builder.build_from_yaml(yaml_content)

        # Preview without writing files
        result = await builder.build_from_skill(path, dry_run=True)
    """

    def __init__(
        self,
        output_base_path: str = "/home/jsagi/Mindrian/mindrian-agno/mindrian/agents",
        model: str = "claude-sonnet-4-20250514",
    ):
        self.output_base_path = Path(output_base_path)
        self.model = model

        # Initialize phases
        self.phases: List[BuilderPhase] = [
            SkillAnalysisPhase(),
            ArchitecturePhase(),
            HandoffProtocolPhase(),
            ToolAssemblyPhase(),
            Neo4jSchemaPhase(),
            CodeGenerationPhase(),
            RegistrationPhase(),
        ]

        # Optional AI assistant for intelligent decisions
        self._assistant: Optional[Agent] = None

    async def build_from_skill(
        self,
        skill_path: str,
        dry_run: bool = False,
        category: Optional[str] = None,
    ) -> BuildResult:
        """
        Build agent from SKILL.md file.

        Args:
            skill_path: Path to SKILL.md file
            dry_run: If True, generate but don't write files
            category: Output category (frameworks, conversational, research)

        Returns:
            BuildResult with generated code and metadata
        """
        import time
        start_time = time.time()

        result = BuildResult(success=False)
        phase_data: Any = skill_path

        # Execute phases sequentially
        for phase in self.phases:
            phase_result = phase.execute(phase_data)
            result.phase_results[phase.phase_id] = phase_result

            # Accumulate errors/warnings
            result.errors.extend(phase_result.errors)
            result.warnings.extend(phase_result.warnings)

            # Stop on failure
            if not phase_result.success:
                result.duration_seconds = time.time() - start_time
                return result

            # Update data for next phase
            if phase.phase_id == "code_generation":
                result.code_files = phase_result.output
                result.spec = phase_data  # spec from previous phase

                # Determine output path
                if not dry_run:
                    category = category or self._infer_category(result.spec)
                    result.output_path = str(
                        self.output_base_path / category / result.spec.id.replace("-", "_")
                    )

                    # Pass to registration phase
                    phase_data = {
                        "code_files": result.code_files,
                        "spec": result.spec,
                        "output_path": result.output_path,
                    }
            else:
                phase_data = phase_result.output

        result.success = True
        result.duration_seconds = time.time() - start_time
        return result

    async def build_from_yaml(
        self,
        yaml_content: str,
        dry_run: bool = False,
        category: Optional[str] = None,
    ) -> BuildResult:
        """Build agent from raw YAML content"""
        return await self.build_from_skill(yaml_content, dry_run, category)

    async def build_from_spec(
        self,
        spec: AgentSpec,
        dry_run: bool = False,
        category: Optional[str] = None,
    ) -> BuildResult:
        """
        Build agent from existing AgentSpec.

        Skips phases 1-2, starts from handoff protocol.
        """
        import time
        start_time = time.time()

        result = BuildResult(success=False, spec=spec)
        phase_data: Any = spec

        # Start from phase 3 (handoff protocol)
        for phase in self.phases[2:]:
            phase_result = phase.execute(phase_data)
            result.phase_results[phase.phase_id] = phase_result

            result.errors.extend(phase_result.errors)
            result.warnings.extend(phase_result.warnings)

            if not phase_result.success:
                result.duration_seconds = time.time() - start_time
                return result

            if phase.phase_id == "code_generation":
                result.code_files = phase_result.output
                result.spec = phase_data

                if not dry_run:
                    category = category or self._infer_category(result.spec)
                    result.output_path = str(
                        self.output_base_path / category / result.spec.id.replace("-", "_")
                    )

                    phase_data = {
                        "code_files": result.code_files,
                        "spec": result.spec,
                        "output_path": result.output_path,
                    }
            else:
                phase_data = phase_result.output

        result.success = True
        result.duration_seconds = time.time() - start_time
        return result

    def preview_skill(self, skill_path: str) -> SkillDefinition:
        """
        Preview parsed SKILL.md without building.

        Args:
            skill_path: Path to SKILL.md

        Returns:
            Parsed SkillDefinition
        """
        phase = SkillAnalysisPhase()
        result = phase.execute(skill_path)
        if result.success:
            return result.output
        raise ValueError(f"Failed to parse SKILL.md: {result.errors}")

    def validate_spec(self, spec: AgentSpec) -> List[str]:
        """
        Validate an AgentSpec.

        Returns list of validation errors.
        """
        return spec.validate()

    def _infer_category(self, spec: AgentSpec) -> str:
        """Infer output category from agent type"""
        type_to_category = {
            AgentType.ROLE: "conversational",
            AgentType.OPERATOR: "frameworks",
            AgentType.COLLABORATIVE: "research",
            AgentType.PIPELINE: "pipelines",
            AgentType.GUIDED: "guided",
        }
        return type_to_category.get(spec.type, "frameworks")

    async def register_in_neo4j(self, spec: AgentSpec) -> bool:
        """
        Register agent in Neo4j knowledge graph.

        This enables intelligent framework selection.
        """
        # Would use Neo4j MCP tool here
        cypher = spec.get_neo4j_register_cypher()
        # Execute via MCP
        print(f"Would execute:\n{cypher}")
        return True

    def list_builders(self) -> List[str]:
        """List all available builder phases"""
        return [f"{p.phase_id}: {p.phase_name}" for p in self.phases]


# ============================================================================
# BUILDER SUB-AGENTS (for intelligent decisions)
# ============================================================================

class SkillAnalyzerAgent:
    """Sub-agent for intelligent SKILL.md analysis"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self._agent = Agent(
            name="Skill Analyzer",
            agent_id="skill-analyzer",
            model=Claude(id=model),
            instructions="""
You analyze SKILL.md files to extract structured information.

For each skill, identify:
1. Name and type (role, operator, collaborative, pipeline, guided)
2. Triggers - what keywords/contexts activate this skill
3. Inputs - what the skill needs to work
4. Outputs - what format it produces
5. Methodology - the core framework/process
6. Quality criteria - what makes output good
7. Chaining - what skills should follow

Be thorough and precise. Extract all relevant metadata.
""",
            markdown=True,
        )

    async def analyze(self, skill_content: str) -> Dict[str, Any]:
        """Analyze SKILL.md content"""
        prompt = f"""
Analyze this SKILL.md and extract structured information:

```markdown
{skill_content}
```

Return a structured analysis with:
- name, type, version
- triggers (list)
- inputs (list)
- outputs (list)
- methodology (summary)
- quality_criteria (list)
- chaining (list of related skills)
"""
        response = await self._agent.arun(prompt)
        return {"analysis": response.content}


class ArchitectAgent:
    """Sub-agent for agent architecture decisions"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self._agent = Agent(
            name="Agent Architect",
            agent_id="agent-architect",
            model=Claude(id=model),
            instructions="""
You design agent architectures for Mindrian.

Given a skill definition, determine:
1. Best agent type (ROLE, OPERATOR, COLLABORATIVE, PIPELINE, GUIDED)
2. Appropriate model (claude-sonnet-4 vs claude-opus-4 vs gemini)
3. Required MCP tools
4. Sub-agent structure (if needed)
5. Handoff configuration

Consider:
- Complexity of the task
- Need for tools/research
- Conversation vs. processing focus
- Chaining requirements
""",
            markdown=True,
        )

    async def design(self, skill: SkillDefinition) -> Dict[str, Any]:
        """Design architecture for skill"""
        prompt = f"""
Design an agent architecture for this skill:

Name: {skill.name}
Type: {skill.type}
Triggers: {skill.triggers}
Methodology: {skill.methodology[:500]}...

What should the agent architecture look like?
"""
        response = await self._agent.arun(prompt)
        return {"architecture": response.content}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def build_agent(skill_path: str, dry_run: bool = False) -> BuildResult:
    """Convenience function to build an agent"""
    builder = AgentBuilder()
    return await builder.build_from_skill(skill_path, dry_run)


def preview_skill(skill_path: str) -> SkillDefinition:
    """Convenience function to preview a skill"""
    builder = AgentBuilder()
    return builder.preview_skill(skill_path)
