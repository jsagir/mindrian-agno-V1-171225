"""
GraphRAG Module - Hybrid Knowledge Graph + Vector Retrieval

This module provides GraphRAG capabilities for Mindrian/Larry by combining:
1. Pinecone vector search (semantic similarity)
2. Neo4j graph traversal (relationship context)

Components:
- neo4j_client: Async Neo4j client for graph operations
- pinecone_client: Enhanced Pinecone client with graph linking
- hybrid_retriever: Combines both for intelligent retrieval
- tools: Agno-compatible tools for agents

Usage:
    from mindrian.graphrag import HybridGraphRAGRetriever

    retriever = HybridGraphRAGRetriever()
    result = await retriever.retrieve("What is Jobs to Be Done?")
    print(result.merged_context)

With Agno agents:
    from mindrian.graphrag import get_graphrag_tools

    agent = Agent(
        tools=get_graphrag_tools(),
        ...
    )
"""

from .hybrid_retriever import HybridGraphRAGRetriever, HybridResult
from .neo4j_client import Neo4jGraphClient, GraphNode, GraphContext, GraphRelationship
from .pinecone_client import GraphRAGPineconeClient, GraphRAGChunk
from .tools import (
    GraphRAGToolkit,
    get_graphrag_toolkit,
    get_graphrag_tools,
    search_pws_knowledge,
    get_framework_details,
    get_problem_type_guidance,
    find_related_concepts,
    get_framework_chain,
    detect_problem_type,
)

__all__ = [
    # Core retriever
    "HybridGraphRAGRetriever",
    "HybridResult",
    # Neo4j client
    "Neo4jGraphClient",
    "GraphNode",
    "GraphContext",
    "GraphRelationship",
    # Pinecone client
    "GraphRAGPineconeClient",
    "GraphRAGChunk",
    # Agno tools
    "GraphRAGToolkit",
    "get_graphrag_toolkit",
    "get_graphrag_tools",
    "search_pws_knowledge",
    "get_framework_details",
    "get_problem_type_guidance",
    "find_related_concepts",
    "get_framework_chain",
    "detect_problem_type",
]
