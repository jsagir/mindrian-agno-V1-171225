"""
Hybrid GraphRAG Retriever - Combines Vector Search + Graph Traversal

This is the core retriever for Mindrian/Larry that implements:
1. Semantic search via Pinecone (find similar content)
2. Entity extraction from queries
3. Graph expansion via Neo4j (follow relationships)
4. Result merging and ranking

The retrieval flow:
1. User query → Pinecone semantic search
2. Extract entities from query → Neo4j entity lookup
3. Expand found entities → Neo4j relationship traversal
4. Merge vector results + graph context
5. Return unified context for LLM

This enables Larry to:
- Find semantically related content (vector)
- Discover framework chains (graph)
- Get related concepts/techniques (graph)
- Understand problem type connections (graph)
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .neo4j_client import Neo4jGraphClient, GraphNode, GraphContext
from .pinecone_client import GraphRAGPineconeClient, GraphRAGChunk


@dataclass
class HybridResult:
    """Combined result from hybrid retrieval"""
    # Vector search results
    vector_chunks: List[GraphRAGChunk] = field(default_factory=list)

    # Graph context
    graph_context: Optional[GraphContext] = None

    # Merged context string for LLM
    merged_context: str = ""

    # Metadata
    query: str = ""
    entities_found: List[str] = field(default_factory=list)
    frameworks_found: List[str] = field(default_factory=list)
    retrieval_stats: Dict[str, Any] = field(default_factory=dict)

    def has_results(self) -> bool:
        """Check if any results were found"""
        return bool(self.vector_chunks) or bool(self.graph_context and self.graph_context.entities)

    def get_framework_names(self) -> List[str]:
        """Get all framework names from results"""
        frameworks = set(self.frameworks_found)

        # From vector chunks
        for chunk in self.vector_chunks:
            if chunk.category == "Framework":
                frameworks.add(chunk.title)

        # From graph entities
        if self.graph_context:
            for entity in self.graph_context.entities:
                if "Framework" in entity.labels:
                    frameworks.add(entity.name)

        return list(frameworks)


class HybridGraphRAGRetriever:
    """
    Hybrid retriever combining Pinecone vector search with Neo4j graph traversal.

    This is the main retrieval engine for Larry and other Mindrian agents.
    It provides rich context by combining:
    - Semantic similarity (what's related to the query?)
    - Graph relationships (what's connected in the knowledge graph?)

    Usage:
        retriever = HybridGraphRAGRetriever()
        result = await retriever.retrieve("What is Jobs to Be Done?")
        print(result.merged_context)  # Use in LLM prompt
    """

    # Keywords that suggest framework-specific queries
    FRAMEWORK_KEYWORDS = [
        "framework", "methodology", "approach", "technique", "method",
        "tool", "model", "system", "process", "strategy",
    ]

    # Problem type keywords for routing
    PROBLEM_TYPE_KEYWORDS = {
        "un-defined": ["future", "trend", "scenario", "long-term", "predict", "forecast"],
        "ill-defined": ["customer", "need", "want", "job", "opportunity", "why"],
        "well-defined": ["solve", "implement", "execute", "optimize", "measure"],
    }

    def __init__(
        self,
        pinecone_client: Optional[GraphRAGPineconeClient] = None,
        neo4j_client: Optional[Neo4jGraphClient] = None,
        enable_graph: bool = True,
        enable_vector: bool = True,
    ):
        self.pinecone = pinecone_client or GraphRAGPineconeClient()
        self.neo4j = neo4j_client or Neo4jGraphClient()
        self.enable_graph = enable_graph
        self.enable_vector = enable_vector

    async def close(self):
        """Clean up connections"""
        await self.pinecone.close()
        await self.neo4j.close()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        include_graph_expansion: bool = True,
        min_score: float = 0.4,
        graph_depth: int = 1,
    ) -> HybridResult:
        """
        Perform hybrid retrieval combining vector search and graph traversal.

        Args:
            query: User's natural language query
            top_k: Number of vector results
            include_graph_expansion: Whether to expand via graph
            min_score: Minimum vector similarity threshold
            graph_depth: How many hops in graph traversal

        Returns:
            HybridResult with merged context
        """
        result = HybridResult(query=query)

        # Step 1: Parallel initial retrieval
        tasks = []

        if self.enable_vector:
            tasks.append(self._vector_search(query, top_k, min_score))

        if self.enable_graph:
            tasks.append(self._entity_extraction(query))

        initial_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process vector results
        vector_chunks = []
        if self.enable_vector and len(initial_results) > 0:
            if not isinstance(initial_results[0], Exception):
                vector_chunks = initial_results[0]
                result.vector_chunks = vector_chunks

        # Process entity extraction
        entities = []
        if self.enable_graph:
            entity_idx = 1 if self.enable_vector else 0
            if len(initial_results) > entity_idx:
                if not isinstance(initial_results[entity_idx], Exception):
                    entities = initial_results[entity_idx]
                    result.entities_found = [e.name for e in entities]

        # Step 2: Graph expansion (if entities found)
        if self.enable_graph and include_graph_expansion and entities:
            result.graph_context = await self._graph_expansion(entities, graph_depth)

        # Step 3: Extract framework names
        result.frameworks_found = self._extract_frameworks(vector_chunks, entities, result.graph_context)

        # Step 4: Merge into unified context
        result.merged_context = self._merge_context(result)

        # Stats
        result.retrieval_stats = {
            "vector_results": len(vector_chunks),
            "entities_found": len(entities),
            "graph_entities": len(result.graph_context.entities) if result.graph_context else 0,
            "graph_relationships": len(result.graph_context.relationships) if result.graph_context else 0,
            "frameworks_found": len(result.frameworks_found),
        }

        return result

    async def _vector_search(
        self,
        query: str,
        top_k: int,
        min_score: float,
    ) -> List[GraphRAGChunk]:
        """Perform Pinecone vector search across namespaces"""
        return await self.pinecone.search_all_namespaces(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )

    async def _entity_extraction(self, query: str) -> List[GraphNode]:
        """Extract entities from query using Neo4j search"""
        # Extract potential entity keywords
        keywords = self._extract_keywords(query)

        if not keywords:
            # Fall back to full query search
            return await self.neo4j.find_entities(query, limit=5)

        # Search by extracted keywords
        return await self.neo4j.search_by_keywords(keywords, limit=10)

    async def _graph_expansion(
        self,
        entities: List[GraphNode],
        depth: int,
    ) -> GraphContext:
        """Expand entities via graph traversal"""
        all_entities = []
        all_relationships = []
        seen_ids = set()

        for entity in entities[:5]:  # Limit to top 5 entities
            if entity.id in seen_ids:
                continue
            seen_ids.add(entity.id)

            # Get related entities
            context = await self.neo4j.get_related_entities(
                entity.id,
                depth=depth,
                limit=10,
            )

            for e in context.entities:
                if e.id not in seen_ids:
                    seen_ids.add(e.id)
                    all_entities.append(e)

            all_relationships.extend(context.relationships)

        return GraphContext(
            entities=entities + all_entities,
            relationships=all_relationships,
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query"""
        # Remove common words
        stop_words = {
            "what", "is", "the", "a", "an", "how", "do", "does", "can", "could",
            "would", "should", "tell", "me", "about", "explain", "describe",
            "help", "with", "for", "to", "in", "on", "of", "and", "or", "but",
            "i", "my", "we", "our", "you", "your", "it", "its", "this", "that",
        }

        # Tokenize and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        keywords = [w for w in words if w not in stop_words]

        # Also extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', query)
        keywords.extend(quoted)

        # Look for known framework patterns
        framework_patterns = [
            r'(?i)(jtbd|jobs?.to.be.done)',
            r'(?i)(minto|pyramid)',
            r'(?i)(cynefin)',
            r'(?i)(design.thinking)',
            r'(?i)(scenario.analysis)',
            r'(?i)(business.model.canvas|bmc)',
            r'(?i)(golden.circle)',
            r'(?i)(issue.tree)',
            r'(?i)(devil.?s?.advocate)',
        ]

        for pattern in framework_patterns:
            matches = re.findall(pattern, query)
            keywords.extend([m if isinstance(m, str) else m[0] for m in matches])

        return list(set(keywords))

    def _extract_frameworks(
        self,
        vector_chunks: List[GraphRAGChunk],
        entities: List[GraphNode],
        graph_context: Optional[GraphContext],
    ) -> List[str]:
        """Extract framework names from all results"""
        frameworks = set()

        # From vector chunks
        for chunk in vector_chunks:
            if chunk.category == "Framework":
                frameworks.add(chunk.title)

        # From initial entities
        for entity in entities:
            if "Framework" in entity.labels:
                frameworks.add(entity.name)

        # From graph context
        if graph_context:
            for entity in graph_context.entities:
                if "Framework" in entity.labels:
                    frameworks.add(entity.name)

        return list(frameworks)

    def _merge_context(self, result: HybridResult) -> str:
        """Merge vector and graph results into unified context"""
        sections = []

        # Header
        sections.append("# Knowledge Context for Query")
        sections.append(f"*Query: {result.query}*\n")

        # Vector search results
        if result.vector_chunks:
            sections.append("## Relevant Knowledge (Semantic Search)\n")
            for i, chunk in enumerate(result.vector_chunks, 1):
                sections.append(f"### [{i}] {chunk.title}")
                sections.append(f"*({chunk.category}, relevance: {chunk.score:.0%})*\n")
                sections.append(chunk.content)

                if chunk.related_entities:
                    sections.append(f"\n*Related: {', '.join(chunk.related_entities[:5])}*")
                sections.append("")

        # Graph context
        if result.graph_context:
            graph_str = result.graph_context.to_context_string()
            if graph_str.strip():
                sections.append(graph_str)

        # Framework summary
        if result.frameworks_found:
            sections.append("\n## Frameworks Referenced")
            sections.append(f"*{', '.join(result.frameworks_found)}*")

        return "\n".join(sections)

    async def get_framework_context(
        self,
        framework_name: str,
        include_chain: bool = True,
    ) -> HybridResult:
        """
        Get comprehensive context for a specific framework.

        This is useful when Larry needs to explain or apply a framework.
        """
        result = HybridResult(query=f"Framework: {framework_name}")

        # Vector search for framework content
        chunks = await self.pinecone.get_framework_chunks(framework_name, top_k=3)
        result.vector_chunks = chunks

        if self.enable_graph:
            # Find framework in graph
            entities = await self.neo4j.find_entities(
                framework_name,
                labels=["Framework"],
                limit=3,
            )

            if entities:
                framework_entity = entities[0]
                result.entities_found = [framework_entity.name]

                # Get concepts for this framework
                concepts = await self.neo4j.get_concept_for_framework(framework_name)

                # Get framework chains if requested
                chains = []
                if include_chain:
                    chains = await self.neo4j.find_framework_chain(framework_name)

                # Build graph context
                result.graph_context = await self.neo4j.get_related_entities(
                    framework_entity.id,
                    depth=1,
                )

                # Add chain info to frameworks found
                for chain in chains:
                    for node in chain:
                        if node.name not in result.frameworks_found:
                            result.frameworks_found.append(node.name)

        result.merged_context = self._merge_context(result)
        return result

    async def get_problem_type_context(
        self,
        problem_type: str,
    ) -> HybridResult:
        """
        Get context for a problem type (un-defined, ill-defined, well-defined).

        This helps Larry recommend appropriate frameworks.
        """
        result = HybridResult(query=f"Problem type: {problem_type}")

        # Get frameworks for this problem type from graph
        if self.enable_graph:
            frameworks = await self.neo4j.get_problem_type_frameworks(problem_type, limit=10)
            result.entities_found = [f.name for f in frameworks]
            result.frameworks_found = [f.name for f in frameworks if "Framework" in f.labels]

            # Build context from frameworks
            entities = []
            relationships = []
            for fw in frameworks[:5]:
                ctx = await self.neo4j.get_related_entities(fw.id, depth=1, limit=5)
                entities.extend(ctx.entities)
                relationships.extend(ctx.relationships)

            result.graph_context = GraphContext(
                entities=frameworks + entities,
                relationships=relationships,
            )

        # Get relevant content from vector search
        if self.enable_vector:
            query = f"{problem_type} problems frameworks methodology"
            result.vector_chunks = await self.pinecone.search_all_namespaces(query, top_k=5)

        result.merged_context = self._merge_context(result)
        return result

    async def quick_context(self, query: str, top_k: int = 3) -> str:
        """
        Quick context retrieval for simple queries.

        Returns just the merged context string, optimized for speed.
        """
        result = await self.retrieve(
            query,
            top_k=top_k,
            include_graph_expansion=True,
            graph_depth=1,
        )
        return result.merged_context

    def detect_problem_type(self, query: str) -> Optional[str]:
        """
        Detect problem type from query keywords.

        Returns: 'un-defined', 'ill-defined', 'well-defined', or None
        """
        query_lower = query.lower()

        scores = {}
        for problem_type, keywords in self.PROBLEM_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[problem_type] = score

        if scores:
            return max(scores, key=scores.get)
        return None


# Convenience functions for quick usage
async def quick_retrieve(query: str, top_k: int = 5) -> HybridResult:
    """Quick hybrid retrieval helper"""
    retriever = HybridGraphRAGRetriever()
    try:
        return await retriever.retrieve(query, top_k=top_k)
    finally:
        await retriever.close()


async def get_context(query: str, top_k: int = 3) -> str:
    """Get merged context string for a query"""
    retriever = HybridGraphRAGRetriever()
    try:
        return await retriever.quick_context(query, top_k=top_k)
    finally:
        await retriever.close()
