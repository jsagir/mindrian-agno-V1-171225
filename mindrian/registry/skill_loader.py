"""
Skill Loader - Parse SKILL.md files and convert to agent configurations

SKILL.md Format:
---
name: skill-name
type: operator|role|guided|collaborative|pipeline|tool
description: ...
triggers: [...]
inputs: [...]
outputs: [...]
mcp_tools: [neo4j, pinecone, tavily]  # Optional: MCPs this skill needs
---

# Markdown content (instructions for the agent)
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class SkillType(str, Enum):
    """Types of skills in Mindrian"""
    OPERATOR = "operator"          # Framework operators (Minto, JTBD, PWS)
    ROLE = "role"                  # Conversational roles (Larry, Devil)
    GUIDED = "guided"              # Step-by-step guides
    COLLABORATIVE = "collaborative"  # Multi-perspective (De Bono)
    PIPELINE = "pipeline"          # Sequential processing
    TOOL = "tool"                  # Atomic tools
    ORCHESTRATOR = "orchestrator"  # Meta-orchestration


@dataclass
class SkillDefinition:
    """Parsed SKILL.md definition"""

    name: str
    type: SkillType
    description: str
    instructions: str  # Full markdown content
    version: str = "1.0.0"
    triggers: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    mcp_tools: List[str] = field(default_factory=list)
    behavioral_rules: List[str] = field(default_factory=list)
    tone: str = ""
    chaining: List[str] = field(default_factory=list)
    default_role: Optional[str] = None

    # Metadata
    file_path: Optional[Path] = None
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)

    def to_agent_instructions(self) -> str:
        """Convert skill to agent system instructions"""
        return self.instructions

    def get_required_mcps(self) -> List[str]:
        """Get list of MCP tools this skill needs"""
        # Auto-detect from content if not specified
        if self.mcp_tools:
            return self.mcp_tools

        detected = []
        content_lower = self.instructions.lower()

        if "neo4j" in content_lower or "cypher" in content_lower:
            detected.append("neo4j")
        if "pinecone" in content_lower or "vector" in content_lower:
            detected.append("pinecone")
        if "research" in content_lower or "web" in content_lower:
            detected.append("tavily")
        if "thinking" in content_lower or "reasoning" in content_lower:
            detected.append("sequential_thinking")

        return detected


class SkillLoader:
    """Load and parse SKILL.md files from directory"""

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    def __init__(self, skills_path: str):
        self.skills_path = Path(skills_path)
        self._cache: Dict[str, SkillDefinition] = {}

    def load_all(self) -> Dict[str, SkillDefinition]:
        """Load all SKILL.md files from skills directory"""
        if not self.skills_path.exists():
            return {}

        for skill_file in self.skills_path.rglob("SKILL.md"):
            try:
                skill = self.load_file(skill_file)
                self._cache[skill.name] = skill
            except Exception as e:
                print(f"Error loading {skill_file}: {e}")

        return self._cache

    def load_file(self, path: Path) -> SkillDefinition:
        """Load a single SKILL.md file"""
        content = path.read_text(encoding="utf-8")
        return self.parse(content, path)

    def parse(self, content: str, file_path: Optional[Path] = None) -> SkillDefinition:
        """Parse SKILL.md content into SkillDefinition"""
        # Extract frontmatter
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("No YAML frontmatter found in SKILL.md")

        frontmatter_yaml = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_yaml)

        # Get markdown content after frontmatter
        instructions = content[match.end():].strip()

        # Parse skill type
        skill_type = SkillType(frontmatter.get("type", "operator"))

        return SkillDefinition(
            name=frontmatter.get("name", "unknown"),
            type=skill_type,
            description=frontmatter.get("description", ""),
            instructions=instructions,
            version=frontmatter.get("version", "1.0.0"),
            triggers=frontmatter.get("triggers", []),
            inputs=frontmatter.get("inputs", []),
            outputs=frontmatter.get("outputs", []),
            mcp_tools=frontmatter.get("mcp_tools", []),
            behavioral_rules=frontmatter.get("behavioral_rules", []),
            tone=frontmatter.get("tone", ""),
            chaining=frontmatter.get("chaining", []),
            default_role=frontmatter.get("default_role"),
            file_path=file_path,
            raw_frontmatter=frontmatter,
        )

    def get(self, name: str) -> Optional[SkillDefinition]:
        """Get a skill by name"""
        if not self._cache:
            self.load_all()
        return self._cache.get(name)

    def get_by_type(self, skill_type: SkillType) -> List[SkillDefinition]:
        """Get all skills of a specific type"""
        if not self._cache:
            self.load_all()
        return [s for s in self._cache.values() if s.type == skill_type]

    def get_by_trigger(self, trigger: str) -> List[SkillDefinition]:
        """Find skills that match a trigger"""
        if not self._cache:
            self.load_all()

        matches = []
        trigger_lower = trigger.lower()
        for skill in self._cache.values():
            for t in skill.triggers:
                if trigger_lower in t.lower():
                    matches.append(skill)
                    break
        return matches

    def list_all(self) -> List[str]:
        """List all available skill names"""
        if not self._cache:
            self.load_all()
        return list(self._cache.keys())
