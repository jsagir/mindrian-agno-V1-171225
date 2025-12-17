"""
Opportunity Bank Service

The Bank of Opportunities is where users save promising opportunities discovered
during conversations. Each banked opportunity preserves its full context:
- The problem it addresses
- The analyses that surfaced it
- The conversation thread that led to discovery
- User notes and tags

Users can later deep-dive into any banked opportunity with full context restored.

This service handles:
1. Banking opportunities (with full context capture)
2. Listing/filtering banked opportunities
3. Restoring context for deep dives
4. Tracking deep dive sessions
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import os

from neo4j import AsyncGraphDatabase

from ..handoff.context import (
    HandoffContext,
    HandoffResult,
    ProblemClarity,
    PreviousAnalysis,
    ConversationSummary,
)


class OpportunityPriority(str, Enum):
    """Priority levels for banked opportunities"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OpportunityStatus(str, Enum):
    """Status of banked opportunity"""
    ACTIVE = "ACTIVE"           # Available for deep dive
    ARCHIVED = "ARCHIVED"       # User archived it
    VALIDATED = "VALIDATED"     # User validated the opportunity
    REJECTED = "REJECTED"       # User decided against it
    IN_PROGRESS = "IN_PROGRESS" # Actively being worked on


@dataclass
class FrameworkAnalysisSummary:
    """Summary of a framework analysis for context preservation"""
    framework_id: str
    framework_name: str
    key_findings: List[str]
    output_summary: str  # Truncated output for quick reference
    full_output: str     # Complete output for deep dives
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OpportunityContext:
    """
    The full context preserved when banking an opportunity.
    This is what allows deep dives to restore the complete picture.
    """
    # Problem context (from Larry)
    problem_statement: str
    problem_what: str
    problem_who: str
    problem_success: str
    problem_clarity_score: float

    # Conversation context
    conversation_summary: str
    key_insights: List[str]
    user_goals: List[str]
    constraints: List[str]

    # Framework analyses
    analyses: List[FrameworkAnalysisSummary] = field(default_factory=list)

    # Origin tracking
    session_id: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)

    def to_larry_prompt(self) -> str:
        """Generate context prompt for Larry when restoring deep dive"""
        analyses_section = ""
        if self.analyses:
            analyses_section = "\n### Previous Analyses\n"
            for analysis in self.analyses:
                analyses_section += f"\n**{analysis.framework_name}:**\n"
                if analysis.key_findings:
                    analyses_section += "Key findings:\n"
                    analyses_section += "\n".join(f"- {f}" for f in analysis.key_findings)
                analyses_section += "\n"

        insights_section = ""
        if self.key_insights:
            insights_section = "\n### Key Insights from Original Exploration\n"
            insights_section += "\n".join(f"- {i}" for i in self.key_insights)

        return f"""## Restored Context: Deep Dive Session

### Original Problem
- **What:** {self.problem_what}
- **Who:** {self.problem_who}
- **Success:** {self.problem_success}
- **Clarity:** {self.problem_clarity_score:.0%}

### Problem Statement
{self.problem_statement}
{analyses_section}
{insights_section}

### Conversation Summary
{self.conversation_summary}
"""

    def to_problem_clarity(self) -> ProblemClarity:
        """Convert to ProblemClarity for handoff context"""
        return ProblemClarity(
            what=self.problem_what,
            who=self.problem_who,
            success=self.problem_success,
            what_clarity=self.problem_clarity_score,
            who_clarity=self.problem_clarity_score * 0.9,  # Slightly lower for who/success
            success_clarity=self.problem_clarity_score * 0.9,
        )

    def to_previous_analyses(self) -> List[PreviousAnalysis]:
        """Convert framework analyses to PreviousAnalysis for handoff"""
        return [
            PreviousAnalysis(
                framework_id=a.framework_id,
                framework_name=a.framework_name,
                output=a.full_output,
                key_findings=a.key_findings,
                confidence=a.confidence,
                timestamp=a.created_at,
            )
            for a in self.analyses
        ]


@dataclass
class DeepDiveSession:
    """A deep dive session into a banked opportunity"""
    id: str
    opportunity_id: str
    focus: str  # What aspect user wants to explore
    started_at: datetime
    ended_at: Optional[datetime] = None
    new_insights: List[str] = field(default_factory=list)
    outcome: str = ""
    session_id: Optional[str] = None  # New conversation session created


@dataclass
class BankedOpportunity:
    """A single banked opportunity with full context"""
    id: str
    name: str
    description: str

    # Scoring
    csio_score: float = 0.0
    cross_section_type: str = ""  # Domain×Domain, Industry×Tech, etc.
    cross_section_elements: List[str] = field(default_factory=list)  # [Element A, Element B]

    # User organization
    priority: OpportunityPriority = OpportunityPriority.MEDIUM
    status: OpportunityStatus = OpportunityStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    user_notes: str = ""

    # Full context
    context: Optional[OpportunityContext] = None

    # Timestamps
    banked_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)

    # Usage tracking
    deep_dive_count: int = 0
    deep_dives: List[DeepDiveSession] = field(default_factory=list)

    # Owner
    user_id: str = ""


class OpportunityBankService:
    """
    Service for managing the Bank of Opportunities.

    Usage:
        service = OpportunityBankService()

        # Bank an opportunity from a deep research result
        opportunity = await service.bank_from_research(
            research_result=result,
            opportunity_name="AI Async Standups",
            user_notes="Validate with engineering managers",
            tags=["remote-work", "AI"],
        )

        # List user's banked opportunities
        opportunities = await service.list_opportunities(
            user_id="user_001",
            priority=["HIGH", "MEDIUM"],
            tags=["AI"],
        )

        # Start a deep dive
        context = await service.start_deep_dive(
            opportunity_id="opp_123",
            focus="Market Research",
        )
    """

    def __init__(self, neo4j_uri: Optional[str] = None, neo4j_auth: Optional[tuple] = None):
        """Initialize with Neo4j connection"""
        self._uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._auth = neo4j_auth or (
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password")
        )
        self._driver = None

    async def _get_driver(self):
        """Lazy initialization of Neo4j driver"""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(self._uri, auth=self._auth)
        return self._driver

    async def close(self):
        """Close the Neo4j driver"""
        if self._driver:
            await self._driver.close()
            self._driver = None

    # =========================================================================
    # BANKING OPPORTUNITIES
    # =========================================================================

    async def bank_opportunity(
        self,
        name: str,
        description: str,
        context: OpportunityContext,
        user_id: str,
        csio_score: float = 0.0,
        cross_section_type: str = "",
        cross_section_elements: Optional[List[str]] = None,
        priority: OpportunityPriority = OpportunityPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        user_notes: str = "",
    ) -> BankedOpportunity:
        """
        Bank a new opportunity with full context preservation.

        This is the core banking operation - saves to Neo4j with all relationships.
        """
        opportunity_id = f"opp_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        opportunity = BankedOpportunity(
            id=opportunity_id,
            name=name,
            description=description,
            csio_score=csio_score,
            cross_section_type=cross_section_type,
            cross_section_elements=cross_section_elements or [],
            priority=priority,
            status=OpportunityStatus.ACTIVE,
            tags=tags or [],
            user_notes=user_notes,
            context=context,
            banked_at=now,
            last_accessed=now,
            user_id=user_id,
        )

        # Persist to Neo4j
        await self._save_to_neo4j(opportunity)

        return opportunity

    async def bank_from_research_result(
        self,
        research_result: Any,  # DeepResearchResult
        opportunity_name: str,
        opportunity_description: str,
        csio_score: float,
        user_id: str,
        cross_section_type: str = "",
        cross_section_elements: Optional[List[str]] = None,
        priority: OpportunityPriority = OpportunityPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        user_notes: str = "",
        session_id: Optional[str] = None,
    ) -> BankedOpportunity:
        """
        Bank an opportunity directly from a DeepResearchResult.

        This extracts all the context automatically from the research result.
        """
        # Build context from research result
        analyses = []

        if research_result.minto_output:
            analyses.append(FrameworkAnalysisSummary(
                framework_id="minto-pyramid",
                framework_name="Minto Pyramid",
                key_findings=["SCQA structure applied"],
                output_summary=research_result.minto_output[:500],
                full_output=research_result.minto_output,
            ))

        if research_result.beautiful_question_output:
            analyses.append(FrameworkAnalysisSummary(
                framework_id="beautiful-question",
                framework_name="Beautiful Question",
                key_findings=["Why/What If/How questions generated"],
                output_summary=research_result.beautiful_question_output[:500],
                full_output=research_result.beautiful_question_output,
            ))

        if research_result.domain_analysis_output:
            analyses.append(FrameworkAnalysisSummary(
                framework_id="domain-analysis",
                framework_name="Domain Analysis",
                key_findings=["Domains and intersections mapped"],
                output_summary=research_result.domain_analysis_output[:500],
                full_output=research_result.domain_analysis_output,
            ))

        if research_result.csio_output:
            analyses.append(FrameworkAnalysisSummary(
                framework_id="csio",
                framework_name="CSIO Analysis",
                key_findings=["Cross-sectional opportunities identified"],
                output_summary=research_result.csio_output[:500],
                full_output=research_result.csio_output,
            ))

        if research_result.research_output:
            analyses.append(FrameworkAnalysisSummary(
                framework_id="tavily-research",
                framework_name="Web Research",
                key_findings=["Market data gathered"],
                output_summary=research_result.research_output[:500],
                full_output=research_result.research_output,
            ))

        # Build the context
        context = OpportunityContext(
            problem_statement=research_result.challenge,
            problem_what=research_result.problem_clarity.what or "",
            problem_who=research_result.problem_clarity.who or "",
            problem_success=research_result.problem_clarity.success or "",
            problem_clarity_score=research_result.problem_clarity.overall_clarity,
            conversation_summary=research_result.larry_output,
            key_insights=[],  # Could be extracted from consolidated report
            user_goals=[],
            constraints=[],
            analyses=analyses,
            session_id=session_id,
        )

        return await self.bank_opportunity(
            name=opportunity_name,
            description=opportunity_description,
            context=context,
            user_id=user_id,
            csio_score=csio_score,
            cross_section_type=cross_section_type,
            cross_section_elements=cross_section_elements,
            priority=priority,
            tags=tags,
            user_notes=user_notes,
        )

    # =========================================================================
    # LISTING & FILTERING
    # =========================================================================

    async def list_opportunities(
        self,
        user_id: str,
        status: Optional[List[OpportunityStatus]] = None,
        priority: Optional[List[OpportunityPriority]] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "banked_at",  # banked_at, csio_score, priority, last_accessed
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> List[BankedOpportunity]:
        """List banked opportunities with filtering and sorting"""

        driver = await self._get_driver()

        # Build query
        where_clauses = ["bo.user_id = $user_id"]
        params = {"user_id": user_id, "limit": limit, "offset": offset}

        if status:
            where_clauses.append("bo.status IN $status")
            params["status"] = [s.value for s in status]
        else:
            where_clauses.append("bo.status = 'ACTIVE'")

        if priority:
            where_clauses.append("bo.priority IN $priority")
            params["priority"] = [p.value for p in priority]

        where_clause = " AND ".join(where_clauses)

        # Tag filtering requires separate match
        tag_match = ""
        if tags:
            tag_match = "MATCH (bo)-[:TAGGED_WITH]->(t:Tag) WHERE t.name IN $tags"
            params["tags"] = tags

        # Sort mapping
        sort_field = {
            "banked_at": "bo.banked_at",
            "csio_score": "bo.csio_score",
            "priority": "CASE bo.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END",
            "last_accessed": "bo.last_accessed",
        }.get(sort_by, "bo.banked_at")

        order_clause = "DESC" if order == "desc" else "ASC"

        query = f"""
        MATCH (bo:BankedOpportunity)
        WHERE {where_clause}
        {tag_match}
        OPTIONAL MATCH (bo)-[:TAGGED_WITH]->(tag:Tag)
        OPTIONAL MATCH (bo)-[:HAS_CONTEXT]->(ctx:OpportunityContext)
        RETURN bo {{
            .*,
            tags: collect(DISTINCT tag.name),
            problem_statement: ctx.problem_statement
        }} as opportunity
        ORDER BY {sort_field} {order_clause}
        SKIP $offset
        LIMIT $limit
        """

        async with driver.session() as session:
            result = await session.run(query, params)
            records = await result.data()

        # Convert to BankedOpportunity objects
        opportunities = []
        for record in records:
            opp_data = record["opportunity"]
            opportunities.append(BankedOpportunity(
                id=opp_data.get("id", ""),
                name=opp_data.get("name", ""),
                description=opp_data.get("description", ""),
                csio_score=opp_data.get("csio_score", 0.0),
                cross_section_type=opp_data.get("cross_section_type", ""),
                priority=OpportunityPriority(opp_data.get("priority", "MEDIUM")),
                status=OpportunityStatus(opp_data.get("status", "ACTIVE")),
                tags=opp_data.get("tags", []),
                user_notes=opp_data.get("user_notes", ""),
                user_id=opp_data.get("user_id", ""),
                deep_dive_count=opp_data.get("deep_dive_count", 0),
            ))

        return opportunities

    async def get_opportunity(self, opportunity_id: str) -> Optional[BankedOpportunity]:
        """Get a single opportunity with full context"""

        driver = await self._get_driver()

        query = """
        MATCH (bo:BankedOpportunity {id: $id})
        OPTIONAL MATCH (bo)-[:HAS_CONTEXT]->(ctx:OpportunityContext)
        OPTIONAL MATCH (ctx)-[:INCLUDES_ANALYSIS]->(fa:FrameworkAnalysis)
        OPTIONAL MATCH (bo)-[:TAGGED_WITH]->(tag:Tag)
        OPTIONAL MATCH (bo)-[:HAS_DEEP_DIVE]->(dd:DeepDiveSession)
        RETURN bo, ctx,
               collect(DISTINCT fa) as analyses,
               collect(DISTINCT tag.name) as tags,
               collect(DISTINCT dd) as deep_dives
        """

        async with driver.session() as session:
            result = await session.run(query, {"id": opportunity_id})
            record = await result.single()

        if not record:
            return None

        bo_data = dict(record["bo"])
        ctx_data = dict(record["ctx"]) if record["ctx"] else None
        analyses_data = [dict(a) for a in record["analyses"]]
        tags = record["tags"]
        deep_dives_data = [dict(dd) for dd in record["deep_dives"]]

        # Build context
        context = None
        if ctx_data:
            analyses = [
                FrameworkAnalysisSummary(
                    framework_id=a.get("framework_id", ""),
                    framework_name=a.get("framework_name", ""),
                    key_findings=a.get("key_findings", []),
                    output_summary=a.get("output_summary", ""),
                    full_output=a.get("full_output", ""),
                    confidence=a.get("confidence", 0.0),
                )
                for a in analyses_data
            ]

            context = OpportunityContext(
                problem_statement=ctx_data.get("problem_statement", ""),
                problem_what=ctx_data.get("problem_what", ""),
                problem_who=ctx_data.get("problem_who", ""),
                problem_success=ctx_data.get("problem_success", ""),
                problem_clarity_score=ctx_data.get("problem_clarity_score", 0.0),
                conversation_summary=ctx_data.get("conversation_summary", ""),
                key_insights=ctx_data.get("key_insights", []),
                user_goals=ctx_data.get("user_goals", []),
                constraints=ctx_data.get("constraints", []),
                analyses=analyses,
                session_id=ctx_data.get("session_id"),
            )

        # Build deep dives
        deep_dives = [
            DeepDiveSession(
                id=dd.get("id", ""),
                opportunity_id=opportunity_id,
                focus=dd.get("focus", ""),
                started_at=dd.get("started_at", datetime.now()),
                ended_at=dd.get("ended_at"),
                new_insights=dd.get("new_insights", []),
                outcome=dd.get("outcome", ""),
            )
            for dd in deep_dives_data
        ]

        return BankedOpportunity(
            id=bo_data.get("id", ""),
            name=bo_data.get("name", ""),
            description=bo_data.get("description", ""),
            csio_score=bo_data.get("csio_score", 0.0),
            cross_section_type=bo_data.get("cross_section_type", ""),
            cross_section_elements=bo_data.get("cross_section_elements", []),
            priority=OpportunityPriority(bo_data.get("priority", "MEDIUM")),
            status=OpportunityStatus(bo_data.get("status", "ACTIVE")),
            tags=tags,
            user_notes=bo_data.get("user_notes", ""),
            context=context,
            user_id=bo_data.get("user_id", ""),
            deep_dive_count=bo_data.get("deep_dive_count", 0),
            deep_dives=deep_dives,
        )

    # =========================================================================
    # DEEP DIVE
    # =========================================================================

    async def start_deep_dive(
        self,
        opportunity_id: str,
        focus: str,
        additional_context: str = "",
    ) -> tuple[DeepDiveSession, HandoffContext]:
        """
        Start a deep dive session into a banked opportunity.

        Returns:
            - DeepDiveSession: The new session record
            - HandoffContext: Full context for Larry to continue the conversation
        """
        # Get the opportunity with full context
        opportunity = await self.get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        if not opportunity.context:
            raise ValueError(f"Opportunity {opportunity_id} has no context")

        # Create deep dive session
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        deep_dive = DeepDiveSession(
            id=f"dd_{uuid.uuid4().hex[:12]}",
            opportunity_id=opportunity_id,
            focus=focus,
            started_at=datetime.now(),
            session_id=session_id,
        )

        # Save to Neo4j
        await self._save_deep_dive(opportunity_id, deep_dive)

        # Update access tracking
        await self._update_access(opportunity_id)

        # Build handoff context for Larry
        handoff_context = HandoffContext(
            handoff_id=f"deepdive_{deep_dive.id}",
            problem_clarity=opportunity.context.to_problem_clarity(),
            conversation=ConversationSummary(
                key_points=opportunity.context.key_insights,
                user_goals=opportunity.context.user_goals,
                constraints=opportunity.context.constraints,
            ),
            previous_analyses=opportunity.context.to_previous_analyses(),
            task_description=f"""
## Deep Dive Session: {opportunity.name}

The user is returning to explore this banked opportunity.

**Focus Area:** {focus}

**Opportunity Details:**
- Name: {opportunity.name}
- Description: {opportunity.description}
- CSIO Score: {opportunity.csio_score}
- Cross-Section: {opportunity.cross_section_type}

**User's Notes from Banking:**
{opportunity.user_notes}

{f"**Additional Context:** {additional_context}" if additional_context else ""}

**Your Task:**
Welcome the user back, acknowledge the restored context, and help them
explore the "{focus}" aspect of this opportunity. Build on the previous
analyses - don't start from scratch.
""",
            from_agent="opportunity-bank",
            to_agent="larry-explorer",
            return_to="deep-dive-session",
            session_id=session_id,
        )

        return deep_dive, handoff_context

    async def complete_deep_dive(
        self,
        deep_dive_id: str,
        new_insights: List[str],
        outcome: str,
    ):
        """Complete a deep dive session with results"""

        driver = await self._get_driver()

        query = """
        MATCH (dd:DeepDiveSession {id: $id})
        SET dd.ended_at = datetime(),
            dd.new_insights = $insights,
            dd.outcome = $outcome
        RETURN dd
        """

        async with driver.session() as session:
            await session.run(query, {
                "id": deep_dive_id,
                "insights": new_insights,
                "outcome": outcome,
            })

    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================

    async def update_priority(self, opportunity_id: str, priority: OpportunityPriority):
        """Update opportunity priority"""
        driver = await self._get_driver()
        query = "MATCH (bo:BankedOpportunity {id: $id}) SET bo.priority = $priority"
        async with driver.session() as session:
            await session.run(query, {"id": opportunity_id, "priority": priority.value})

    async def update_status(self, opportunity_id: str, status: OpportunityStatus):
        """Update opportunity status"""
        driver = await self._get_driver()
        query = "MATCH (bo:BankedOpportunity {id: $id}) SET bo.status = $status"
        async with driver.session() as session:
            await session.run(query, {"id": opportunity_id, "status": status.value})

    async def update_notes(self, opportunity_id: str, notes: str):
        """Update user notes"""
        driver = await self._get_driver()
        query = "MATCH (bo:BankedOpportunity {id: $id}) SET bo.user_notes = $notes"
        async with driver.session() as session:
            await session.run(query, {"id": opportunity_id, "notes": notes})

    async def add_tags(self, opportunity_id: str, tags: List[str]):
        """Add tags to opportunity"""
        driver = await self._get_driver()
        query = """
        MATCH (bo:BankedOpportunity {id: $id})
        UNWIND $tags AS tag_name
        MERGE (t:Tag {name: tag_name})
        MERGE (bo)-[:TAGGED_WITH]->(t)
        """
        async with driver.session() as session:
            await session.run(query, {"id": opportunity_id, "tags": tags})

    # =========================================================================
    # NEO4J PERSISTENCE
    # =========================================================================

    async def _save_to_neo4j(self, opportunity: BankedOpportunity):
        """Save opportunity with full context to Neo4j"""

        driver = await self._get_driver()

        # Main opportunity node
        opp_query = """
        CREATE (bo:BankedOpportunity {
            id: $id,
            name: $name,
            description: $description,
            csio_score: $csio_score,
            cross_section_type: $cross_section_type,
            cross_section_elements: $cross_section_elements,
            priority: $priority,
            status: $status,
            user_notes: $user_notes,
            user_id: $user_id,
            banked_at: datetime(),
            last_accessed: datetime(),
            deep_dive_count: 0
        })
        RETURN bo
        """

        async with driver.session() as session:
            # Create main node
            await session.run(opp_query, {
                "id": opportunity.id,
                "name": opportunity.name,
                "description": opportunity.description,
                "csio_score": opportunity.csio_score,
                "cross_section_type": opportunity.cross_section_type,
                "cross_section_elements": opportunity.cross_section_elements,
                "priority": opportunity.priority.value,
                "status": opportunity.status.value,
                "user_notes": opportunity.user_notes,
                "user_id": opportunity.user_id,
            })

            # Create context if exists
            if opportunity.context:
                ctx = opportunity.context
                ctx_query = """
                MATCH (bo:BankedOpportunity {id: $opp_id})
                CREATE (ctx:OpportunityContext {
                    id: randomUUID(),
                    problem_statement: $problem_statement,
                    problem_what: $problem_what,
                    problem_who: $problem_who,
                    problem_success: $problem_success,
                    problem_clarity_score: $problem_clarity_score,
                    conversation_summary: $conversation_summary,
                    key_insights: $key_insights,
                    user_goals: $user_goals,
                    constraints: $constraints,
                    session_id: $session_id,
                    created_at: datetime()
                })
                CREATE (bo)-[:HAS_CONTEXT]->(ctx)
                RETURN ctx
                """

                result = await session.run(ctx_query, {
                    "opp_id": opportunity.id,
                    "problem_statement": ctx.problem_statement,
                    "problem_what": ctx.problem_what,
                    "problem_who": ctx.problem_who,
                    "problem_success": ctx.problem_success,
                    "problem_clarity_score": ctx.problem_clarity_score,
                    "conversation_summary": ctx.conversation_summary,
                    "key_insights": ctx.key_insights,
                    "user_goals": ctx.user_goals,
                    "constraints": ctx.constraints,
                    "session_id": ctx.session_id,
                })

                # Create framework analyses
                for analysis in ctx.analyses:
                    fa_query = """
                    MATCH (bo:BankedOpportunity {id: $opp_id})-[:HAS_CONTEXT]->(ctx:OpportunityContext)
                    CREATE (fa:FrameworkAnalysis {
                        id: randomUUID(),
                        framework_id: $framework_id,
                        framework_name: $framework_name,
                        key_findings: $key_findings,
                        output_summary: $output_summary,
                        full_output: $full_output,
                        confidence: $confidence,
                        created_at: datetime()
                    })
                    CREATE (ctx)-[:INCLUDES_ANALYSIS]->(fa)
                    """

                    await session.run(fa_query, {
                        "opp_id": opportunity.id,
                        "framework_id": analysis.framework_id,
                        "framework_name": analysis.framework_name,
                        "key_findings": analysis.key_findings,
                        "output_summary": analysis.output_summary,
                        "full_output": analysis.full_output,
                        "confidence": analysis.confidence,
                    })

            # Add tags
            if opportunity.tags:
                tag_query = """
                MATCH (bo:BankedOpportunity {id: $opp_id})
                UNWIND $tags AS tag_name
                MERGE (t:Tag {name: tag_name})
                CREATE (bo)-[:TAGGED_WITH]->(t)
                """
                await session.run(tag_query, {
                    "opp_id": opportunity.id,
                    "tags": opportunity.tags,
                })

    async def _save_deep_dive(self, opportunity_id: str, deep_dive: DeepDiveSession):
        """Save deep dive session to Neo4j"""

        driver = await self._get_driver()

        query = """
        MATCH (bo:BankedOpportunity {id: $opp_id})
        CREATE (dd:DeepDiveSession {
            id: $id,
            focus: $focus,
            started_at: datetime(),
            session_id: $session_id
        })
        CREATE (bo)-[:HAS_DEEP_DIVE]->(dd)
        SET bo.deep_dive_count = bo.deep_dive_count + 1
        RETURN dd
        """

        async with driver.session() as session:
            await session.run(query, {
                "opp_id": opportunity_id,
                "id": deep_dive.id,
                "focus": deep_dive.focus,
                "session_id": deep_dive.session_id,
            })

    async def _update_access(self, opportunity_id: str):
        """Update last accessed timestamp"""

        driver = await self._get_driver()
        query = "MATCH (bo:BankedOpportunity {id: $id}) SET bo.last_accessed = datetime()"

        async with driver.session() as session:
            await session.run(query, {"id": opportunity_id})
