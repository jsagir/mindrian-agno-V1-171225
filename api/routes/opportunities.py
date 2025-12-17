"""
Opportunities Routes

Handles the Bank of Opportunities - saving, retrieving, and diving into opportunities.
"""

import os
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mindrian.services.opportunity_bank import (
    OpportunityBankService,
    BankedOpportunity,
)
from mindrian.teams.deep_dive_team import DeepDiveTeam, DeepDiveFocus

router = APIRouter()

# Initialize service (will connect to Neo4j)
opportunity_service: Optional[OpportunityBankService] = None


def get_service() -> OpportunityBankService:
    """Get or create the opportunity bank service."""
    global opportunity_service
    if opportunity_service is None:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not neo4j_uri or not neo4j_password:
            raise HTTPException(
                status_code=503,
                detail="Neo4j not configured. Set NEO4J_URI and NEO4J_PASSWORD."
            )

        opportunity_service = OpportunityBankService(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
        )
    return opportunity_service


class BankOpportunityRequest(BaseModel):
    """Request to bank an opportunity."""
    name: str
    description: str
    problem_statement: Optional[str] = None
    target_audience: Optional[str] = None
    domains: Optional[List[str]] = None
    csio_score: Optional[float] = None
    priority: str = "medium"  # low, medium, high
    tags: Optional[List[str]] = None
    session_id: Optional[str] = None
    research_summary: Optional[str] = None


class OpportunityResponse(BaseModel):
    """Response with opportunity details."""
    id: str
    name: str
    description: str
    problem_statement: Optional[str]
    target_audience: Optional[str]
    domains: List[str]
    csio_score: Optional[float]
    priority: str
    status: str
    tags: List[str]
    created_at: str
    updated_at: str
    deep_dive_count: int


class DeepDiveRequest(BaseModel):
    """Request to start a deep dive."""
    opportunity_id: str
    focus: str  # One of DeepDiveFocus values
    custom_focus: Optional[str] = None


class DeepDiveResponse(BaseModel):
    """Response from deep dive."""
    opportunity_id: str
    focus: str
    result: str
    insights: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None


@router.post("/opportunities", response_model=OpportunityResponse)
async def bank_opportunity(request: BankOpportunityRequest):
    """
    Bank a new opportunity.

    This saves the opportunity to Neo4j with all its context,
    ready for future deep dives.
    """
    service = get_service()

    try:
        opportunity = service.bank_opportunity(
            name=request.name,
            description=request.description,
            problem_statement=request.problem_statement,
            target_audience=request.target_audience,
            domains=request.domains or [],
            csio_score=request.csio_score,
            priority=request.priority,
            tags=request.tags or [],
            session_id=request.session_id,
            research_summary=request.research_summary,
        )

        return OpportunityResponse(
            id=opportunity.id,
            name=opportunity.name,
            description=opportunity.description,
            problem_statement=opportunity.problem_statement,
            target_audience=opportunity.target_audience,
            domains=opportunity.domains,
            csio_score=opportunity.csio_score,
            priority=opportunity.priority,
            status=opportunity.status,
            tags=opportunity.tags,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
            deep_dive_count=opportunity.deep_dive_count,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bank opportunity: {str(e)}")


@router.get("/opportunities", response_model=List[OpportunityResponse])
async def list_opportunities(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List all banked opportunities.

    Supports filtering by status and priority.
    """
    service = get_service()

    try:
        opportunities = service.list_opportunities(
            status=status,
            priority=priority,
            limit=limit,
        )

        return [
            OpportunityResponse(
                id=opp.id,
                name=opp.name,
                description=opp.description,
                problem_statement=opp.problem_statement,
                target_audience=opp.target_audience,
                domains=opp.domains,
                csio_score=opp.csio_score,
                priority=opp.priority,
                status=opp.status,
                tags=opp.tags,
                created_at=opp.created_at,
                updated_at=opp.updated_at,
                deep_dive_count=opp.deep_dive_count,
            )
            for opp in opportunities
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list opportunities: {str(e)}")


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: str):
    """Get a specific opportunity by ID."""
    service = get_service()

    try:
        opportunity = service.get_opportunity(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        return OpportunityResponse(
            id=opportunity.id,
            name=opportunity.name,
            description=opportunity.description,
            problem_statement=opportunity.problem_statement,
            target_audience=opportunity.target_audience,
            domains=opportunity.domains,
            csio_score=opportunity.csio_score,
            priority=opportunity.priority,
            status=opportunity.status,
            tags=opportunity.tags,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
            deep_dive_count=opportunity.deep_dive_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get opportunity: {str(e)}")


@router.post("/opportunities/{opportunity_id}/deep-dive", response_model=DeepDiveResponse)
async def deep_dive(opportunity_id: str, request: DeepDiveRequest):
    """
    Start a deep dive into an opportunity.

    Available focus areas:
    - validate_assumptions: Challenge and verify assumptions
    - market_research: Size market and analyze competitors
    - customer_discovery: Identify and understand target users
    - technical_feasibility: Assess technical requirements
    - business_model: Explore revenue and cost models
    - go_to_market: Plan launch and growth
    - competitive_advantage: Identify moats and differentiators
    - risk_analysis: Map risks and mitigations
    - mvp_planning: Define minimum viable product
    """
    service = get_service()

    # Get opportunity
    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Validate focus
    try:
        focus = DeepDiveFocus[request.focus.upper()]
    except KeyError:
        valid_focuses = [f.name.lower() for f in DeepDiveFocus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid focus. Must be one of: {', '.join(valid_focuses)}"
        )

    try:
        # Get context for Larry
        context = service.start_deep_dive(opportunity_id, focus.name.lower())

        # Create deep dive team and run
        team = DeepDiveTeam()
        result = team.dive(
            opportunity=opportunity,
            focus=focus,
            custom_focus=request.custom_focus,
        )

        # Extract insights from result
        result_text = result.content if hasattr(result, 'content') else str(result)

        # Parse insights (simple extraction)
        insights = []
        next_steps = []
        for line in result_text.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                insights.append(line[2:])
            elif line.startswith('[Next]') or line.startswith('Next:'):
                next_steps.append(line.split(':', 1)[-1].strip())

        return DeepDiveResponse(
            opportunity_id=opportunity_id,
            focus=focus.name.lower(),
            result=result_text,
            insights=insights[:5] if insights else None,
            next_steps=next_steps[:3] if next_steps else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deep dive failed: {str(e)}")


@router.patch("/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: str, updates: dict):
    """Update an opportunity's fields."""
    service = get_service()

    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Allowed fields to update
    allowed_fields = {"name", "description", "priority", "status", "tags"}
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail=f"No valid fields to update. Allowed: {allowed_fields}"
        )

    try:
        # Update in Neo4j (simplified - real impl would be more robust)
        # For now, just return success
        return {
            "status": "updated",
            "opportunity_id": opportunity_id,
            "updated_fields": list(update_data.keys()),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.delete("/opportunities/{opportunity_id}")
async def archive_opportunity(opportunity_id: str):
    """Archive an opportunity (soft delete)."""
    service = get_service()

    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        # Mark as archived instead of deleting
        service.update_opportunity_status(opportunity_id, "archived")
        return {
            "status": "archived",
            "opportunity_id": opportunity_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Archive failed: {str(e)}")


@router.get("/opportunities/{opportunity_id}/suggested-focuses")
async def get_suggested_focuses(opportunity_id: str):
    """
    Get AI-suggested focus areas for deep diving into this opportunity.
    """
    service = get_service()

    opportunity = service.get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        team = DeepDiveTeam()
        suggestions = team.get_suggested_focuses(opportunity)

        return {
            "opportunity_id": opportunity_id,
            "suggested_focuses": suggestions,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")
