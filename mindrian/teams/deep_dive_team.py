"""
Deep Dive Team

Handles deep dives into banked opportunities with full context restoration.
This is the team that kicks in when a user returns to a banked opportunity.

The Flow:
1. User selects banked opportunity from Bank of Opportunities
2. User chooses a focus area (Market Research, Validate Assumptions, etc.)
3. OpportunityBankService restores full context
4. DeepDiveTeam orchestrates the exploration with Larry + relevant frameworks
5. New insights are recorded back to the opportunity

This team differs from DeepResearchTeam:
- DeepResearchTeam: Initial exploration of a NEW challenge
- DeepDiveTeam: Continued exploration of a BANKED opportunity with context
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb
from agno.tools.tavily import TavilyTools

from ..handoff.context import HandoffContext, HandoffResult, ProblemClarity, PreviousAnalysis
from ..handoff.types import HandoffType
from ..services.opportunity_bank import (
    OpportunityBankService,
    BankedOpportunity,
    OpportunityContext,
    DeepDiveSession,
    OpportunityStatus,
)


class DeepDiveFocus(str, Enum):
    """Pre-defined focus areas for deep dives"""
    VALIDATE_ASSUMPTIONS = "validate_assumptions"
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    BUILD_MVP_PLAN = "build_mvp_plan"
    CUSTOMER_DISCOVERY = "customer_discovery"
    BUSINESS_MODEL = "business_model"
    GO_TO_MARKET = "go_to_market"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    TEAM_REQUIREMENTS = "team_requirements"
    CUSTOM = "custom"


# Focus-specific instructions for Larry
FOCUS_INSTRUCTIONS = {
    DeepDiveFocus.VALIDATE_ASSUMPTIONS: """
## Focus: Validate Assumptions

Help the user validate the key assumptions behind this opportunity:
1. List the critical assumptions that must be true
2. For each assumption, design a quick validation test
3. Prioritize which assumptions are riskiest
4. Suggest who to talk to for validation

Use the Devil's Advocate perspective when appropriate.
""",

    DeepDiveFocus.MARKET_RESEARCH: """
## Focus: Market Research

Help the user understand the market for this opportunity:
1. Define the target market size (TAM, SAM, SOM)
2. Identify market trends and timing
3. Find comparable markets or adjacent opportunities
4. Research buyer behavior and willingness to pay

Use Tavily research to gather real data.
""",

    DeepDiveFocus.COMPETITOR_ANALYSIS: """
## Focus: Competitor Analysis

Help the user understand the competitive landscape:
1. Identify direct competitors
2. Identify indirect competitors and substitutes
3. Analyze competitor strengths and weaknesses
4. Find the differentiation opportunity

Research specific companies and their offerings.
""",

    DeepDiveFocus.BUILD_MVP_PLAN: """
## Focus: Build MVP Plan

Help the user define a minimum viable product:
1. Identify the core value proposition
2. Define the smallest feature set that delivers value
3. Create a build plan with milestones
4. Estimate effort and resources needed

Be practical and scope-conscious.
""",

    DeepDiveFocus.CUSTOMER_DISCOVERY: """
## Focus: Customer Discovery

Help the user design customer discovery:
1. Define the ideal customer profile
2. Create interview questions that validate the problem
3. Design a customer outreach strategy
4. Define success criteria for discovery

Focus on learning, not selling.
""",

    DeepDiveFocus.BUSINESS_MODEL: """
## Focus: Business Model

Help the user develop the business model:
1. Define value proposition clearly
2. Identify revenue streams
3. Map cost structure
4. Analyze unit economics

Use frameworks like Business Model Canvas or Lean Canvas.
""",

    DeepDiveFocus.GO_TO_MARKET: """
## Focus: Go-to-Market Strategy

Help the user plan market entry:
1. Define launch strategy
2. Identify initial target segment
3. Plan acquisition channels
4. Set success metrics

Be specific about first 100 customers.
""",

    DeepDiveFocus.TECHNICAL_FEASIBILITY: """
## Focus: Technical Feasibility

Help the user assess technical viability:
1. Identify core technical challenges
2. Assess required expertise
3. Evaluate build vs. buy decisions
4. Estimate technical complexity and timeline

Be honest about technical risks.
""",

    DeepDiveFocus.TEAM_REQUIREMENTS: """
## Focus: Team Requirements

Help the user plan team needs:
1. Identify critical roles needed
2. Assess founder-market fit
3. Plan hiring timeline
4. Identify advisors or partners needed

Be realistic about capability gaps.
""",
}


@dataclass
class DeepDiveResult:
    """Result from a deep dive session"""
    opportunity_id: str
    focus: DeepDiveFocus
    session_id: str

    # Conversation output
    conversation_output: str = ""

    # Insights discovered
    new_insights: List[str] = field(default_factory=list)
    validated_assumptions: List[str] = field(default_factory=list)
    new_questions: List[str] = field(default_factory=list)

    # Research (if applicable)
    research_output: str = ""

    # Recommendations
    next_steps: List[str] = field(default_factory=list)
    recommended_focus: Optional[DeepDiveFocus] = None

    # Metadata
    duration_seconds: float = 0.0
    success: bool = True
    error: Optional[str] = None


class DeepDiveTeam:
    """
    Deep Dive Team - Continued exploration of banked opportunities.

    This team:
    1. Restores full context from a banked opportunity
    2. Configures Larry with focus-specific instructions
    3. Optionally brings in research (Tavily) or other frameworks
    4. Records insights back to the opportunity

    Usage:
        team = DeepDiveTeam()

        # Start a deep dive
        result = await team.dive(
            opportunity_id="opp_abc123",
            focus=DeepDiveFocus.MARKET_RESEARCH,
            user_id="user_001",
        )

        # Continue conversation in the deep dive
        response = await team.continue_dive(
            session_id=result.session_id,
            user_message="What about the European market?",
        )
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        opportunity_bank: Optional[OpportunityBankService] = None,
    ):
        self._model = model
        self._db = SqliteDb(db_file="tmp/mindrian.db")
        self._opportunity_bank = opportunity_bank or OpportunityBankService()

        # Create agents
        self._create_agents()

        # Track active sessions
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    def _create_agents(self):
        """Create deep dive agents"""

        # Larry configured for deep dives (context-aware)
        self._larry = Agent(
            name="Larry",
            id="larry-deep-dive",
            model=Claude(id=self._model),
            description="Explores opportunities with full context awareness",
            instructions=["""
# Larry: Deep Dive Explorer

You are continuing an exploration of a previously banked opportunity.
You have FULL CONTEXT from the original exploration - use it!

## Your Approach

1. **Acknowledge Context**: You remember everything from before
2. **Build on Previous Work**: Don't start from scratch
3. **Focus on the Focus**: Stay on the user's chosen focus area
4. **Be Practical**: This is about making progress, not theorizing
5. **Challenge Constructively**: Push back on weak assumptions

## Rules
- Short responses (under 150 words unless detailed analysis needed)
- Reference previous analyses when relevant
- Ask one clarifying question at a time
- Always end with a clear next step or question

## On Returning
When the user returns to a banked opportunity, start with:
"Welcome back! I remember we identified [opportunity] as promising because [reason].
Last time we [summary]. You want to explore [focus area] - let's dig in.
[Relevant question or prompt based on focus]"
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Tavily researcher for market research and competitor analysis
        self._researcher = Agent(
            name="Deep Dive Researcher",
            id="deep-dive-researcher",
            model=Claude(id=self._model),
            description="Conducts targeted research for deep dives",
            instructions=["""
# Deep Dive Researcher

You conduct focused research to support deep dive exploration.

## Your Role
- Search for specific market data
- Find competitor information
- Gather customer insights
- Validate or challenge assumptions with real data

## Output Format
Always structure findings as:
1. **Key Finding** - The main insight
2. **Source** - Where this came from
3. **Confidence** - How reliable is this?
4. **Implication** - What this means for the opportunity

Keep it actionable. The user needs to make decisions.
"""],
            tools=[TavilyTools()],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

        # Devil's Advocate for assumption validation
        self._devil = Agent(
            name="Devil's Advocate",
            id="devils-advocate-dive",
            model=Claude(id=self._model),
            description="Challenges assumptions during deep dives",
            instructions=["""
# Devil's Advocate - Deep Dive Mode

Challenge assumptions behind this opportunity.

## Your Attacks
1. **Market Attack**: Is the market real? Big enough? Growing?
2. **Customer Attack**: Will they actually pay? How much?
3. **Competition Attack**: Why won't incumbents crush this?
4. **Execution Attack**: Can this team actually build this?
5. **Timing Attack**: Why now? Why not 5 years ago?

## Rules
- Be tough but fair
- Attack the idea, not the person
- Offer constructive alternatives
- End with "The opportunity is real IF..."

Don't be a nihilist. Find the path through.
"""],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    async def dive(
        self,
        opportunity_id: str,
        focus: DeepDiveFocus,
        user_id: str,
        custom_focus: str = "",
        additional_context: str = "",
    ) -> DeepDiveResult:
        """
        Start a deep dive into a banked opportunity.

        Args:
            opportunity_id: The banked opportunity to explore
            focus: What aspect to focus on
            user_id: The user initiating the dive
            custom_focus: Custom focus description if focus is CUSTOM
            additional_context: Any additional context from user

        Returns:
            DeepDiveResult with initial exploration output
        """
        import time
        start_time = time.time()

        try:
            # Get the opportunity with full context
            opportunity = await self._opportunity_bank.get_opportunity(opportunity_id)
            if not opportunity:
                return DeepDiveResult(
                    opportunity_id=opportunity_id,
                    focus=focus,
                    session_id="",
                    success=False,
                    error=f"Opportunity {opportunity_id} not found",
                )

            if not opportunity.context:
                return DeepDiveResult(
                    opportunity_id=opportunity_id,
                    focus=focus,
                    session_id="",
                    success=False,
                    error=f"Opportunity {opportunity_id} has no context",
                )

            # Start deep dive session
            deep_dive, handoff_context = await self._opportunity_bank.start_deep_dive(
                opportunity_id=opportunity_id,
                focus=custom_focus if focus == DeepDiveFocus.CUSTOM else focus.value,
                additional_context=additional_context,
            )

            # Build Larry's prompt with restored context
            focus_instructions = FOCUS_INSTRUCTIONS.get(focus, "")
            if focus == DeepDiveFocus.CUSTOM:
                focus_instructions = f"## Custom Focus: {custom_focus}\n\nHelp the user explore this aspect of the opportunity."

            larry_prompt = f"""
{opportunity.context.to_larry_prompt()}

## Opportunity Being Explored
**{opportunity.name}**
{opportunity.description}

**CSIO Score:** {opportunity.csio_score}
**Cross-Section:** {opportunity.cross_section_type}

**User's Notes:**
{opportunity.user_notes}

{focus_instructions}

{f"**Additional Context from User:** {additional_context}" if additional_context else ""}

---

Welcome the user back to this opportunity and help them explore the {focus.value.replace('_', ' ')} aspect.
Reference specific findings from the previous analyses.
"""

            # Run Larry
            response = await self._larry.arun(larry_prompt)
            conversation_output = response.content if hasattr(response, 'content') else str(response)

            # Store session state for continuation
            self._active_sessions[deep_dive.session_id] = {
                "opportunity": opportunity,
                "focus": focus,
                "deep_dive": deep_dive,
                "handoff_context": handoff_context,
                "messages": [
                    {"role": "assistant", "content": conversation_output}
                ],
            }

            return DeepDiveResult(
                opportunity_id=opportunity_id,
                focus=focus,
                session_id=deep_dive.session_id,
                conversation_output=conversation_output,
                duration_seconds=time.time() - start_time,
                success=True,
            )

        except Exception as e:
            return DeepDiveResult(
                opportunity_id=opportunity_id,
                focus=focus,
                session_id="",
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def continue_dive(
        self,
        session_id: str,
        user_message: str,
        request_research: bool = False,
        request_devil: bool = False,
    ) -> Dict[str, Any]:
        """
        Continue a deep dive conversation.

        Args:
            session_id: The active session to continue
            user_message: User's message
            request_research: Whether to invoke Tavily research
            request_devil: Whether to invoke Devil's Advocate

        Returns:
            Dict with Larry's response and optional research/devil output
        """
        if session_id not in self._active_sessions:
            return {"error": f"Session {session_id} not found or expired"}

        session = self._active_sessions[session_id]
        opportunity = session["opportunity"]
        focus = session["focus"]

        # Add user message to history
        session["messages"].append({"role": "user", "content": user_message})

        results = {"larry": "", "research": "", "devil": ""}

        # Build context-aware prompt
        history_context = "\n".join([
            f"{'User' if m['role'] == 'user' else 'Larry'}: {m['content']}"
            for m in session["messages"][-6:]  # Last 6 messages for context
        ])

        larry_prompt = f"""
## Continuing Deep Dive: {opportunity.name}
**Focus:** {focus.value.replace('_', ' ')}

## Recent Conversation
{history_context}

## User's Latest Message
{user_message}

Respond helpfully, staying focused on {focus.value.replace('_', ' ')}.
Reference previous context when relevant.
"""

        # Run Larry
        response = await self._larry.arun(larry_prompt)
        results["larry"] = response.content if hasattr(response, 'content') else str(response)
        session["messages"].append({"role": "assistant", "content": results["larry"]})

        # Optionally run research
        if request_research and focus in [DeepDiveFocus.MARKET_RESEARCH, DeepDiveFocus.COMPETITOR_ANALYSIS]:
            research_prompt = f"""
## Research Request for: {opportunity.name}

**Context:**
{opportunity.context.problem_statement if opportunity.context else opportunity.description}

**User Question:**
{user_message}

**Focus Area:** {focus.value.replace('_', ' ')}

Search for relevant data to answer the user's question.
Be specific and cite sources.
"""
            research_response = await self._researcher.arun(research_prompt)
            results["research"] = research_response.content if hasattr(research_response, 'content') else str(research_response)

        # Optionally run Devil's Advocate
        if request_devil and focus == DeepDiveFocus.VALIDATE_ASSUMPTIONS:
            devil_prompt = f"""
## Devil's Advocate Review: {opportunity.name}

**The Opportunity:**
{opportunity.description}

**User's Current Question/Statement:**
{user_message}

**Previous Analyses:**
{opportunity.context.conversation_summary if opportunity.context else "No previous context"}

Challenge the assumptions in the user's statement.
What could go wrong? What are they missing?
"""
            devil_response = await self._devil.arun(devil_prompt)
            results["devil"] = devil_response.content if hasattr(devil_response, 'content') else str(devil_response)

        return results

    async def complete_dive(
        self,
        session_id: str,
        insights: List[str],
        outcome: str,
        next_focus: Optional[DeepDiveFocus] = None,
    ) -> bool:
        """
        Complete a deep dive session and record results.

        Args:
            session_id: The session to complete
            insights: Key insights discovered
            outcome: Summary of the deep dive outcome
            next_focus: Recommended next focus area

        Returns:
            True if successfully completed
        """
        if session_id not in self._active_sessions:
            return False

        session = self._active_sessions[session_id]
        deep_dive = session["deep_dive"]

        # Complete in opportunity bank
        await self._opportunity_bank.complete_deep_dive(
            deep_dive_id=deep_dive.id,
            new_insights=insights,
            outcome=outcome,
        )

        # Clean up session
        del self._active_sessions[session_id]

        return True

    async def get_suggested_focuses(
        self,
        opportunity_id: str,
    ) -> List[Dict[str, str]]:
        """
        Get suggested focus areas for a deep dive based on opportunity state.

        Returns list of {focus, reason} suggestions.
        """
        opportunity = await self._opportunity_bank.get_opportunity(opportunity_id)
        if not opportunity:
            return []

        suggestions = []

        # Check what analyses exist
        has_market_research = False
        has_competitor = False
        has_validation = False

        if opportunity.context:
            for analysis in opportunity.context.analyses:
                if "market" in analysis.framework_name.lower():
                    has_market_research = True
                if "competitor" in analysis.framework_name.lower():
                    has_competitor = True
                if "validation" in analysis.framework_name.lower():
                    has_validation = True

        # Suggest based on gaps
        if not has_validation:
            suggestions.append({
                "focus": DeepDiveFocus.VALIDATE_ASSUMPTIONS.value,
                "reason": "Critical assumptions haven't been validated yet"
            })

        if not has_market_research:
            suggestions.append({
                "focus": DeepDiveFocus.MARKET_RESEARCH.value,
                "reason": "Market size and trends need research"
            })

        if not has_competitor:
            suggestions.append({
                "focus": DeepDiveFocus.COMPETITOR_ANALYSIS.value,
                "reason": "Competitive landscape not yet mapped"
            })

        # Always suggest based on CSIO score
        if opportunity.csio_score >= 7.0:
            suggestions.append({
                "focus": DeepDiveFocus.BUILD_MVP_PLAN.value,
                "reason": f"High CSIO score ({opportunity.csio_score}) - ready to plan MVP"
            })

        # Based on deep dive count
        if opportunity.deep_dive_count == 0:
            suggestions.insert(0, {
                "focus": DeepDiveFocus.VALIDATE_ASSUMPTIONS.value,
                "reason": "First deep dive - start by validating core assumptions"
            })
        elif opportunity.deep_dive_count >= 3:
            suggestions.append({
                "focus": DeepDiveFocus.GO_TO_MARKET.value,
                "reason": "Multiple deep dives done - time to plan go-to-market"
            })

        return suggestions[:4]  # Return top 4 suggestions
