"""
GraphRAG Tools for Agno Agents

These tools provide GraphRAG capabilities to Larry and other Mindrian agents.
They wrap the hybrid retriever to enable:
- Semantic knowledge retrieval
- Graph-based context expansion
- Framework chain discovery
- Problem type guidance

Usage with Agno:
    from mindrian.graphrag.tools import get_graphrag_toolkit

    agent = Agent(
        tools=get_graphrag_toolkit(),
        ...
    )
"""

import asyncio
from typing import Dict, List, Optional, Any
from functools import wraps

from agno.tools import tool, Toolkit

from .hybrid_retriever import HybridGraphRAGRetriever, HybridResult
from .neo4j_client import Neo4jGraphClient
from .pinecone_client import GraphRAGPineconeClient


# Global retriever instance (lazy loaded)
_retriever: Optional[HybridGraphRAGRetriever] = None


def get_retriever() -> HybridGraphRAGRetriever:
    """Get or create the global retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = HybridGraphRAGRetriever()
    return _retriever


def run_async(coro):
    """Run async coroutine in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@tool(name="search_pws_knowledge")
def search_pws_knowledge(
    query: str,
    top_k: int = 5,
    include_graph: bool = True,
) -> str:
    """
    Search Larry's PWS (Personal Wisdom System) knowledge base.

    This performs hybrid retrieval combining:
    - Semantic vector search (finds similar content)
    - Knowledge graph traversal (finds related concepts)

    Use this tool when:
    - User asks about frameworks, methodologies, or techniques
    - You need context about a PWS concept
    - You want to find related knowledge

    Args:
        query: Natural language search query
        top_k: Number of results to return (default 5)
        include_graph: Whether to include graph expansion (default True)

    Returns:
        Formatted knowledge context with relevant frameworks and concepts
    """
    retriever = get_retriever()

    async def _search():
        result = await retriever.retrieve(
            query=query,
            top_k=top_k,
            include_graph_expansion=include_graph,
        )
        return result.merged_context

    return run_async(_search())


@tool(name="get_framework_details")
def get_framework_details(
    framework_name: str,
    include_chain: bool = True,
) -> str:
    """
    Get detailed information about a specific framework.

    This retrieves comprehensive context about a framework including:
    - Description and methodology
    - Key concepts and techniques
    - Related frameworks (chains)
    - When to use it

    Use this tool when:
    - User asks about a specific framework (JTBD, Minto Pyramid, etc.)
    - You need to explain how to apply a framework
    - You want to recommend framework chains

    Args:
        framework_name: Name of the framework (e.g., "JTBD", "Minto Pyramid", "Cynefin")
        include_chain: Whether to include related framework chains (default True)

    Returns:
        Detailed framework context including related concepts and chains
    """
    retriever = get_retriever()

    async def _get_framework():
        result = await retriever.get_framework_context(
            framework_name=framework_name,
            include_chain=include_chain,
        )
        return result.merged_context

    return run_async(_get_framework())


@tool(name="get_problem_type_guidance")
def get_problem_type_guidance(
    problem_type: str,
) -> str:
    """
    Get recommended frameworks and guidance for a problem type.

    Problem types in PWS:
    - "un-defined": Future-focused, high uncertainty, trends
    - "ill-defined": Customer/market focused, needs discovery
    - "well-defined": Execution focused, optimization

    Use this tool when:
    - You've classified a user's problem type
    - You need to recommend appropriate frameworks
    - User asks "what approach should I use?"

    Args:
        problem_type: One of "un-defined", "ill-defined", or "well-defined"

    Returns:
        Recommended frameworks and methodology for that problem type
    """
    retriever = get_retriever()

    async def _get_guidance():
        result = await retriever.get_problem_type_context(problem_type)
        return result.merged_context

    return run_async(_get_guidance())


@tool(name="find_related_concepts")
def find_related_concepts(
    concept: str,
    depth: int = 1,
) -> str:
    """
    Find concepts and entities related to a given topic.

    This uses knowledge graph traversal to discover:
    - Related frameworks
    - Connected concepts
    - Techniques and tools
    - Authors and sources

    Use this tool when:
    - User mentions a concept and you want more context
    - You want to explore connections between ideas
    - Building a comprehensive answer about a topic

    Args:
        concept: The concept or topic to explore
        depth: How many relationship hops to traverse (default 1)

    Returns:
        Related concepts and their connections
    """
    retriever = get_retriever()

    async def _find_related():
        # First find entities matching the concept
        entities = await retriever.neo4j.find_entities(concept, limit=3)

        if not entities:
            return f"No entities found matching '{concept}'"

        # Get related entities for each found entity
        all_context = []
        for entity in entities[:2]:
            context = await retriever.neo4j.get_related_entities(
                entity.id,
                depth=depth,
                limit=15,
            )
            all_context.append(f"## {entity.name} ({entity.primary_label})\n")
            all_context.append(context.to_context_string())

        return "\n\n".join(all_context)

    return run_async(_find_related())


@tool(name="get_framework_chain")
def get_framework_chain(
    starting_framework: str,
) -> str:
    """
    Get recommended framework chains starting from a framework.

    Framework chains show which frameworks work well together, like:
    - Cynefin → JTBD → Business Model Canvas
    - Minto Pyramid → Issue Trees → Decision Matrix

    Use this tool when:
    - User is applying a framework and needs next steps
    - You want to recommend a complete methodology path
    - Planning a multi-framework approach

    Args:
        starting_framework: The framework to find chains for

    Returns:
        Framework chains with recommendations
    """
    retriever = get_retriever()

    async def _get_chain():
        chains = await retriever.neo4j.find_framework_chain(starting_framework)

        if not chains:
            return f"No framework chains found starting from '{starting_framework}'"

        result = [f"## Framework Chains from {starting_framework}\n"]

        for i, chain in enumerate(chains, 1):
            chain_names = [node.name for node in chain]
            result.append(f"**Chain {i}:** {' → '.join(chain_names)}")

            # Add brief descriptions
            for node in chain:
                desc = node.description[:100] + "..." if len(node.description) > 100 else node.description
                result.append(f"  - **{node.name}**: {desc}")
            result.append("")

        return "\n".join(result)

    return run_async(_get_chain())


@tool(name="detect_problem_type")
def detect_problem_type(
    user_message: str,
) -> str:
    """
    Analyze a user message to detect the problem type.

    This helps classify whether the user's problem is:
    - un-defined: Future-focused, trends, scenarios
    - ill-defined: Customer needs, opportunities
    - well-defined: Clear execution, optimization

    Use this tool when:
    - Starting a new conversation to understand the problem
    - User describes their situation vaguely
    - You need to route to appropriate frameworks

    Args:
        user_message: The user's message or problem description

    Returns:
        Detected problem type with confidence and recommendations
    """
    retriever = get_retriever()
    problem_type = retriever.detect_problem_type(user_message)

    if problem_type:
        return f"""
## Problem Type Analysis

**Detected Type:** {problem_type}

**Characteristics:**
- un-defined: High uncertainty about the future, exploring trends and possibilities
- ill-defined: Understanding customer needs, finding opportunities
- well-defined: Clear problem with known solutions, execution focus

**Recommended Approach:** Use `get_problem_type_guidance('{problem_type}')` for specific frameworks
"""
    else:
        return """
## Problem Type Analysis

**Result:** Unable to determine problem type from the message.

**Next Steps:**
1. Ask clarifying questions about the user's situation
2. Understand the time horizon (short-term vs long-term)
3. Identify whether the challenge is understanding needs vs executing solutions
"""


class GraphRAGToolkit(Toolkit):
    """
    Agno Toolkit containing all GraphRAG tools.

    Usage:
        from mindrian.graphrag.tools import GraphRAGToolkit

        agent = Agent(
            tools=[GraphRAGToolkit()],
            ...
        )
    """

    def __init__(self):
        super().__init__(name="graphrag")

        # Register all tools
        self.register(search_pws_knowledge)
        self.register(get_framework_details)
        self.register(get_problem_type_guidance)
        self.register(find_related_concepts)
        self.register(get_framework_chain)
        self.register(detect_problem_type)


def get_graphrag_toolkit() -> GraphRAGToolkit:
    """Get the GraphRAG toolkit for Agno agents"""
    return GraphRAGToolkit()


def get_graphrag_tools() -> List:
    """Get list of GraphRAG tools for Agno agents"""
    return [
        search_pws_knowledge,
        get_framework_details,
        get_problem_type_guidance,
        find_related_concepts,
        get_framework_chain,
        detect_problem_type,
    ]


# Cleanup function for graceful shutdown
async def cleanup():
    """Clean up global retriever connections"""
    global _retriever
    if _retriever:
        await _retriever.close()
        _retriever = None
