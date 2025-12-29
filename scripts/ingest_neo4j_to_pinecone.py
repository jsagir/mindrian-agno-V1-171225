#!/usr/bin/env python3
"""
Neo4j to Pinecone GraphRAG Ingestion Script

This script exports knowledge from Neo4j and ingests it into the
Pinecone 'mindrian-graphrag' index with graph linking metadata.

Each record in Pinecone contains:
- content: The text to embed (title + description)
- title: Node name
- category: Node type (Framework, Concept, etc.)
- neo4j_node_id: Neo4j element ID for graph linking
- neo4j_label: Primary node label
- related_entities: Names of connected entities
- source: "neo4j"

Usage:
    python scripts/ingest_neo4j_to_pinecone.py

    # With options
    python scripts/ingest_neo4j_to_pinecone.py --labels Framework,Concept --batch-size 50
"""

import os
import sys
import asyncio
import argparse
from typing import Dict, List, Any
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import AsyncGraphDatabase
import httpx


@dataclass
class GraphRecord:
    """A record to be ingested into Pinecone"""
    id: str
    content: str
    title: str
    category: str
    neo4j_node_id: str
    neo4j_label: str
    related_entities: List[str]
    description: str = ""
    source: str = "neo4j"


class Neo4jToPineconeIngester:
    """
    Ingests Neo4j knowledge graph data into Pinecone for GraphRAG.
    """

    # Node labels to export (priority order)
    EXPORT_LABELS = [
        "Framework",
        "Concept",
        "Technique",
        "ProcessStep",
        "Question",
        "BeautifulQuestion",
        "Author",
        "ProblemType",
        "CynefinDomain",
        "Opportunity",
        "Book",
        "CourseModule",
        "Week",
    ]

    # Relationship types for related entities
    RELATIONSHIP_TYPES = [
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

    # Pinecone configuration
    PINECONE_INDEX_HOST = "mindrian-graphrag-bc1849d.svc.aped-4627-b74a.pinecone.io"
    NAMESPACE = "graphrag"

    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = "neo4j",
        neo4j_password: str = None,
        pinecone_api_key: str = None,
    ):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")

        self._neo4j_driver = None
        self._http_client = None

    async def connect(self):
        """Initialize connections"""
        # Validate required env vars
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        self._neo4j_driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        self._http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Api-Key": self.pinecone_api_key,
                "Content-Type": "application/json",
            }
        )

        # Test connections
        async with self._neo4j_driver.session() as session:
            result = await session.run("RETURN 1 as test")
            await result.single()
        print("Connected to Neo4j")

    async def close(self):
        """Close connections"""
        if self._neo4j_driver:
            await self._neo4j_driver.close()
        if self._http_client:
            await self._http_client.aclose()

    async def get_node_counts(self) -> Dict[str, int]:
        """Get counts of each node type"""
        counts = {}
        async with self._neo4j_driver.session() as session:
            for label in self.EXPORT_LABELS:
                result = await session.run(f"""
                    MATCH (n:{label})
                    RETURN count(n) as count
                """)
                record = await result.single()
                counts[label] = record["count"]
        return counts

    async def export_nodes(
        self,
        labels: List[str] = None,
        limit_per_label: int = None,
    ) -> List[GraphRecord]:
        """
        Export nodes from Neo4j as GraphRecords.

        Args:
            labels: Which node labels to export (default: all)
            limit_per_label: Max nodes per label (for testing)

        Returns:
            List of GraphRecord objects
        """
        labels = labels or self.EXPORT_LABELS
        records = []

        async with self._neo4j_driver.session() as session:
            for label in labels:
                limit_clause = f"LIMIT {limit_per_label}" if limit_per_label else ""

                # Get nodes with their related entities
                result = await session.run(f"""
                    MATCH (n:{label})
                    OPTIONAL MATCH (n)-[r]->(related)
                    WHERE type(r) IN $rel_types
                    WITH n, collect(DISTINCT coalesce(related.name, related.title)) as related_names
                    RETURN
                        elementId(n) as node_id,
                        n.name as name,
                        n.title as title,
                        coalesce(n.description, '') as description,
                        labels(n) as labels,
                        related_names
                    {limit_clause}
                """, rel_types=self.RELATIONSHIP_TYPES)

                async for record in result:
                    node_id = record["node_id"]
                    name = record["name"] or record["title"] or "Unknown"
                    description = record["description"] or ""
                    related = [r for r in record["related_names"] if r]

                    # Build content for embedding
                    content_parts = [name]
                    if description:
                        content_parts.append(description)

                    graph_record = GraphRecord(
                        id=f"{label.lower()}_{self._sanitize_id(name)}",
                        content=" | ".join(content_parts),
                        title=name,
                        category=label,
                        neo4j_node_id=node_id,
                        neo4j_label=label,
                        related_entities=related[:10],  # Limit to 10
                        description=description,
                    )
                    records.append(graph_record)

                print(f"  Exported {len([r for r in records if r.category == label])} {label} nodes")

        return records

    def _sanitize_id(self, text: str) -> str:
        """Sanitize text for use as ID"""
        import re
        # Remove special characters, convert to lowercase, replace spaces with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        return sanitized[:50]  # Limit length

    async def upsert_to_pinecone(
        self,
        records: List[GraphRecord],
        batch_size: int = 100,
    ) -> int:
        """
        Upsert records to Pinecone.

        Args:
            records: List of GraphRecord objects
            batch_size: Number of records per batch

        Returns:
            Number of records upserted
        """
        total_upserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            # Convert to Pinecone format
            pinecone_records = []
            for record in batch:
                pinecone_record = {
                    "_id": record.id,
                    "content": record.content,  # This gets embedded
                    "title": record.title,
                    "category": record.category,
                    "neo4j_node_id": record.neo4j_node_id,
                    "neo4j_label": record.neo4j_label,
                    "related_entities": record.related_entities,
                    "source": record.source,
                }
                if record.description:
                    pinecone_record["description"] = record.description[:1000]

                pinecone_records.append(pinecone_record)

            # Upsert batch
            url = f"https://{self.PINECONE_INDEX_HOST}/records/namespaces/{self.NAMESPACE}/upsert"
            try:
                response = await self._http_client.post(
                    url,
                    json={"records": pinecone_records}
                )
                response.raise_for_status()
                total_upserted += len(batch)
                print(f"  Upserted batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as e:
                print(f"  Error upserting batch: {e}")

        return total_upserted

    async def run(
        self,
        labels: List[str] = None,
        batch_size: int = 100,
        limit_per_label: int = None,
        dry_run: bool = False,
    ):
        """
        Run the full ingestion pipeline.

        Args:
            labels: Which labels to export (default: all)
            batch_size: Pinecone batch size
            limit_per_label: Limit nodes per label (for testing)
            dry_run: If True, export but don't upsert
        """
        print("=" * 60)
        print("Neo4j to Pinecone GraphRAG Ingestion")
        print("=" * 60)

        await self.connect()

        try:
            # Show node counts
            print("\n Node counts in Neo4j:")
            counts = await self.get_node_counts()
            total_nodes = 0
            for label, count in counts.items():
                if count > 0:
                    print(f"  {label}: {count}")
                    total_nodes += count
            print(f"  Total: {total_nodes}")

            # Export nodes
            print("\n Exporting nodes...")
            records = await self.export_nodes(labels, limit_per_label)
            print(f"\n Total records to ingest: {len(records)}")

            if dry_run:
                print("\n Dry run - skipping Pinecone upsert")
                print("\nSample records:")
                for record in records[:3]:
                    print(f"  - {record.title} ({record.category})")
                    print(f"    Related: {record.related_entities[:3]}")
                return

            # Upsert to Pinecone
            print(f"\n Upserting to Pinecone (namespace: {self.NAMESPACE})...")
            upserted = await self.upsert_to_pinecone(records, batch_size)
            print(f"\n Successfully upserted {upserted} records")

            # Verify
            print("\n Verifying Pinecone index stats...")
            stats_url = f"https://{self.PINECONE_INDEX_HOST}/describe_index_stats"
            response = await self._http_client.post(stats_url, json={})
            stats = response.json()

            namespaces = stats.get("namespaces", {})
            if self.NAMESPACE in namespaces:
                ns_stats = namespaces[self.NAMESPACE]
                print(f"  Namespace '{self.NAMESPACE}': {ns_stats.get('recordCount', 0)} records")
            else:
                print(f"  Namespace '{self.NAMESPACE}': (not yet visible, may take a moment)")

            print("\n Ingestion complete!")

        finally:
            await self.close()


async def main():
    parser = argparse.ArgumentParser(description="Ingest Neo4j data to Pinecone GraphRAG")
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Comma-separated list of node labels to export (default: all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for Pinecone upserts (default: 100)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit nodes per label (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Export but don't upsert to Pinecone"
    )

    args = parser.parse_args()

    labels = args.labels.split(",") if args.labels else None

    ingester = Neo4jToPineconeIngester()
    await ingester.run(
        labels=labels,
        batch_size=args.batch_size,
        limit_per_label=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    asyncio.run(main())
