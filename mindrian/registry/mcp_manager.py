"""
MCP Manager - Multi-MCP Orchestration with Sequential Thinking as Core

This module manages connections to multiple MCP servers and provides:
1. Sequential Thinking MCP as the "brain" that drives agent reasoning
2. Neo4j MCP for knowledge graph operations
3. Pinecone MCP for vector search
4. Tavily MCP for web research
5. Extensible architecture for adding new MCPs

The Sequential Thinking MCP acts as a meta-reasoning layer that:
- Plans multi-step operations
- Orchestrates tool usage across MCPs
- Maintains coherent thought chains
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio


class MCPType(str, Enum):
    """Types of MCP servers"""
    SEQUENTIAL_THINKING = "sequential_thinking"  # Core reasoning brain
    NEO4J = "neo4j"                              # Knowledge graph
    PINECONE = "pinecone"                        # Vector search
    TAVILY = "tavily"                            # Web research
    NOTION = "notion"                            # Documentation
    CUSTOM = "custom"                            # User-defined


@dataclass
class MCPServer:
    """MCP Server configuration and state"""
    name: str
    type: MCPType
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    connected: bool = False
    tools: List[str] = field(default_factory=list)

    # Runtime state
    _client: Any = None


@dataclass
class ThinkingStep:
    """A step in Sequential Thinking reasoning"""
    step_number: int
    thought: str
    action: Optional[str] = None
    tool: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    next_step_needed: bool = True


class MCPManager:
    """
    Manages multiple MCP servers with Sequential Thinking as the orchestrator.

    The Sequential Thinking MCP drives the intellectual process:
    1. Receives a task/query
    2. Breaks it into reasoning steps
    3. For each step, decides which MCP tools to invoke
    4. Synthesizes results into coherent output
    """

    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tool_registry: Dict[str, str] = {}  # tool_name -> server_name
        self._thinking_chain: List[ThinkingStep] = []

    def register_server(self, server: MCPServer) -> None:
        """Register an MCP server"""
        self._servers[server.name] = server

        # Register server's tools
        for tool in server.tools:
            self._tool_registry[tool] = server.name

    def register_default_servers(self) -> None:
        """Register default Mindrian MCP servers"""

        # Sequential Thinking - The Brain
        self.register_server(MCPServer(
            name="sequential_thinking",
            type=MCPType.SEQUENTIAL_THINKING,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
            tools=["create_thinking_chain", "add_thought", "get_conclusions"],
        ))

        # Neo4j - Knowledge Graph
        self.register_server(MCPServer(
            name="neo4j",
            type=MCPType.NEO4J,
            command="mcp-neo4j-cypher.exe",
            args=["--db-url", "neo4j+s://5b8df33f.databases.neo4j.io"],
            tools=[
                "run_cypher_query",
                "get_schema",
                "create_node",
                "create_relationship",
            ],
        ))

        # Pinecone - Vector Search
        self.register_server(MCPServer(
            name="pinecone",
            type=MCPType.PINECONE,
            command="npx",
            args=["-y", "@pinecone-database/mcp"],
            tools=[
                "search_records",
                "upsert_records",
                "list_indexes",
                "describe_index",
            ],
        ))

        # Tavily - Web Research
        self.register_server(MCPServer(
            name="tavily",
            type=MCPType.TAVILY,
            command="npx",
            args=["-y", "tavily-mcp@0.1.3"],
            tools=["search", "extract", "news"],
        ))

    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get an MCP server by name"""
        return self._servers.get(name)

    def get_server_for_tool(self, tool_name: str) -> Optional[MCPServer]:
        """Get the MCP server that provides a specific tool"""
        server_name = self._tool_registry.get(tool_name)
        if server_name:
            return self._servers.get(server_name)
        return None

    def list_servers(self) -> List[str]:
        """List all registered server names"""
        return list(self._servers.keys())

    def list_tools(self) -> Dict[str, List[str]]:
        """List all tools organized by server"""
        result = {}
        for name, server in self._servers.items():
            result[name] = server.tools
        return result

    def get_tools_for_skill(self, skill_mcps: List[str]) -> List[str]:
        """Get all tools available for a skill's MCP requirements"""
        tools = []
        for mcp_name in skill_mcps:
            server = self._servers.get(mcp_name)
            if server:
                tools.extend(server.tools)
        return tools

    # Sequential Thinking Integration

    async def think_and_act(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None,
        max_steps: int = 10,
    ) -> Dict[str, Any]:
        """
        Use Sequential Thinking to reason through a task and invoke tools.

        This is the core intellectual driver:
        1. Create thinking chain for the task
        2. For each thought, determine if a tool is needed
        3. Execute tools and incorporate results
        4. Continue until task is complete or max_steps reached

        Args:
            task: The task/query to reason about
            context: Additional context for reasoning
            available_tools: Limit which tools can be used
            max_steps: Maximum reasoning steps

        Returns:
            Dict with thinking_chain, conclusions, and final_answer
        """
        self._thinking_chain = []
        conclusions = []

        # Initialize with task understanding
        step = ThinkingStep(
            step_number=1,
            thought=f"Understanding task: {task}",
            next_step_needed=True,
        )
        self._thinking_chain.append(step)

        # This is a placeholder for actual MCP integration
        # In production, this would invoke the Sequential Thinking MCP
        return {
            "task": task,
            "thinking_chain": self._thinking_chain,
            "conclusions": conclusions,
            "final_answer": None,
            "tools_used": [],
        }

    def create_tool_functions(self, mcp_names: List[str]) -> Dict[str, Callable]:
        """
        Create Agno-compatible tool functions for specified MCPs.

        Returns dict of tool_name -> callable that can be passed to Agno agents.
        """
        tool_funcs = {}

        for mcp_name in mcp_names:
            server = self._servers.get(mcp_name)
            if not server:
                continue

            for tool_name in server.tools:
                # Create wrapper function for each tool
                tool_funcs[tool_name] = self._create_tool_wrapper(server, tool_name)

        return tool_funcs

    def _create_tool_wrapper(self, server: MCPServer, tool_name: str) -> Callable:
        """Create a wrapper function for an MCP tool"""

        async def tool_wrapper(**kwargs) -> Any:
            """Execute MCP tool"""
            # Placeholder - actual implementation would call MCP server
            return {
                "server": server.name,
                "tool": tool_name,
                "params": kwargs,
                "result": f"[{tool_name} result placeholder]",
            }

        tool_wrapper.__name__ = tool_name
        tool_wrapper.__doc__ = f"Execute {tool_name} from {server.name} MCP"
        return tool_wrapper


# Global MCP manager instance
mcp_manager = MCPManager()
mcp_manager.register_default_servers()
