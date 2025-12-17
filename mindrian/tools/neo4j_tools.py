"""
Neo4j Tools - Knowledge graph operations via MCP

Provides tools for:
- Querying the knowledge graph
- Storing new opportunities
- Framework retrieval
- Relationship mapping
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CypherResult:
    """Result of a Cypher query"""
    success: bool
    data: List[Dict[str, Any]]
    error: Optional[str] = None


class Neo4jTools:
    """
    Neo4j MCP tools wrapper.

    These tools interact with the Neo4j knowledge graph containing:
    - Frameworks (Minto, JTBD, PWS, etc.)
    - Opportunities (validated problems)
    - Relationships (PRECEDES, COMPLEMENTS)
    """

    def __init__(self, mcp_client: Optional[Any] = None):
        self._client = mcp_client

    async def query(self, cypher: str, params: Optional[Dict] = None) -> CypherResult:
        """
        Execute a Cypher query.

        Args:
            cypher: Cypher query string
            params: Query parameters

        Returns:
            CypherResult with data or error
        """
        # This would call the MCP server
        # For now, return placeholder
        return CypherResult(
            success=True,
            data=[{"placeholder": "MCP not connected"}],
        )

    async def get_frameworks(self) -> List[Dict[str, Any]]:
        """Get all frameworks from knowledge graph"""
        result = await self.query("""
            MATCH (f:Framework)
            RETURN f.name as name, f.type as type, f.description as description
            ORDER BY f.name
        """)
        return result.data if result.success else []

    async def get_framework_chain(self, framework_name: str) -> List[str]:
        """Get frameworks that chain with the given framework"""
        result = await self.query("""
            MATCH (f:Framework {name: $name})-[:PRECEDES|COMPLEMENTS]->(next:Framework)
            RETURN next.name as name
        """, {"name": framework_name})
        return [r["name"] for r in result.data] if result.success else []

    async def store_opportunity(
        self,
        problem: str,
        who: str,
        success_metric: str,
        classification: str,
    ) -> Optional[str]:
        """
        Store a validated opportunity in the knowledge graph.

        Args:
            problem: Problem description
            who: Stakeholders affected
            success_metric: How success is measured
            classification: Problem type (un-defined, ill-defined, well-defined)

        Returns:
            Node ID if successful
        """
        result = await self.query("""
            CREATE (o:Opportunity {
                problem: $problem,
                stakeholder: $who,
                success_metric: $success,
                classification: $classification,
                created: datetime()
            })
            RETURN elementId(o) as id
        """, {
            "problem": problem,
            "who": who,
            "success": success_metric,
            "classification": classification,
        })
        return result.data[0]["id"] if result.success and result.data else None

    async def search_similar_opportunities(
        self,
        keywords: List[str],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for similar opportunities"""
        result = await self.query("""
            MATCH (o:Opportunity)
            WHERE any(k IN $keywords WHERE
                toLower(o.problem) CONTAINS toLower(k) OR
                toLower(o.stakeholder) CONTAINS toLower(k)
            )
            RETURN o.problem as problem, o.stakeholder as stakeholder,
                   o.classification as classification
            LIMIT $limit
        """, {"keywords": keywords, "limit": limit})
        return result.data if result.success else []
