"""
Pinecone PWS Brain - Enhanced RAG for Mindrian Agents

This module provides semantic search over 1,400+ PWS course chunks
stored in Pinecone with integrated inference (auto-embedding).

Usage in Agents:
    from mindrian.tools.pinecone_pws_brain import PineconePWSBrain

    brain = PineconePWSBrain()

    # Get context for a query
    context = await brain.get_context("How do I apply JTBD to my startup?")

    # Get framework-specific knowledge
    jtbd_knowledge = await brain.get_framework_knowledge("jtbd", "opportunity scoring")

    # Enhance agent prompt with relevant PWS wisdom
    enhanced_prompt = await brain.enhance_agent_prompt(
        query="Help me validate my idea",
        agent_type="larry"
    )
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PWSSources:
    """Track source documents for citations"""
    title: str
    source: str
    framework: str
    problem_type: str
    score: float


class PineconePWSBrain:
    """
    Pinecone-powered PWS Brain for Mindrian agents.

    Uses integrated inference - Pinecone auto-embeds queries using
    multilingual-e5-large model (same used for ingestion).
    """

    # Index configuration
    INDEX_HOST = "neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io"
    NAMESPACE = "pws-materials"

    # Framework metadata for routing
    FRAMEWORKS = {
        "jtbd": "Jobs To Be Done - understand customer progress",
        "minto-pyramid": "Minto Pyramid - SCQA structured communication",
        "s-curve": "S-Curve Analysis - technology evolution phases",
        "scenario-analysis": "Scenario Analysis - 2x2 future planning",
        "reverse-salient": "Reverse Salient - bottleneck identification",
        "red-teaming": "Red Teaming - adversarial challenge",
        "debono-hats": "De Bono Hats - six thinking perspectives",
        "systems-thinking": "Systems Thinking - feedback loops",
        "pws-validation": "PWS Validation - 4-pillar scorecard",
        "four-lenses": "Four Lenses of Innovation - Gibson framework",
    }

    # Problem type routing
    PROBLEM_TYPES = {
        "un-defined": "Exploration phase - broad discovery tools",
        "ill-defined": "Strategy phase - framing and analysis tools",
        "well-defined": "Execution phase - validation and planning tools",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            # Fallback to hardcoded key (for development only)
            self.api_key = "pcsk_7UvUYB_7eHKr2v1CufsNbWveoV76pnv8BR898eqXfqRv4mxFU7UZjPg97yLPqhVJWYMwVd"

        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-load async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_framework: Optional[str] = None,
        filter_problem_type: Optional[str] = None,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over PWS knowledge base.

        Args:
            query: Natural language query
            top_k: Number of results (default 5)
            filter_framework: Limit to specific framework (e.g., "jtbd")
            filter_problem_type: Limit to problem type (e.g., "ill-defined")
            rerank: Whether to use Pinecone reranking (default True)

        Returns:
            List of matching chunks with metadata and scores
        """
        url = f"https://{self.INDEX_HOST}/records/namespaces/{self.NAMESPACE}/search"

        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

        # Build the query
        request_body = {
            "query": {
                "inputs": {"text": query},
                "topK": top_k * 2 if rerank else top_k,  # Get more for reranking
            },
            "fields": ["content", "title", "category", "type", "source",
                      "tags", "problem_type", "framework_name"],
        }

        # Add filters if specified
        if filter_framework or filter_problem_type:
            filter_conditions = {}
            if filter_framework:
                filter_conditions["framework_name"] = {"$eq": filter_framework}
            if filter_problem_type:
                filter_conditions["problem_type"] = {"$eq": filter_problem_type}
            request_body["query"]["filter"] = filter_conditions

        # Add reranking
        if rerank:
            request_body["rerank"] = {
                "model": "pinecone-rerank-v0",
                "rankFields": ["content"],
                "topN": top_k,
            }

        try:
            response = await self.client.post(url, headers=headers, json=request_body)
            response.raise_for_status()

            data = response.json()
            results = []

            for hit in data.get("result", {}).get("hits", []):
                results.append({
                    "id": hit.get("_id"),
                    "score": hit.get("_score", 0),
                    "content": hit.get("fields", {}).get("content", ""),
                    "title": hit.get("fields", {}).get("title", ""),
                    "framework": hit.get("fields", {}).get("framework_name", ""),
                    "problem_type": hit.get("fields", {}).get("problem_type", ""),
                    "source": hit.get("fields", {}).get("source", ""),
                    "tags": hit.get("fields", {}).get("tags", ""),
                    "type": hit.get("fields", {}).get("type", ""),
                })

            return results

        except Exception as e:
            print(f"Pinecone search error: {e}")
            return []

    async def get_context(
        self,
        query: str,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> str:
        """
        Get formatted context for LLM prompt injection.

        Returns a markdown-formatted context block ready for
        inclusion in agent prompts.
        """
        results = await self.search(query, top_k=top_k)

        if not results:
            return ""

        # Format as context block
        context = "## PWS Knowledge Context\n"
        context += "*Relevant frameworks and methodologies from Problems Worth Solving:*\n\n"

        sources = []
        for i, r in enumerate(results, 1):
            framework_label = self.FRAMEWORKS.get(r["framework"], r["framework"])
            context += f"### [{i}] {r['title']}\n"
            context += f"*Framework: {framework_label} | Type: {r['problem_type']}*\n\n"
            context += f"{r['content']}\n\n"

            sources.append(PWSSources(
                title=r["title"],
                source=r["source"],
                framework=r["framework"],
                problem_type=r["problem_type"],
                score=r["score"],
            ))

        if include_sources:
            context += "---\n**Sources:** "
            context += ", ".join([f"{s.source}" for s in sources[:3]])
            context += "\n"

        return context

    async def get_framework_knowledge(
        self,
        framework: str,
        query: str,
        top_k: int = 3,
    ) -> str:
        """
        Get knowledge specific to a framework.

        Useful for framework agents (JTBD agent, Minto agent, etc.)
        to ground their responses in PWS methodology.
        """
        results = await self.search(
            query,
            top_k=top_k,
            filter_framework=framework
        )

        if not results:
            return f"No specific {framework} content found for this query."

        knowledge = f"## {self.FRAMEWORKS.get(framework, framework)} Knowledge\n\n"
        for r in results:
            knowledge += f"**{r['title']}**\n{r['content']}\n\n"

        return knowledge

    async def get_problem_phase_knowledge(
        self,
        problem_type: str,
        query: str,
        top_k: int = 5,
    ) -> str:
        """
        Get knowledge relevant to a problem phase.

        Used by the Problem Classifier to suggest appropriate tools.
        """
        results = await self.search(
            query,
            top_k=top_k,
            filter_problem_type=problem_type
        )

        if not results:
            return ""

        phase_desc = self.PROBLEM_TYPES.get(problem_type, problem_type)
        knowledge = f"## {phase_desc}\n\n"

        # Group by framework
        by_framework = {}
        for r in results:
            fw = r["framework"]
            if fw not in by_framework:
                by_framework[fw] = []
            by_framework[fw].append(r)

        for fw, chunks in by_framework.items():
            knowledge += f"### {self.FRAMEWORKS.get(fw, fw)}\n"
            for c in chunks[:2]:  # Max 2 per framework
                knowledge += f"- {c['content'][:300]}...\n\n"

        return knowledge

    async def enhance_agent_prompt(
        self,
        query: str,
        agent_type: str = "general",
        base_instructions: str = "",
    ) -> str:
        """
        Enhance an agent's prompt with relevant PWS knowledge.

        This is the main integration point for Mindrian agents.

        Args:
            query: User's query or current topic
            agent_type: Type of agent (larry, devil, minto, jtbd, etc.)
            base_instructions: The agent's base system prompt

        Returns:
            Enhanced prompt with PWS context injected
        """
        # Get relevant context
        context = await self.get_context(query, top_k=4)

        if not context:
            return base_instructions

        # Agent-specific enhancements
        agent_guidance = {
            "larry": "Use this knowledge to ask clarifying questions that help the user apply these frameworks.",
            "devil": "Use this knowledge to identify assumptions and challenge the user's thinking constructively.",
            "minto": "Use this knowledge to structure the user's ideas using SCQA format.",
            "jtbd": "Use this knowledge to help identify the jobs customers are trying to accomplish.",
            "pws": "Use this knowledge to score and validate the user's opportunity.",
            "scenario": "Use this knowledge to build robust scenario analyses.",
            "reverse-salient": "Use this knowledge to identify bottlenecks and constraints.",
        }

        guidance = agent_guidance.get(agent_type,
            "Apply the relevant frameworks and methodologies from this knowledge.")

        enhanced = f"""{base_instructions}

{context}

---
**Agent Guidance:** {guidance}
"""
        return enhanced

    async def suggest_frameworks(self, query: str) -> List[Dict[str, str]]:
        """
        Suggest relevant frameworks based on a query.

        Used by the orchestrator to route to appropriate agents.
        """
        results = await self.search(query, top_k=6, rerank=True)

        # Count framework occurrences
        framework_counts = {}
        for r in results:
            fw = r["framework"]
            if fw not in framework_counts:
                framework_counts[fw] = {"count": 0, "score": 0}
            framework_counts[fw]["count"] += 1
            framework_counts[fw]["score"] += r["score"]

        # Sort by relevance
        suggestions = []
        for fw, data in sorted(
            framework_counts.items(),
            key=lambda x: (x[1]["count"], x[1]["score"]),
            reverse=True
        ):
            suggestions.append({
                "framework": fw,
                "name": self.FRAMEWORKS.get(fw, fw),
                "relevance": data["count"],
            })

        return suggestions[:3]  # Top 3 suggestions


# Singleton instance for easy access
_brain_instance: Optional[PineconePWSBrain] = None

def get_pws_brain() -> PineconePWSBrain:
    """Get the singleton PWS Brain instance"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = PineconePWSBrain()
    return _brain_instance


# Agno Tool wrapper functions
async def search_pws_knowledge(
    query: str,
    framework: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """
    Search PWS knowledge base for relevant frameworks and methodologies.

    Use this tool when you need to ground your response in PWS teachings
    or when the user asks about specific frameworks.

    Args:
        query: What to search for
        framework: Optional - limit to specific framework (jtbd, minto-pyramid, etc.)
        top_k: Number of results (default 5)
    """
    brain = get_pws_brain()

    if framework:
        return await brain.get_framework_knowledge(framework, query, top_k)
    else:
        return await brain.get_context(query, top_k)


async def suggest_pws_frameworks(query: str) -> str:
    """
    Suggest relevant PWS frameworks for a given problem or question.

    Use this when you need to recommend which frameworks might help
    the user with their current challenge.

    Args:
        query: Description of the user's problem or question
    """
    brain = get_pws_brain()
    suggestions = await brain.suggest_frameworks(query)

    if not suggestions:
        return "No specific framework recommendations for this query."

    result = "## Recommended PWS Frameworks\n\n"
    for s in suggestions:
        result += f"- **{s['name']}** (relevance: {s['relevance']})\n"

    return result
