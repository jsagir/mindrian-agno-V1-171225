"""
PWS Brain - Pinecone RAG Implementation

This provides Larry's knowledge brain using Pinecone vector search.
No Neo4j dependency - pure vector RAG for PWS methodology retrieval.

Uses the 'neo4j-knowledge-base' Pinecone index which contains:
- PWS core methodologies
- Course modules (weeks 1-10)
- Frameworks (96+ frameworks)
- Books and references
- Case studies and examples

The index uses 'multilingual-e5-large' for embeddings with integrated inference.
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PWSChunk:
    """A chunk of PWS knowledge"""
    id: str
    content: str
    title: str
    category: str
    score: float
    metadata: Dict[str, Any] = None

    def to_context(self) -> str:
        """Format as context for LLM"""
        return f"### {self.title}\n*({self.category})*\n{self.content}"


class PWSBrainPinecone:
    """
    PWS Brain using Pinecone for vector search.

    This is Larry's knowledge base - containing frameworks, methodologies,
    and structured thinking approaches from the Personal Wisdom System.

    Features:
    - Semantic search across 300+ PWS knowledge chunks
    - Multiple namespaces (pws-materials, frameworks, etc.)
    - Integrated embeddings (no separate embedding API needed)
    - Framework-aware retrieval with category filtering
    """

    # Pinecone index configuration
    INDEX_NAME = "neo4j-knowledge-base"
    INDEX_HOST = "neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io"
    DEFAULT_NAMESPACE = "pws-materials"

    # Categories in the knowledge base
    CATEGORIES = [
        "Core Methodology",
        "Course Module",
        "Framework",
        "Book",
        "Case Study",
        "Summary",
        "Validation Tool",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy load HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json",
                }
            )
        return self._client

    async def search(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "",
        category_filter: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[PWSChunk]:
        """
        Search PWS knowledge base.

        Args:
            query: Search query (natural language)
            top_k: Number of results (default 5)
            namespace: Pinecone namespace ("" for default, "pws-materials" for course)
            category_filter: Filter by category (e.g., "Framework", "Course Module")
            min_score: Minimum similarity score (0.0-1.0)

        Returns:
            List of PWSChunk objects sorted by relevance
        """
        if not self.api_key:
            print("Warning: PINECONE_API_KEY not set, returning empty results")
            return []

        # Build request body for integrated inference
        body = {
            "query": {
                "inputs": {"text": query},
                "top_k": top_k,
            },
            "fields": ["content", "title", "category", "type", "deliverables", "week"],
        }

        # Add namespace if specified
        if namespace:
            body["namespace"] = namespace

        try:
            url = f"https://{self.INDEX_HOST}/records/namespaces/{namespace}/query"
            response = await self.client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

            results = []
            for hit in data.get("result", {}).get("hits", []):
                score = hit.get("_score", 0)
                if score < min_score:
                    continue

                fields = hit.get("fields", {})
                category = fields.get("category", fields.get("type", "Unknown"))

                # Apply category filter if specified
                if category_filter and category.lower() != category_filter.lower():
                    continue

                chunk = PWSChunk(
                    id=hit.get("_id", ""),
                    content=fields.get("content", ""),
                    title=fields.get("title", "PWS Knowledge"),
                    category=category,
                    score=score,
                    metadata={
                        "week": fields.get("week"),
                        "deliverables": fields.get("deliverables"),
                        "type": fields.get("type"),
                    }
                )
                results.append(chunk)

            return results

        except Exception as e:
            print(f"PWS Brain search error: {e}")
            return []

    async def search_all_namespaces(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> List[PWSChunk]:
        """
        Search across all namespaces and merge results.

        This searches both the default namespace and pws-materials,
        then merges and ranks results by score.
        """
        # Search both namespaces
        default_results = await self.search(query, top_k=top_k, namespace="", min_score=min_score)
        pws_results = await self.search(query, top_k=top_k, namespace="pws-materials", min_score=min_score)

        # Merge and dedupe by ID
        seen_ids = set()
        all_results = []

        for chunk in default_results + pws_results:
            if chunk.id not in seen_ids:
                seen_ids.add(chunk.id)
                all_results.append(chunk)

        # Sort by score and limit
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

    async def get_pws_context(
        self,
        query: str,
        top_k: int = 3,
    ) -> str:
        """
        Get formatted PWS context for inclusion in prompts.

        Returns a formatted context block ready for LLM consumption.
        This is the main method Larry uses to get knowledge context.

        Args:
            query: User's question or topic
            top_k: Number of knowledge chunks to retrieve

        Returns:
            Formatted PWS perspective string
        """
        chunks = await self.search_all_namespaces(query, top_k=top_k, min_score=0.4)

        if not chunks:
            return ""

        # Format as context
        context = "## Larry's PWS Knowledge Context\n"
        context += "*Relevant frameworks and methodologies from Personal Wisdom System:*\n\n"

        for i, chunk in enumerate(chunks, 1):
            context += f"**[{i}] {chunk.title}** ({chunk.category}, relevance: {chunk.score:.0%})\n"
            context += f"{chunk.content}\n\n"

        return context

    async def get_framework_info(self, framework_name: str) -> Optional[PWSChunk]:
        """
        Get specific framework information.

        Args:
            framework_name: Name of the framework (e.g., "JTBD", "Minto Pyramid")

        Returns:
            PWSChunk with framework details or None
        """
        results = await self.search(
            f"{framework_name} framework methodology",
            top_k=3,
            category_filter="Framework",
        )

        # Find best match
        for chunk in results:
            if framework_name.lower() in chunk.title.lower():
                return chunk

        return results[0] if results else None

    async def get_problem_type_guidance(self, problem_type: str) -> str:
        """
        Get guidance for a specific problem type.

        Args:
            problem_type: One of "un-defined", "ill-defined", "well-defined"

        Returns:
            Formatted guidance for that problem type
        """
        query_map = {
            "un-defined": "undefined problems future trends scenario planning long-term",
            "ill-defined": "ill-defined problems Jobs to be Done JTBD finding opportunities",
            "well-defined": "well-defined problems issue trees structured problem solving validation",
        }

        query = query_map.get(problem_type.lower(), problem_type)
        chunks = await self.search(query, top_k=3, namespace="pws-materials")

        if not chunks:
            return f"No specific guidance found for {problem_type} problems."

        guidance = f"## Guidance for {problem_type.title()} Problems\n\n"
        for chunk in chunks:
            guidance += f"### {chunk.title}\n{chunk.content}\n\n"

        return guidance

    async def enhance_prompt(
        self,
        user_query: str,
        base_prompt: str = "",
    ) -> str:
        """
        Enhance any prompt with PWS knowledge context.

        Use this to inject Larry's wisdom into agent conversations.

        Args:
            user_query: The user's question/topic
            base_prompt: Existing prompt to enhance

        Returns:
            Enhanced prompt with PWS context
        """
        pws_context = await self.get_pws_context(user_query)

        if not pws_context:
            return base_prompt

        return f"""{base_prompt}

{pws_context}

---
*Apply the PWS knowledge above to inform your response. Reference specific frameworks when relevant.*
"""

    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "index": self.INDEX_NAME,
            "host": self.INDEX_HOST,
            "namespaces": ["", "pws-materials"],
            "embedding_model": "multilingual-e5-large",
            "dimensions": 1024,
            "categories": self.CATEGORIES,
            "status": "connected" if self.api_key else "no_api_key",
        }


# Convenience functions
def get_pws_brain() -> PWSBrainPinecone:
    """Get a configured PWS brain instance"""
    return PWSBrainPinecone()


async def quick_search(query: str, top_k: int = 3) -> List[PWSChunk]:
    """Quick search helper"""
    brain = PWSBrainPinecone()
    return await brain.search_all_namespaces(query, top_k=top_k)
