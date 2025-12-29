#!/usr/bin/env python3
"""
Simple GraphRAG Agent Example

Shows how to create a minimal Agno agent with GraphRAG tools.
This is the simplest way to get started.

Usage:
    python scripts/example_graphrag_agent.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.agent import Agent
from agno.models.google import Gemini
from mindrian.graphrag import get_graphrag_tools


# Create a simple agent with GraphRAG
agent = Agent(
    name="PWS Assistant",
    model=Gemini(id="gemini-2.0-flash"),
    instructions="""You are a Problem Worth Solving (PWS) assistant.

You help users understand frameworks and methodologies for structured thinking.
Use your tools to search for relevant knowledge when users ask about:
- Frameworks (JTBD, Cynefin, Minto Pyramid, etc.)
- Problem types (un-defined, ill-defined, well-defined)
- Techniques and methodologies

Always search for knowledge before answering framework questions.""",
    tools=get_graphrag_tools(),
    markdown=True,
    show_tool_calls=True,
)


if __name__ == "__main__":
    print("PWS Assistant with GraphRAG")
    print("=" * 40)

    # Example queries
    queries = [
        "What is Jobs to Be Done?",
        "What frameworks help with uncertain future problems?",
        "How do I structure my thinking for executive communication?",
    ]

    for query in queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 40)
        response = agent.run(query)
        print(f"📝 Response:\n{response.content}\n")
