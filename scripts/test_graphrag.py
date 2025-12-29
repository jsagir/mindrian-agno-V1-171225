#!/usr/bin/env python3
"""
Test script for GraphRAG implementation.

Tests:
1. Neo4j connection and queries
2. Pinecone connection and search
3. Hybrid retrieval
4. Agno tool integration

Usage:
    python scripts/test_graphrag.py
"""

import os
import sys
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mindrian.graphrag import (
    HybridGraphRAGRetriever,
    Neo4jGraphClient,
    GraphRAGPineconeClient,
    get_graphrag_tools,
)


async def test_neo4j_connection():
    """Test Neo4j connection"""
    print("\n" + "=" * 50)
    print("Testing Neo4j Connection")
    print("=" * 50)

    client = Neo4jGraphClient()

    try:
        healthy = await client.health_check()
        print(f"  Health check: {'PASS' if healthy else 'FAIL'}")

        if healthy:
            # Get stats
            stats = await client.get_graph_stats()
            print(f"\n  Node counts:")
            for label, count in stats.get("node_counts", {}).items():
                if count > 0:
                    print(f"    {label}: {count}")

            # Test entity search
            print(f"\n  Testing entity search...")
            entities = await client.find_entities("JTBD", limit=3)
            print(f"    Found {len(entities)} entities for 'JTBD'")
            for entity in entities:
                print(f"      - {entity.name} ({entity.primary_label})")

        return healthy

    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    finally:
        await client.close()


async def test_pinecone_connection():
    """Test Pinecone connection"""
    print("\n" + "=" * 50)
    print("Testing Pinecone Connection")
    print("=" * 50)

    client = GraphRAGPineconeClient()

    try:
        # Get stats
        stats = await client.get_stats()
        print(f"  Index: {client.INDEX_NAME}")
        print(f"  Host: {client.INDEX_HOST}")

        namespaces = stats.get("namespaces", {})
        print(f"\n  Namespaces:")
        for ns, ns_stats in namespaces.items():
            ns_name = ns if ns else "(default)"
            print(f"    {ns_name}: {ns_stats.get('recordCount', 0)} records")

        # Test search
        print(f"\n  Testing search...")
        results = await client.search("problem solving framework", top_k=3)
        print(f"    Found {len(results)} results")
        for result in results:
            print(f"      - {result.title} ({result.score:.2%})")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    finally:
        await client.close()


async def test_hybrid_retrieval():
    """Test hybrid retrieval"""
    print("\n" + "=" * 50)
    print("Testing Hybrid Retrieval")
    print("=" * 50)

    retriever = HybridGraphRAGRetriever()

    try:
        # Test basic retrieval
        print("\n  Query: 'What is Jobs to Be Done?'")
        result = await retriever.retrieve("What is Jobs to Be Done?", top_k=3)

        print(f"\n  Results:")
        print(f"    Vector chunks: {len(result.vector_chunks)}")
        print(f"    Entities found: {len(result.entities_found)}")
        print(f"    Frameworks: {result.frameworks_found}")

        if result.graph_context:
            print(f"    Graph entities: {len(result.graph_context.entities)}")
            print(f"    Relationships: {len(result.graph_context.relationships)}")

        print(f"\n  Stats: {result.retrieval_stats}")

        # Print sample of merged context
        if result.merged_context:
            print(f"\n  Merged context (first 500 chars):")
            print("  " + "-" * 40)
            print(f"  {result.merged_context[:500]}...")

        # Test framework context
        print("\n\n  Query: Framework context for 'Minto Pyramid'")
        fw_result = await retriever.get_framework_context("Minto Pyramid")
        print(f"    Found {len(fw_result.vector_chunks)} chunks")
        print(f"    Frameworks: {fw_result.frameworks_found}")

        # Test problem type context
        print("\n  Query: Problem type guidance for 'ill-defined'")
        pt_result = await retriever.get_problem_type_context("ill-defined")
        print(f"    Found {len(pt_result.vector_chunks)} chunks")
        print(f"    Frameworks: {pt_result.frameworks_found[:5]}")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await retriever.close()


def test_agno_tools():
    """Test Agno tool integration"""
    print("\n" + "=" * 50)
    print("Testing Agno Tools")
    print("=" * 50)

    try:
        tools = get_graphrag_tools()
        print(f"\n  Available tools: {len(tools)}")

        for tool in tools:
            name = getattr(tool, 'name', getattr(tool, '__name__', 'Unknown'))
            print(f"    - {name}")

        # Test a tool
        print("\n  Testing detect_problem_type tool...")
        from mindrian.graphrag.tools import detect_problem_type
        result = detect_problem_type("I want to understand what customers really need")
        print(f"    Result: {result[:200]}...")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("GraphRAG Implementation Tests")
    print("=" * 60)

    results = {}

    # Test components
    results["neo4j"] = await test_neo4j_connection()
    results["pinecone"] = await test_pinecone_connection()
    results["hybrid"] = await test_hybrid_retrieval()
    results["tools"] = test_agno_tools()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED - check output above")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
