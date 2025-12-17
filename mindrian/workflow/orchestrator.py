"""
Mindrian Orchestrator - Main workflow coordinator

The orchestrator:
1. Receives user input
2. Routes through Larry for clarification
3. Classifies the problem
4. Delegates to appropriate agents/teams
5. Coordinates framework execution
6. Synthesizes final output
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from agno.agent import Agent
from agno.models.anthropic import Claude

from ..registry.agent_registry import AgentRegistry, agent_registry
from ..registry.skill_loader import SkillLoader
from ..registry.mcp_manager import MCPManager, mcp_manager
from ..agents.conversational.larry import LarryAgent, LarryMode
from ..agents.conversational.devil import DevilsAdvocateAgent
from .router import ProblemRouter, ProblemType, RoutingDecision


class OrchestratorState(str, Enum):
    """States of the orchestrator"""
    IDLE = "idle"
    CLARIFYING = "clarifying"      # Larry asking questions
    CLASSIFYING = "classifying"    # Determining problem type
    PROCESSING = "processing"       # Running frameworks
    VALIDATING = "validating"       # Devil's advocate review
    OUTPUTTING = "outputting"       # Generating final output
    COMPLETE = "complete"


@dataclass
class Session:
    """Conversation session state"""
    session_id: str
    state: OrchestratorState = OrchestratorState.IDLE
    problem_description: Optional[str] = None
    problem_type: Optional[ProblemType] = None
    routing_decision: Optional[RoutingDecision] = None

    # Conversation history
    messages: List[Dict[str, str]] = field(default_factory=list)

    # Agent outputs
    agent_outputs: Dict[str, Any] = field(default_factory=dict)

    # Final deliverables
    deliverables: List[Dict[str, Any]] = field(default_factory=list)


class MindrianOrchestrator:
    """
    Main orchestrator for Mindrian conversations.

    Usage:
        orchestrator = MindrianOrchestrator(skills_path="/path/to/skills")
        await orchestrator.initialize()

        # Start conversation
        response = await orchestrator.process("I want to build an AI chatbot")

        # Continue conversation
        response = await orchestrator.process("For customer support")

        # Get session summary
        summary = orchestrator.get_session_summary()
    """

    def __init__(
        self,
        skills_path: str = "/home/jsagi/Mindrian/mindrian-platform/skills",
        model: str = "claude-sonnet-4-20250514",
    ):
        self.skills_path = skills_path
        self.model = model

        # Initialize components
        self._skill_loader = SkillLoader(skills_path)
        self._mcp_manager = mcp_manager
        self._registry = AgentRegistry(self._skill_loader, self._mcp_manager)
        self._router = ProblemRouter()

        # Active agents
        self._larry: Optional[LarryAgent] = None
        self._devil: Optional[DevilsAdvocateAgent] = None
        self._active_agents: Dict[str, Agent] = {}

        # Session management
        self._sessions: Dict[str, Session] = {}
        self._current_session: Optional[Session] = None

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator"""
        if self._initialized:
            return

        # Load all skills
        self._skill_loader.load_all()

        # Register all skills as agents
        self._registry.register_all_skills()

        # Create core agents
        self._larry = LarryAgent(mcp_manager=self._mcp_manager)
        self._devil = DevilsAdvocateAgent(mcp_manager=self._mcp_manager)

        self._initialized = True

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create a new conversation session"""
        import uuid
        session_id = session_id or str(uuid.uuid4())

        session = Session(session_id=session_id)
        self._sessions[session_id] = session
        self._current_session = session

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        return self._sessions.get(session_id)

    async def process(
        self,
        user_input: str,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Process user input through the orchestration pipeline.

        Args:
            user_input: User's message
            session_id: Optional session ID (creates new if not provided)

        Returns:
            Agent response
        """
        if not self._initialized:
            await self.initialize()

        # Get or create session
        if session_id:
            session = self.get_session(session_id)
            if not session:
                session = self.create_session(session_id)
        elif not self._current_session:
            session = self.create_session()
        else:
            session = self._current_session

        # Record user message
        session.messages.append({"role": "user", "content": user_input})

        # Process based on current state
        response = await self._process_state(session, user_input)

        # Record assistant response
        session.messages.append({"role": "assistant", "content": response})

        return response

    async def _process_state(self, session: Session, user_input: str) -> str:
        """Process input based on current state"""

        # State: IDLE or CLARIFYING - Use Larry
        if session.state in (OrchestratorState.IDLE, OrchestratorState.CLARIFYING):
            session.state = OrchestratorState.CLARIFYING
            return await self._clarify_with_larry(session, user_input)

        # State: CLASSIFYING - Determine problem type
        elif session.state == OrchestratorState.CLASSIFYING:
            return await self._classify_and_route(session)

        # State: PROCESSING - Run framework agents
        elif session.state == OrchestratorState.PROCESSING:
            return await self._process_with_frameworks(session, user_input)

        # State: VALIDATING - Devil's advocate
        elif session.state == OrchestratorState.VALIDATING:
            return await self._validate_with_devil(session, user_input)

        # State: OUTPUTTING - Generate deliverable
        elif session.state == OrchestratorState.OUTPUTTING:
            return await self._generate_output(session, user_input)

        return "I'm not sure how to proceed. Let's start fresh."

    async def _clarify_with_larry(self, session: Session, user_input: str) -> str:
        """Use Larry to clarify the problem"""

        # Build conversation context
        context = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in session.messages[-10:]  # Last 10 messages
        ])

        # Get Larry's response
        response = await self._larry.run(user_input)

        # Check if Larry thinks problem is clear
        if self._larry.should_transition_to_output():
            session.state = OrchestratorState.CLASSIFYING

            # Store problem description
            summary = self._larry.get_summary()
            session.problem_description = (
                f"Problem: {summary['problem']['what']}\n"
                f"Who: {summary['problem']['who']}\n"
                f"Success: {summary['problem']['success']}"
            )

            # Add transition message
            response += "\n\n---\n\nI think I understand. Let me classify this and suggest next steps..."

        return response

    async def _classify_and_route(self, session: Session) -> str:
        """Classify the problem and determine routing"""

        # Get problem clarity
        clarity = self._larry.state.problem_clarity_score()

        # Classify
        decision = self._router.classify(
            session.problem_description or "",
            clarity_score=clarity,
        )

        session.problem_type = decision.problem_type
        session.routing_decision = decision

        # Move to processing
        session.state = OrchestratorState.PROCESSING

        # Build response
        response = f"""
**Problem Classification:** {decision.problem_type.value}

{decision.reasoning}

**Recommended Approach:**
- Primary frameworks: {', '.join(decision.frameworks)}
- Analysis depth: {'Deep exploration' if decision.problem_type == ProblemType.UNDEFINED else 'Strategic analysis' if decision.problem_type == ProblemType.ILL_DEFINED else 'Tactical planning'}

Would you like me to proceed with this analysis, or would you prefer a different approach?
"""
        return response

    async def _process_with_frameworks(self, session: Session, user_input: str) -> str:
        """Process with appropriate framework agents"""

        # Check for user confirmation
        if "yes" in user_input.lower() or "proceed" in user_input.lower():
            # Get first framework
            if session.routing_decision:
                framework = session.routing_decision.frameworks[0]

                # Create framework agent
                try:
                    agent = self._registry.create(framework)
                    self._active_agents[framework] = agent

                    # Run framework
                    framework_input = f"""
Analyze the following problem using the {framework} framework:

{session.problem_description}

Context from clarification:
{self._larry.get_summary()}
"""
                    response = await agent.arun(framework_input)

                    # Store output
                    session.agent_outputs[framework] = response.content

                    # Move to validation
                    session.state = OrchestratorState.VALIDATING

                    return response.content + "\n\n---\n\nWould you like me to challenge this analysis?"

                except Exception as e:
                    return f"I couldn't load the {framework} framework. Error: {e}"

        return "Let me know if you'd like to proceed with the analysis, or if you have other preferences."

    async def _validate_with_devil(self, session: Session, user_input: str) -> str:
        """Use Devil's Advocate to challenge the analysis"""

        if "yes" in user_input.lower() or "challenge" in user_input.lower():
            # Get last framework output
            last_output = list(session.agent_outputs.values())[-1] if session.agent_outputs else ""

            # Run devil's advocate
            challenge_input = f"""
Challenge the following analysis. Find weaknesses and potential issues:

{last_output}

Original problem:
{session.problem_description}
"""
            response = await self._devil.run(challenge_input)

            # Move to output
            session.state = OrchestratorState.OUTPUTTING

            return response + "\n\n---\n\nWould you like me to generate a final deliverable?"

        return "Should I challenge this analysis with a devil's advocate perspective?"

    async def _generate_output(self, session: Session, user_input: str) -> str:
        """Generate final deliverable"""

        # Compile all outputs
        all_outputs = "\n\n---\n\n".join([
            f"## {framework}\n{output}"
            for framework, output in session.agent_outputs.items()
        ])

        # Generate synthesis
        synthesis = f"""
# Analysis Summary

## Problem Statement
{session.problem_description}

## Classification
Type: {session.problem_type.value if session.problem_type else 'Unknown'}

## Analysis Results
{all_outputs}

## Recommended Next Steps
Based on this analysis, here are the recommended next steps:
1. Review the findings with key stakeholders
2. Address any weaknesses identified
3. Develop detailed implementation plan

---
*Generated by Mindrian*
"""

        session.state = OrchestratorState.COMPLETE
        session.deliverables.append({
            "type": "analysis_summary",
            "content": synthesis,
        })

        return synthesis

    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of a session"""
        session = self.get_session(session_id) if session_id else self._current_session
        if not session:
            return {}

        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "problem_type": session.problem_type.value if session.problem_type else None,
            "problem_description": session.problem_description,
            "message_count": len(session.messages),
            "frameworks_used": list(session.agent_outputs.keys()),
            "deliverables_count": len(session.deliverables),
            "larry_summary": self._larry.get_summary() if self._larry else {},
        }

    def set_larry_mode(self, mode: LarryMode) -> None:
        """Change Larry's conversation mode"""
        if self._larry:
            self._larry.set_mode(mode)

    def get_available_frameworks(self) -> List[str]:
        """Get list of available frameworks"""
        return self._skill_loader.list_all()

    def get_registered_agents(self) -> List[str]:
        """Get list of registered agents"""
        return self._registry.list_all()
