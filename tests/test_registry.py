"""
Tests for the agent registry and skill loader
"""

import pytest
from pathlib import Path

from mindrian.registry.skill_loader import SkillLoader, SkillDefinition, SkillType
from mindrian.registry.agent_registry import AgentRegistry, AgentDefinition, AgentCategory
from mindrian.registry.mcp_manager import MCPManager, MCPServer, MCPType


class TestSkillLoader:
    """Tests for SkillLoader"""

    def test_parse_skill_md(self):
        """Test parsing a SKILL.md file"""
        content = """---
name: test-skill
type: operator
description: A test skill
version: 1.0.0
triggers:
  - "test trigger"
mcp_tools:
  - neo4j
  - pinecone
---

# Test Skill

This is a test skill with instructions.
"""
        loader = SkillLoader("/nonexistent")
        skill = loader.parse(content)

        assert skill.name == "test-skill"
        assert skill.type == SkillType.OPERATOR
        assert skill.description == "A test skill"
        assert "test trigger" in skill.triggers
        assert "neo4j" in skill.mcp_tools

    def test_get_required_mcps_auto_detect(self):
        """Test auto-detection of MCP requirements"""
        skill = SkillDefinition(
            name="test",
            type=SkillType.OPERATOR,
            description="Test",
            instructions="This skill uses neo4j for knowledge graph and vector search.",
        )

        mcps = skill.get_required_mcps()
        assert "neo4j" in mcps


class TestMCPManager:
    """Tests for MCPManager"""

    def test_register_server(self):
        """Test registering an MCP server"""
        manager = MCPManager()

        server = MCPServer(
            name="test-server",
            type=MCPType.CUSTOM,
            command="test",
            tools=["tool1", "tool2"],
        )

        manager.register_server(server)

        assert manager.get_server("test-server") is not None
        assert "test-server" in manager.list_servers()

    def test_default_servers(self):
        """Test default server registration"""
        manager = MCPManager()
        manager.register_default_servers()

        assert "sequential_thinking" in manager.list_servers()
        assert "neo4j" in manager.list_servers()
        assert "pinecone" in manager.list_servers()

    def test_get_server_for_tool(self):
        """Test finding server by tool"""
        manager = MCPManager()
        manager.register_default_servers()

        server = manager.get_server_for_tool("run_cypher_query")
        assert server is not None
        assert server.name == "neo4j"


class TestAgentRegistry:
    """Tests for AgentRegistry"""

    def test_register_definition(self):
        """Test registering an agent definition"""
        registry = AgentRegistry()

        definition = AgentDefinition(
            name="test-agent",
            category=AgentCategory.FRAMEWORK,
            custom_instructions="Test instructions",
        )

        registry.register(definition)

        assert "test-agent" in registry.list_all()
        assert registry.get("test-agent") is not None

    def test_list_by_category(self):
        """Test listing agents by category"""
        registry = AgentRegistry()

        registry.register(AgentDefinition(
            name="framework1",
            category=AgentCategory.FRAMEWORK,
        ))
        registry.register(AgentDefinition(
            name="conversational1",
            category=AgentCategory.CONVERSATIONAL,
        ))

        frameworks = registry.list_by_category(AgentCategory.FRAMEWORK)
        assert "framework1" in frameworks
        assert "conversational1" not in frameworks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
