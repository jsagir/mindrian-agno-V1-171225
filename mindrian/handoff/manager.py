"""
Handoff Manager - Executes and Tracks Agent Handoffs

The central coordinator for all agent-to-agent communication in Mindrian.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

from .types import HandoffType, HandoffMode, ReturnBehavior
from .context import HandoffContext, HandoffResult, PreviousAnalysis


@dataclass
class ActiveHandoff:
    """Tracks an in-progress handoff"""
    handoff_id: str
    context: HandoffContext
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[HandoffResult] = None


class HandoffManager:
    """
    Manages all agent handoffs in Mindrian.

    Key Responsibilities:
    1. Create handoff contexts with proper state
    2. Execute handoffs (delegate, transfer, return)
    3. Track handoff history for synthesis
    4. Handle errors and timeouts
    5. Support different handoff modes (sequential, parallel, debate)
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self._model = model
        self._db = SqliteDb(db_file="tmp/mindrian.db")

        # Registered agents
        self._agents: Dict[str, Agent] = {}

        # Active handoffs
        self._active_handoffs: Dict[str, ActiveHandoff] = {}

        # Handoff history (for session continuity)
        self._history: List[ActiveHandoff] = []

        # Callbacks
        self._on_handoff_start: Optional[Callable] = None
        self._on_handoff_complete: Optional[Callable] = None

    def register_agent(self, agent_id: str, agent: Agent) -> None:
        """Register an agent for handoffs"""
        self._agents[agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get a registered agent"""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all registered agent IDs"""
        return list(self._agents.keys())

    # =========================================================================
    # HANDOFF CREATION
    # =========================================================================

    def create_delegation(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        problem_clarity: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
        expected_output: str = "",
        focus_areas: Optional[List[str]] = None,
        mode: HandoffMode = HandoffMode.SEQUENTIAL,
        return_behavior: ReturnBehavior = ReturnBehavior.SYNTHESIZE,
    ) -> HandoffContext:
        """
        Create a delegation handoff (most common pattern).

        Larry delegates to a framework or team, expects results back.
        """
        from .context import ProblemClarity, ConversationSummary

        # Build problem clarity
        clarity = ProblemClarity()
        if problem_clarity:
            clarity.what = problem_clarity.get("what", "")
            clarity.who = problem_clarity.get("who", "")
            clarity.success = problem_clarity.get("success", "")
            clarity.what_clarity = problem_clarity.get("what_clarity", 0.0)
            clarity.who_clarity = problem_clarity.get("who_clarity", 0.0)
            clarity.success_clarity = problem_clarity.get("success_clarity", 0.0)
            clarity.assumptions = problem_clarity.get("assumptions", [])
            clarity.open_questions = problem_clarity.get("open_questions", [])

        # Build conversation summary
        conversation = ConversationSummary()
        if conversation_context:
            conversation.key_points = conversation_context.get("key_points", [])
            conversation.user_goals = conversation_context.get("user_goals", [])
            conversation.constraints = conversation_context.get("constraints", [])
            conversation.preferences = conversation_context.get("preferences", [])
            conversation.recent_messages = conversation_context.get("recent_messages", [])

        # Build previous analyses
        analyses = []
        if previous_analyses:
            for pa in previous_analyses:
                analyses.append(PreviousAnalysis(
                    framework_id=pa.get("framework_id", ""),
                    framework_name=pa.get("framework_name", ""),
                    output=pa.get("output", ""),
                    key_findings=pa.get("key_findings", []),
                    recommendations=pa.get("recommendations", []),
                    confidence=pa.get("confidence", 0.0),
                ))

        return HandoffContext(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=clarity,
            conversation=conversation,
            previous_analyses=analyses,
            task_description=task,
            expected_output=expected_output,
            focus_areas=focus_areas or [],
            from_agent=from_agent,
            to_agent=to_agent,
            return_to=from_agent,  # Delegation returns to sender
            return_behavior=return_behavior,
            handoff_type=HandoffType.DELEGATE,
            handoff_mode=mode,
        )

    def create_transfer(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        context: HandoffContext,
    ) -> HandoffContext:
        """
        Create a transfer handoff (full control change).

        Used when user should talk directly to another agent.
        """
        transfer_context = HandoffContext(
            handoff_id=str(uuid.uuid4())[:8],
            problem_clarity=context.problem_clarity,
            conversation=context.conversation,
            previous_analyses=context.previous_analyses,
            task_description=f"Taking over conversation. Reason: {reason}",
            from_agent=from_agent,
            to_agent=to_agent,
            return_to="",  # No return - full transfer
            handoff_type=HandoffType.TRANSFER,
        )
        return transfer_context

    def create_return(
        self,
        from_agent: str,
        to_agent: str,
        output: str,
        key_findings: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        confidence: float = 0.0,
        scores: Optional[Dict[str, float]] = None,
        suggested_next: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
    ) -> HandoffResult:
        """
        Create a return from completed work.

        Framework returns results to orchestrator.
        """
        return HandoffResult(
            handoff_id="",  # Will be set by executor
            from_agent=from_agent,
            to_agent=to_agent,
            success=True,
            output=output,
            key_findings=key_findings or [],
            recommendations=recommendations or [],
            confidence=confidence,
            scores=scores or {},
            suggested_next_agents=suggested_next or [],
            open_questions=open_questions or [],
        )

    # =========================================================================
    # HANDOFF EXECUTION
    # =========================================================================

    async def execute(
        self,
        context: HandoffContext,
        timeout: int = 300,
    ) -> HandoffResult:
        """
        Execute a single handoff.

        Args:
            context: The handoff context with all state
            timeout: Max seconds to wait

        Returns:
            HandoffResult with output or error
        """
        import time
        start_time = time.time()

        # Track the handoff
        active = ActiveHandoff(
            handoff_id=context.handoff_id,
            context=context,
            status="running",
            started_at=datetime.now(),
        )
        self._active_handoffs[context.handoff_id] = active

        # Notify start
        if self._on_handoff_start:
            self._on_handoff_start(context)

        try:
            # Get the target agent
            agent = self.get_agent(context.to_agent)
            if not agent:
                raise ValueError(f"Agent '{context.to_agent}' not registered")

            # Build the prompt from context
            prompt = context.to_prompt()

            # Execute with timeout
            try:
                response = await asyncio.wait_for(
                    agent.arun(prompt),
                    timeout=timeout
                )
                output = response.content if hasattr(response, 'content') else str(response)

            except asyncio.TimeoutError:
                raise TimeoutError(f"Handoff to {context.to_agent} timed out after {timeout}s")

            # Build result
            result = HandoffResult(
                handoff_id=context.handoff_id,
                from_agent=context.to_agent,
                to_agent=context.return_to,
                success=True,
                output=output,
                duration_seconds=time.time() - start_time,
            )

            # Update tracking
            active.status = "completed"
            active.completed_at = datetime.now()
            active.result = result
            self._history.append(active)

            # Notify completion
            if self._on_handoff_complete:
                self._on_handoff_complete(result)

            return result

        except Exception as e:
            # Build error result
            result = HandoffResult(
                handoff_id=context.handoff_id,
                from_agent=context.to_agent,
                to_agent=context.return_to,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

            active.status = "failed"
            active.completed_at = datetime.now()
            active.result = result
            self._history.append(active)

            return result

        finally:
            # Clean up active tracking
            if context.handoff_id in self._active_handoffs:
                del self._active_handoffs[context.handoff_id]

    async def execute_sequential(
        self,
        contexts: List[HandoffContext],
    ) -> List[HandoffResult]:
        """
        Execute handoffs sequentially, passing context forward.

        Each agent receives the output of the previous agent.
        """
        results = []
        accumulated_context = None

        for i, context in enumerate(contexts):
            # Add previous results to context
            if accumulated_context and results:
                context.previous_analyses.append(results[-1].to_analysis())

            # Execute
            result = await self.execute(context)
            results.append(result)

            # Stop on failure
            if not result.success:
                break

        return results

    async def execute_parallel(
        self,
        contexts: List[HandoffContext],
    ) -> List[HandoffResult]:
        """
        Execute all handoffs in parallel.

        All agents work simultaneously, results combined.
        """
        tasks = [self.execute(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(HandoffResult(
                    handoff_id=contexts[i].handoff_id,
                    from_agent=contexts[i].to_agent,
                    to_agent=contexts[i].return_to,
                    success=False,
                    error=str(result),
                ))
            else:
                final_results.append(result)

        return final_results

    async def execute_debate(
        self,
        contexts: List[HandoffContext],
        rounds: int = 2,
    ) -> List[HandoffResult]:
        """
        Execute as a debate with multiple rounds.

        Round 1: All agents give initial positions
        Round 2+: Agents respond to each other
        """
        all_results = []

        # Round 1: Initial positions
        round1_results = await self.execute_parallel(contexts)
        all_results.extend(round1_results)

        # Subsequent rounds
        for round_num in range(2, rounds + 1):
            # Build context with all previous positions
            positions_summary = "\n\n---\n\n".join([
                f"**{r.from_agent}:** {r.output}"
                for r in all_results if r.success
            ])

            # Create new contexts for this round
            round_contexts = []
            for ctx in contexts:
                new_ctx = HandoffContext(
                    handoff_id=str(uuid.uuid4())[:8],
                    problem_clarity=ctx.problem_clarity,
                    conversation=ctx.conversation,
                    task_description=f"""
Round {round_num} of debate.

## Previous Positions
{positions_summary}

## Your Task
Respond to the other perspectives. What do you agree with? What do you challenge?
Refine your position based on the debate.
""",
                    from_agent=ctx.from_agent,
                    to_agent=ctx.to_agent,
                    return_to=ctx.return_to,
                    handoff_type=HandoffType.DELEGATE,
                )
                round_contexts.append(new_ctx)

            # Execute this round
            round_results = await self.execute_parallel(round_contexts)
            all_results.extend(round_results)

        return all_results

    # =========================================================================
    # SYNTHESIS
    # =========================================================================

    async def synthesize(
        self,
        results: List[HandoffResult],
        context: HandoffContext,
        synthesis_instructions: str = "",
    ) -> str:
        """
        Synthesize multiple handoff results into a coherent output.

        This is what Larry does after receiving framework outputs.
        """
        # Build synthesis prompt
        all_outputs = "\n\n---\n\n".join([
            f"## {r.from_agent}\n{r.output}"
            for r in results if r.success
        ])

        synthesizer = Agent(
            name="Synthesizer",
            agent_id="synthesizer",
            model=Claude(id=self._model),
            instructions=synthesis_instructions or """
You synthesize multiple framework analyses into a coherent summary.

Your job:
1. Identify key insights that multiple frameworks agree on
2. Highlight tensions or contradictions to resolve
3. Provide clear, actionable recommendations
4. Note what remains uncertain
5. Suggest concrete next steps

Be concise but comprehensive. The user should have a clear path forward.
""",
            db=self._db,
            markdown=True,
        )

        prompt = f"""
# Synthesis Request

## Original Problem
{context.problem_clarity.to_prompt()}

## Framework Analyses
{all_outputs}

## Your Task
Synthesize these analyses into a clear, actionable summary for the user.
"""

        response = await synthesizer.arun(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    # =========================================================================
    # STATE & HISTORY
    # =========================================================================

    def get_active_handoffs(self) -> List[ActiveHandoff]:
        """Get all currently active handoffs"""
        return list(self._active_handoffs.values())

    def get_history(self, limit: int = 10) -> List[ActiveHandoff]:
        """Get recent handoff history"""
        return self._history[-limit:]

    def get_handoff(self, handoff_id: str) -> Optional[ActiveHandoff]:
        """Get a specific handoff by ID"""
        # Check active first
        if handoff_id in self._active_handoffs:
            return self._active_handoffs[handoff_id]

        # Check history
        for h in self._history:
            if h.handoff_id == handoff_id:
                return h

        return None

    def clear_history(self) -> None:
        """Clear handoff history"""
        self._history.clear()

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_handoff_start(self, callback: Callable) -> None:
        """Set callback for handoff start"""
        self._on_handoff_start = callback

    def on_handoff_complete(self, callback: Callable) -> None:
        """Set callback for handoff completion"""
        self._on_handoff_complete = callback


# Global instance
handoff_manager = HandoffManager()
