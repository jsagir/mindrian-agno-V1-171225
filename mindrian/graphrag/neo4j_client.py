"""
Neo4j Client for GraphRAG - Async graph operations for hybrid retrieval

Provides:
- Entity extraction from queries
- Relationship discovery
- Multi-hop graph traversal
- Framework chain finding
- Concept hierarchy navigation
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from neo4j import AsyncGraphDatabase


@dataclass
class GraphNode:
    """A node from the knowledge graph"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]

    @property
    def primary_label(self) -> str:
        return self.labels[0] if self.labels else "Unknown"

    @property
    def name(self) -> str:
        return self.properties.get("name", self.properties.get("title", "Unknown"))

    @property
    def description(self) -> str:
        return self.properties.get("description", "")[:500]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "labels": self.labels,
            "name": self.name,
            "description": self.description,
            "properties": self.properties,
        }


@dataclass
class GraphRelationship:
    """A relationship between nodes"""
    type: str
    source_id: str
    target_id: str
    source_name: str = ""
    target_name: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        return f"{self.source_name} --[{self.type}]--> {self.target_name}"


@dataclass
class GraphContext:
    """Graph context retrieved for a query"""
    entities: List[GraphNode] = field(default_factory=list)
    relationships: List[GraphRelationship] = field(default_factory=list)
    paths: List[List[GraphNode]] = field(default_factory=list)

    def to_context_string(self) -> str:
        """Format as context for LLM"""
        lines = []

        # Entities grouped by label
        if self.entities:
            lines.append("## Related Knowledge Graph Entities\n")

            by_label = {}
            for entity in self.entities:
                label = entity.primary_label
                if label not in by_label:
                    by_label[label] = []
                by_label[label].append(entity)

            for label, entities in by_label.items():
                lines.append(f"### {label}s")
                for entity in entities[:5]:
                    desc = entity.description[:200] if entity.description else "No description"
                    lines.append(f"- **{entity.name}**: {desc}")
                lines.append("")

        # Key relationships
        if self.relationships:
            lines.append("## Connections & Relationships\n")
            for rel in self.relationships[:15]:
                lines.append(f"- {rel.to_string()}")

        return "\n".join(lines)

    def get_entity_names(self) -> List[str]:
        """Get all entity names"""
        return [e.name for e in self.entities if e.name != "Unknown"]


class Neo4jGraphClient:
    """
    Async Neo4j client for graph-based retrieval.

    Key operations for PWS/Larry:
    1. find_entities - Find matching Framework, Concept, Technique nodes
    2. get_related_entities - Traverse relationships for context
    3. find_framework_chain - Get PRECEDES/COMPLEMENTS chains
    4. get_problem_type_frameworks - Frameworks for un/ill/well-defined
    5. get_concept_hierarchy - Parent/child concepts
    """

    # Priority labels for PWS domain
    PWS_PRIORITY_LABELS = [
        "Framework",
        "Concept",
        "Technique",
        "ProcessStep",
        "Question",
        "BeautifulQuestion",
        "Author",
        "ProblemType",
        "Opportunity",
        "CynefinDomain",
    ]

    # Key relationship types for traversal
    KEY_RELATIONSHIPS = [
        "HAS_CONCEPT",
        "HAS_TECHNIQUE",
        "REQUIRES",
        "PRECEDES",
        "COMPLEMENTS",
        "APPLIES_TO",
        "DESIGNED_FOR",
        "TEACHES",
        "AUTHORED_BY",
        "IS_PART_OF",
        "RELATES_TO",
    ]

    def __init__(
        self,
        uri: str = None,
        user: str = "neo4j",
        password: str = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self._driver = None

    async def connect(self):
        """Initialize async driver"""
        if not self._driver:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )

    async def close(self):
        """Close connection"""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def health_check(self) -> bool:
        """Check if Neo4j is reachable"""
        try:
            await self.connect()
            async with self._driver.session() as session:
                result = await session.run("RETURN 1 as health")
                record = await result.single()
                return record["health"] == 1
        except Exception as e:
            print(f"Neo4j health check failed: {e}")
            return False

    async def find_entities(
        self,
        query: str,
        labels: List[str] = None,
        limit: int = 10,
    ) -> List[GraphNode]:
        """
        Find entities matching query using text search.

        Searches name, title, and description fields.
        Priority given to PWS-relevant node types.
        """
        await self.connect()

        labels = labels or self.PWS_PRIORITY_LABELS

        # Build label filter
        label_conditions = " OR ".join([f"'{l}' IN labels(n)" for l in labels])

        async with self._driver.session() as session:
            # Search across name, title, description
            result = await session.run(f"""
                MATCH (n)
                WHERE ({label_conditions})
                AND (
                    toLower(n.name) CONTAINS toLower($search_term) OR
                    toLower(n.title) CONTAINS toLower($search_term) OR
                    toLower(coalesce(n.description, '')) CONTAINS toLower($search_term)
                )
                RETURN n, labels(n) as labels
                ORDER BY
                    CASE WHEN toLower(n.name) = toLower($search_term) THEN 0
                         WHEN toLower(n.name) STARTS WITH toLower($search_term) THEN 1
                         ELSE 2 END,
                    size(labels(n)) DESC
                LIMIT $limit
            """, search_term=query, limit=limit)

            nodes = []
            async for record in result:
                node = record["n"]
                nodes.append(GraphNode(
                    id=str(node.element_id),
                    labels=record["labels"],
                    properties=dict(node),
                ))
            return nodes

    async def get_related_entities(
        self,
        node_id: str,
        relationship_types: List[str] = None,
        depth: int = 1,
        limit: int = 20,
    ) -> GraphContext:
        """
        Get entities related to a starting node.

        Traverses relationships to find connected context.
        """
        await self.connect()

        rel_types = relationship_types or self.KEY_RELATIONSHIPS
        rel_filter = "|".join(rel_types)

        async with self._driver.session() as session:
            result = await session.run(f"""
                MATCH (n)-[r:{rel_filter}]-(related)
                WHERE elementId(n) = $node_id
                RETURN n, type(r) as rel_type, r, related, labels(related) as labels
                LIMIT $limit
            """, node_id=node_id, limit=limit)

            entities = []
            relationships = []
            seen_ids = set()

            async for record in result:
                source = record["n"]
                related = record["related"]
                rel_type = record["rel_type"]

                # Add entity
                related_id = str(related.element_id)
                if related_id not in seen_ids:
                    seen_ids.add(related_id)
                    entities.append(GraphNode(
                        id=related_id,
                        labels=record["labels"],
                        properties=dict(related),
                    ))

                # Add relationship
                source_name = source.get("name", source.get("title", ""))
                target_name = related.get("name", related.get("title", ""))

                relationships.append(GraphRelationship(
                    type=rel_type,
                    source_id=str(source.element_id),
                    target_id=related_id,
                    source_name=source_name,
                    target_name=target_name,
                ))

            return GraphContext(
                entities=entities,
                relationships=relationships,
                paths=[],
            )

    async def find_framework_chain(
        self,
        framework_name: str,
        max_depth: int = 3,
    ) -> List[List[GraphNode]]:
        """
        Find recommended framework chains (PRECEDES, COMPLEMENTS).

        Example chains:
        - Cynefin → JTBD → Minto Pyramid
        - Scenario Planning → Trending to Absurd
        """
        await self.connect()

        async with self._driver.session() as session:
            result = await session.run("""
                MATCH path = (f:Framework)-[:PRECEDES|COMPLEMENTS*1..3]->(next:Framework)
                WHERE toLower(f.name) CONTAINS toLower($name)
                RETURN [node IN nodes(path) | node] as chain
                LIMIT 5
            """, name=framework_name)

            chains = []
            async for record in result:
                chain = [
                    GraphNode(
                        id=str(n.element_id),
                        labels=list(n.labels),
                        properties=dict(n),
                    )
                    for n in record["chain"]
                ]
                chains.append(chain)
            return chains

    async def get_problem_type_frameworks(
        self,
        problem_type: str,
        limit: int = 10,
    ) -> List[GraphNode]:
        """
        Get frameworks recommended for a problem type.

        Problem types: un-defined, ill-defined, well-defined, wicked
        """
        await self.connect()

        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (f:Framework)-[:DESIGNED_FOR|APPLIES_TO|ADDRESSES_PROBLEM_TYPE]->(pt:ProblemType)
                WHERE toLower(pt.name) CONTAINS toLower($problem_type)
                   OR toLower(coalesce(pt.description, '')) CONTAINS toLower($problem_type)
                RETURN f, labels(f) as labels
                LIMIT $limit
            """, problem_type=problem_type, limit=limit)

            frameworks = []
            async for record in result:
                node = record["f"]
                frameworks.append(GraphNode(
                    id=str(node.element_id),
                    labels=record["labels"],
                    properties=dict(node),
                ))
            return frameworks

    async def get_concept_for_framework(
        self,
        framework_name: str,
        limit: int = 10,
    ) -> List[GraphNode]:
        """Get concepts associated with a framework"""
        await self.connect()

        async with self._driver.session() as session:
            result = await session.run("""
                MATCH (f:Framework)-[:HAS_CONCEPT|HAS|CONTAINS_CONCEPT]->(c:Concept)
                WHERE toLower(f.name) CONTAINS toLower($name)
                RETURN c, labels(c) as labels
                LIMIT $limit
            """, name=framework_name, limit=limit)

            concepts = []
            async for record in result:
                node = record["c"]
                concepts.append(GraphNode(
                    id=str(node.element_id),
                    labels=record["labels"],
                    properties=dict(node),
                ))
            return concepts

    async def search_by_keywords(
        self,
        keywords: List[str],
        labels: List[str] = None,
        limit: int = 20,
    ) -> List[GraphNode]:
        """
        Search for nodes matching any of the keywords.
        Useful for entity extraction from user queries.
        """
        await self.connect()

        labels = labels or self.PWS_PRIORITY_LABELS
        label_conditions = " OR ".join([f"'{l}' IN labels(n)" for l in labels])

        async with self._driver.session() as session:
            result = await session.run(f"""
                MATCH (n)
                WHERE ({label_conditions})
                AND any(keyword IN $keywords WHERE
                    toLower(n.name) CONTAINS toLower(keyword) OR
                    toLower(coalesce(n.title, '')) CONTAINS toLower(keyword)
                )
                RETURN n, labels(n) as labels
                LIMIT $limit
            """, keywords=keywords, limit=limit)

            nodes = []
            async for record in result:
                node = record["n"]
                nodes.append(GraphNode(
                    id=str(node.element_id),
                    labels=record["labels"],
                    properties=dict(node),
                ))
            return nodes

    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        await self.connect()

        async with self._driver.session() as session:
            # Count nodes by label
            label_counts = {}
            for label in self.PWS_PRIORITY_LABELS:
                result = await session.run(f"""
                    MATCH (n:{label})
                    RETURN count(n) as count
                """)
                record = await result.single()
                label_counts[label] = record["count"]

            # Total relationships
            rel_result = await session.run("""
                MATCH ()-[r]->()
                RETURN count(r) as count
            """)
            rel_record = await rel_result.single()

            return {
                "node_counts": label_counts,
                "total_relationships": rel_record["count"],
                "priority_labels": self.PWS_PRIORITY_LABELS,
            }
