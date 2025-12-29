#!/usr/bin/env python3
"""
Demo: How Mindrian Agents Exploit the Pinecone PWS Brain

This shows the integration flow:
1. User asks a question
2. Agent queries PWS Brain for relevant knowledge
3. Agent response is grounded in PWS frameworks
"""

import asyncio
from mindrian.tools.pinecone_pws_brain import (
    PineconePWSBrain,
    search_pws_knowledge,
    suggest_pws_frameworks,
)


async def demo_basic_search():
    """Demo 1: Basic semantic search"""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Semantic Search")
    print("=" * 60)

    brain = PineconePWSBrain()

    query = "How do I understand what customers really want?"
    print(f"\nQuery: {query}\n")

    results = await brain.search(query, top_k=3)

    for r in results:
        print(f"📚 [{r['framework']}] {r['title']}")
        print(f"   Score: {r['score']:.3f}")
        print(f"   {r['content'][:200]}...\n")


async def demo_framework_specific():
    """Demo 2: Framework-specific knowledge"""
    print("\n" + "=" * 60)
    print("DEMO 2: Framework-Specific Knowledge")
    print("=" * 60)

    brain = PineconePWSBrain()

    # Get JTBD-specific knowledge
    print("\n--- JTBD Framework ---")
    knowledge = await brain.get_framework_knowledge(
        framework="jtbd",
        query="opportunity scoring formula",
        top_k=2
    )
    print(knowledge[:500] + "...")


async def demo_agent_prompt_enhancement():
    """Demo 3: Enhancing agent prompts with PWS context"""
    print("\n" + "=" * 60)
    print("DEMO 3: Agent Prompt Enhancement")
    print("=" * 60)

    brain = PineconePWSBrain()

    # Larry's base instructions
    larry_base = """You are Larry, the Clarifier. You help users think clearly about their problems.
    Keep responses under 100 words. Ask one question at a time."""

    # User's query
    user_query = "I have an idea for a new app but I'm not sure if people want it"

    # Enhance Larry's prompt with PWS knowledge
    enhanced = await brain.enhance_agent_prompt(
        query=user_query,
        agent_type="larry",
        base_instructions=larry_base
    )

    print(f"\n--- Original Larry Prompt ---")
    print(larry_base)
    print(f"\n--- Enhanced with PWS Brain ---")
    print(enhanced[:1500] + "...")


async def demo_framework_suggestions():
    """Demo 4: Framework routing based on user query"""
    print("\n" + "=" * 60)
    print("DEMO 4: Framework Suggestions for Routing")
    print("=" * 60)

    brain = PineconePWSBrain()

    queries = [
        "I need to understand why customers aren't buying",
        "How do I structure my pitch deck?",
        "What if AI replaces all jobs in 10 years?",
        "My startup keeps hitting the same bottleneck",
    ]

    for q in queries:
        print(f"\n📝 Query: {q}")
        suggestions = await brain.suggest_frameworks(q)
        for s in suggestions:
            print(f"   → {s['name']} (relevance: {s['relevance']})")


async def demo_problem_phase_routing():
    """Demo 5: Problem phase-based knowledge retrieval"""
    print("\n" + "=" * 60)
    print("DEMO 5: Problem Phase Knowledge")
    print("=" * 60)

    brain = PineconePWSBrain()

    print("\n--- ILL-DEFINED Problems (Strategy Phase) ---")
    knowledge = await brain.get_problem_phase_knowledge(
        problem_type="ill-defined",
        query="validate my business idea",
        top_k=4
    )
    print(knowledge[:800] + "...")


async def demo_agno_tool_functions():
    """Demo 6: Using as Agno tool functions"""
    print("\n" + "=" * 60)
    print("DEMO 6: Agno Tool Integration")
    print("=" * 60)

    # These functions are ready to be registered as Agno tools
    print("\n--- Tool: search_pws_knowledge ---")
    result = await search_pws_knowledge(
        query="milkshake study customer jobs",
        top_k=2
    )
    print(result[:600] + "...")

    print("\n--- Tool: suggest_pws_frameworks ---")
    result = await suggest_pws_frameworks(
        query="I want to challenge my assumptions about the market"
    )
    print(result)


async def main():
    """Run all demos"""
    print("\n" + "🧠" * 30)
    print("  MINDRIAN PWS BRAIN DEMO")
    print("  1,400+ chunks | 13+ frameworks | Semantic Search")
    print("🧠" * 30)

    await demo_basic_search()
    await demo_framework_specific()
    await demo_agent_prompt_enhancement()
    await demo_framework_suggestions()
    await demo_problem_phase_routing()
    await demo_agno_tool_functions()

    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print("""
The PWS Brain enables Mindrian agents to:

1. GROUND responses in actual PWS course content
2. ROUTE to appropriate frameworks based on user needs
3. ENHANCE prompts with relevant methodologies
4. CITE sources from lectures and course materials
5. FILTER by framework or problem phase

Integration points:
- Larry: Gets clarification question techniques
- Devil's Advocate: Gets challenge frameworks
- Framework Agents: Get framework-specific knowledge
- Orchestrator: Gets routing suggestions
""")


if __name__ == "__main__":
    asyncio.run(main())
