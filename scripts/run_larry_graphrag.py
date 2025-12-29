#!/usr/bin/env python3
"""
Run Larry with GraphRAG - Interactive CLI

This script runs Larry (The Clarifier) with full GraphRAG capabilities,
combining Pinecone vector search with Neo4j graph traversal.

Usage:
    python scripts/run_larry_graphrag.py

    # Or with specific mode
    python scripts/run_larry_graphrag.py --mode explore
"""

import os
import sys
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.anthropic import Claude

# Import GraphRAG tools
from mindrian.graphrag import get_graphrag_tools


def create_larry_with_graphrag(model_provider: str = "gemini") -> Agent:
    """
    Create Larry agent with GraphRAG tools.

    Args:
        model_provider: "gemini" or "anthropic"
    """
    # Get GraphRAG tools
    graphrag_tools = get_graphrag_tools()

    # Larry's system prompt
    system_prompt = """You are Larry, The Clarifier - the default conversational agent in Mindrian.

## Your Role
Your job is NOT to provide answers - it's to ensure the person understands their own problem deeply.
You ask penetrating questions before providing solutions.

## The Three Questions
You aren't done until you know:
1. What is the actual problem? (not the symptom, not the solution)
2. Who has this problem? (specific stakeholders)
3. What does success look like? (measurable outcomes)

## Problem Classification
- **Un-defined**: Future-focused, high uncertainty, exploring trends (use Scenario Planning, Trending to Absurd)
- **Ill-defined**: Customer/market focused, needs discovery (use JTBD, Design Thinking)
- **Well-defined**: Execution focused, optimization (use Issue Trees, MECE)

## Your GraphRAG Tools
You have access to powerful knowledge retrieval tools:

1. `search_pws_knowledge(query)` - Search frameworks and methodologies
2. `get_framework_details(name)` - Get details about a specific framework
3. `get_problem_type_guidance(type)` - Get frameworks for un/ill/well-defined problems
4. `find_related_concepts(concept)` - Explore connected concepts via knowledge graph
5. `get_framework_chain(framework)` - Find recommended framework sequences
6. `detect_problem_type(message)` - Classify the user's problem type

## Behavioral Rules
- Keep responses SHORT (under 100 words unless explaining a framework)
- Ask ONE question at a time
- Challenge assumptions gently but firmly
- Park tangential ideas for later ("Let's note that and come back to it")
- NEVER provide solutions until the problem is crystal clear
- Use your GraphRAG tools to retrieve relevant frameworks when needed

## Question Techniques
- **Woah Question**: Creates pause and reflection ("What would change if that weren't true?")
- **Digging Question**: Goes deeper ("What's behind that?")
- **Clarifying Question**: Sharpens understanding ("When you say X, do you mean...?")
- **Challenge Question**: Tests assumptions ("How do you know that's true?")
- **Beautiful Question**: Opens new possibilities ("What if we...?")

Start by understanding what brought the user here today."""

    # Select model
    if model_provider == "haiku":
        model = Claude(id="claude-3-5-haiku-20241022")
    elif model_provider == "anthropic":
        model = Claude(id="claude-sonnet-4-20250514")
    else:
        model = Gemini(id="gemini-2.0-flash")

    # Create agent
    agent = Agent(
        name="Larry",
        model=model,
        instructions=system_prompt,
        tools=graphrag_tools,
        markdown=True,
        show_tool_calls=True,
    )

    return agent


async def chat_loop(agent: Agent):
    """Interactive chat loop with Larry"""
    print("\n" + "=" * 60)
    print("  Larry - The Clarifier (with GraphRAG)")
    print("=" * 60)
    print("\nI'm Larry. I help you understand your problem deeply before")
    print("jumping to solutions. What's on your mind today?")
    print("\n(Type 'quit' to exit, 'tools' to see available tools)")
    print("-" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'quit':
                print("\nGoodbye! Remember: clarity before solutions.")
                break

            if user_input.lower() == 'tools':
                print("\n📦 Available GraphRAG Tools:")
                print("  • search_pws_knowledge - Search frameworks")
                print("  • get_framework_details - Framework deep-dive")
                print("  • get_problem_type_guidance - Problem type frameworks")
                print("  • find_related_concepts - Graph exploration")
                print("  • get_framework_chain - Framework sequences")
                print("  • detect_problem_type - Classify problems\n")
                continue

            # Get response from Larry
            response = agent.run(user_input)

            print(f"\nLarry: {response.content}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Larry with GraphRAG")
    parser.add_argument(
        "--model",
        choices=["gemini", "anthropic", "haiku"],
        default="haiku",
        help="Model provider (default: haiku)"
    )

    args = parser.parse_args()

    # Check for API keys
    if args.model == "gemini" and not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable required")
        print("Set it with: export GOOGLE_API_KEY=your_key")
        sys.exit(1)

    if args.model in ["anthropic", "haiku"] and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable required")
        sys.exit(1)

    # Create Larry
    print("Initializing Larry with GraphRAG...")
    agent = create_larry_with_graphrag(args.model)

    # Run chat loop
    asyncio.run(chat_loop(agent))


if __name__ == "__main__":
    main()
