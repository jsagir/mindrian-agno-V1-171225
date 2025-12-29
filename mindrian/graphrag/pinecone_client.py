"""
Pinecone Client for GraphRAG - Vector search with graph node linking

Enhanced Pinecone client that:
1. Performs semantic search
2. Includes metadata for Neo4j node linking
3. Supports the 'graphrag' namespace
4. Uses integrated inference (multilingual-e5-large)
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class GraphRAGChunk:
    """A chunk with both vector and graph metadata"""
    id: str
    content: str
    title: str
    category: str
    score: float

    # Graph linking metadata
    neo4j_node_id: Optional[str] = None
    neo4j_label: Optional[str] = None
    related_entities: List[str] = field(default_factory=list)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_context(self) -> str:
        """Format as context for LLM"""
        context = f"### {self.title}\n"
        context += f"*({self.category}, relevance: {self.score:.0%})*\n\n"
        context += self.content

        if self.related_entities:
            context += f"\n\n*Related: {', '.join(self.related_entities[:5])}*"

        return context


class GraphRAGPineconeClient:
    """
    Enhanced Pinecone client for GraphRAG.

    Uses the 'neo4j-knowledge-base' index with:
    - 'graphrag' namespace for graph-linked chunks
    - 'pws-materials' namespace for existing PWS content
    - Integrated inference (no separate embedding calls)

    Metadata schema for GraphRAG:
    {
        "content": "...",
        "title": "...",
        "category": "Framework|Concept|Technique|...",
        "neo4j_node_id": "4:xxx:yyy",  # Neo4j element ID
        "neo4j_label": "Framework",
        "related_entities": ["JTBD", "Minto Pyramid", ...],
        "source": "neo4j|document|...",
        "chunk_index": 0,
    }
    """

    # New GraphRAG-optimized index
    INDEX_NAME = "mindrian-graphrag"
    INDEX_HOST = "mindrian-graphrag-bc1849d.svc.aped-4627-b74a.pinecone.io"

    # Legacy index (for backward compatibility with existing PWS content)
    LEGACY_INDEX_NAME = "neo4j-knowledge-base"
    LEGACY_INDEX_HOST = "neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io"

    # Namespaces
    NAMESPACE_GRAPHRAG = "graphrag"
    NAMESPACE_PWS = "pws-materials"
    NAMESPACE_DEFAULT = ""

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

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        namespace: str = "graphrag",
        top_k: int = 5,
        min_score: float = 0.4,
        category_filter: Optional[str] = None,
        include_graph_links: bool = True,
    ) -> List[GraphRAGChunk]:
        """
        Search for similar content using integrated inference.

        Args:
            query: Natural language query
            namespace: Pinecone namespace (graphrag, pws-materials, or "")
            top_k: Number of results
            min_score: Minimum similarity threshold
            category_filter: Filter by category (Framework, Concept, etc.)
            include_graph_links: Include Neo4j linking metadata

        Returns:
            List of GraphRAGChunk with scores and metadata
        """
        if not self.api_key:
            print("Warning: PINECONE_API_KEY not set")
            return []

        # Build request for integrated inference
        body = {
            "query": {
                "inputs": {"text": query},
                "top_k": top_k,
            },
            "fields": [
                "content", "title", "category", "type",
                "neo4j_node_id", "neo4j_label", "related_entities",
                "source", "week", "deliverables",
            ],
        }

        try:
            # Use /search endpoint for integrated inference
            url = f"https://{self.INDEX_HOST}/records/namespaces/{namespace}/search"
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

                # Apply category filter
                if category_filter and category.lower() != category_filter.lower():
                    continue

                chunk = GraphRAGChunk(
                    id=hit.get("_id", ""),
                    content=fields.get("content", ""),
                    title=fields.get("title", "Knowledge"),
                    category=category,
                    score=score,
                    neo4j_node_id=fields.get("neo4j_node_id"),
                    neo4j_label=fields.get("neo4j_label"),
                    related_entities=fields.get("related_entities", []),
                    metadata={
                        "source": fields.get("source"),
                        "week": fields.get("week"),
                        "deliverables": fields.get("deliverables"),
                    }
                )
                results.append(chunk)

            return results

        except Exception as e:
            print(f"Pinecone search error: {e}")
            return []

    async def search_all_namespaces(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.4,
    ) -> List[GraphRAGChunk]:
        """
        Search across all namespaces and merge results.

        Priority:
        1. graphrag namespace (graph-linked chunks)
        2. pws-materials namespace (course content)
        3. default namespace
        """
        import asyncio

        # Search primary namespaces in parallel (skip empty default namespace)
        tasks = [
            self.search(query, namespace=self.NAMESPACE_GRAPHRAG, top_k=top_k, min_score=min_score),
            self.search(query, namespace=self.NAMESPACE_PWS, top_k=top_k, min_score=min_score),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge and dedupe
        seen_ids = set()
        all_chunks = []

        for result in results:
            if isinstance(result, Exception):
                continue
            for chunk in result:
                if chunk.id not in seen_ids:
                    seen_ids.add(chunk.id)
                    all_chunks.append(chunk)

        # Sort by score and limit
        all_chunks.sort(key=lambda x: x.score, reverse=True)
        return all_chunks[:top_k]

    async def upsert_graphrag_chunk(
        self,
        chunk_id: str,
        content: str,
        title: str,
        category: str,
        neo4j_node_id: Optional[str] = None,
        neo4j_label: Optional[str] = None,
        related_entities: List[str] = None,
        source: str = "neo4j",
    ) -> bool:
        """
        Upsert a chunk to the graphrag namespace with Neo4j linking.

        Uses integrated inference - no need to compute embeddings.
        """
        if not self.api_key:
            print("Warning: PINECONE_API_KEY not set")
            return False

        record = {
            "_id": chunk_id,
            "content": content,  # This field is embedded by Pinecone
            "title": title,
            "category": category,
            "source": source,
        }

        if neo4j_node_id:
            record["neo4j_node_id"] = neo4j_node_id
        if neo4j_label:
            record["neo4j_label"] = neo4j_label
        if related_entities:
            record["related_entities"] = related_entities

        try:
            url = f"https://{self.INDEX_HOST}/records/namespaces/{self.NAMESPACE_GRAPHRAG}/upsert"
            response = await self.client.post(url, json={"records": [record]})
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Pinecone upsert error: {e}")
            return False

    async def upsert_batch(
        self,
        records: List[Dict[str, Any]],
        namespace: str = None,
    ) -> int:
        """
        Upsert multiple records in batch.

        Args:
            records: List of record dicts with _id and content
            namespace: Target namespace (default: graphrag)

        Returns:
            Number of records upserted
        """
        namespace = namespace or self.NAMESPACE_GRAPHRAG

        if not self.api_key or not records:
            return 0

        try:
            url = f"https://{self.INDEX_HOST}/records/namespaces/{namespace}/upsert"
            response = await self.client.post(url, json={"records": records})
            response.raise_for_status()
            return len(records)

        except Exception as e:
            print(f"Pinecone batch upsert error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            url = f"https://{self.INDEX_HOST}/describe_index_stats"
            response = await self.client.post(url, json={})
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Pinecone stats error: {e}")
            return {}

    async def get_framework_chunks(
        self,
        framework_name: str,
        top_k: int = 3,
    ) -> List[GraphRAGChunk]:
        """Get chunks specifically about a framework"""
        return await self.search(
            query=f"{framework_name} framework methodology",
            top_k=top_k,
            category_filter="Framework",
        )

    async def get_pws_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """
        Get formatted PWS context for LLM prompts.

        Main method for Larry to get knowledge context.
        """
        chunks = await self.search_all_namespaces(query, top_k=top_k)

        if not chunks:
            return ""

        context = "## PWS Knowledge Context\n\n"
        for chunk in chunks:
            context += chunk.to_context() + "\n\n"

        return context
