"""
Handoff Tools - Functions Larry Uses to Delegate and Transfer

These are the actual tools that Larry (or any orchestrator) uses
to hand off work to other agents.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from .types import HandoffType, HandoffMode, ReturnBehavior
from .context import HandoffContext, HandoffResult, ProblemClarity


# =============================================================================
# TOOL DEFINITIONS (for use with Agno's tool system)
# =============================================================================

def create_handoff_tool(
    handoff_manager: "HandoffManager",
    available_agents: Dict[str, str],  # agent_id -> description
) -> Callable:
    """
    Create a handoff tool for Larry to use.

    This tool allows Larry to delegate work to specialized frameworks.
    """

    async def delegate_to_framework(
        framework_id: str,
        task: str,
        problem_what: str = "",
        problem_who: str = "",
        problem_success: str = "",
        expected_output: str = "",
        focus_areas: Optional[List[str]] = None,
    ) -> str:
        """
        Delegate a task to a specialized framework.

        Args:
            framework_id: ID of the framework to delegate to
            task: Clear description of what the framework should do
            problem_what: The problem being solved
            problem_who: Who has this problem
            problem_success: What success looks like
            expected_output: What format/content expected back
            focus_areas: Specific areas to focus on

        Returns:
            The framework's analysis output
        """
        # Validate framework exists
        if framework_id not in available_agents:
            available = ", ".join(available_agents.keys())
            return f"Error: Framework '{framework_id}' not found. Available: {available}"

        # Create handoff context
        context = handoff_manager.create_delegation(
            from_agent="larry",
            to_agent=framework_id,
            task=task,
            problem_clarity={
                "what": problem_what,
                "who": problem_who,
                "success": problem_success,
                "what_clarity": 0.8 if problem_what else 0.0,
                "who_clarity": 0.8 if problem_who else 0.0,
                "success_clarity": 0.8 if problem_success else 0.0,
            },
            expected_output=expected_output,
            focus_areas=focus_areas,
        )

        # Execute handoff
        result = await handoff_manager.execute(context)

        if result.success:
            return result.output
        else:
            return f"Error from {framework_id}: {result.error}"

    # Add metadata for Agno
    delegate_to_framework.__name__ = "delegate_to_framework"
    delegate_to_framework.__doc__ = f"""
Delegate a task to a specialized thinking framework.

Available frameworks:
{chr(10).join(f'- {k}: {v}' for k, v in available_agents.items())}

Use this when:
1. The problem is clear enough for analysis (clarity > 60%)
2. A specific type of thinking is needed
3. User is ready for structured output

Do NOT use this when:
1. Problem is still unclear
2. User hasn't answered What/Who/Success
3. More clarification is needed
"""

    return delegate_to_framework


def create_team_handoff_tool(
    handoff_manager: "HandoffManager",
    available_teams: Dict[str, Dict[str, Any]],  # team_id -> {description, members, mode}
) -> Callable:
    """
    Create a tool for delegating to entire teams.
    """

    async def delegate_to_team(
        team_id: str,
        task: str,
        problem_what: str = "",
        problem_who: str = "",
        problem_success: str = "",
        key_points: Optional[List[str]] = None,
    ) -> str:
        """
        Delegate a task to a framework team for comprehensive analysis.

        Args:
            team_id: ID of the team (validation-team, exploration-team, etc.)
            task: Clear description of what the team should analyze
            problem_what: The problem being solved
            problem_who: Who has this problem
            problem_success: What success looks like
            key_points: Key discussion points from clarification

        Returns:
            Synthesized output from all team members
        """
        if team_id not in available_teams:
            available = ", ".join(available_teams.keys())
            return f"Error: Team '{team_id}' not found. Available: {available}"

        team_info = available_teams[team_id]
        members = team_info.get("members", [])
        mode = team_info.get("mode", HandoffMode.SEQUENTIAL)

        # Create contexts for each team member
        contexts = []
        for member_id in members:
            context = handoff_manager.create_delegation(
                from_agent="larry",
                to_agent=member_id,
                task=task,
                problem_clarity={
                    "what": problem_what,
                    "who": problem_who,
                    "success": problem_success,
                },
                conversation_context={
                    "key_points": key_points or [],
                },
            )
            contexts.append(context)

        # Execute based on mode
        if mode == HandoffMode.SEQUENTIAL:
            results = await handoff_manager.execute_sequential(contexts)
        elif mode == HandoffMode.PARALLEL:
            results = await handoff_manager.execute_parallel(contexts)
        elif mode == HandoffMode.DEBATE:
            results = await handoff_manager.execute_debate(contexts)
        else:
            results = await handoff_manager.execute_sequential(contexts)

        # Synthesize results
        synthesis = await handoff_manager.synthesize(
            results=results,
            context=contexts[0] if contexts else None,
            synthesis_instructions=team_info.get("synthesizer_prompt", ""),
        )

        return synthesis

    delegate_to_team.__name__ = "delegate_to_team"
    delegate_to_team.__doc__ = f"""
Delegate a task to a framework team for multi-perspective analysis.

Available teams:
{chr(10).join(f'- {k}: {v.get("description", "")}' for k, v in available_teams.items())}

Teams run multiple frameworks together and synthesize their outputs.
Use teams for comprehensive analysis, use individual frameworks for focused work.
"""

    return delegate_to_team


def create_return_tool() -> Callable:
    """
    Create a tool for frameworks to return results to Larry.

    This is used when a framework completes its work.
    """

    def return_to_orchestrator(
        output: str,
        key_findings: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        confidence: float = 0.0,
        suggested_next: Optional[List[str]] = None,
        open_questions: Optional[List[str]] = None,
    ) -> HandoffResult:
        """
        Return results to the orchestrator (Larry).

        Args:
            output: Main analysis output
            key_findings: List of key findings
            recommendations: List of recommendations
            confidence: Confidence in the analysis (0.0-1.0)
            suggested_next: Suggested next frameworks to consult
            open_questions: Questions that remain unanswered

        Returns:
            HandoffResult for the orchestrator
        """
        return HandoffResult(
            handoff_id="",  # Will be filled by manager
            from_agent="",  # Will be filled by manager
            to_agent="larry",
            success=True,
            output=output,
            key_findings=key_findings or [],
            recommendations=recommendations or [],
            confidence=confidence,
            suggested_next_agents=suggested_next or [],
            open_questions=open_questions or [],
        )

    return return_to_orchestrator


def create_escalate_tool() -> Callable:
    """
    Create a tool for agents to escalate to human input.
    """

    def escalate_to_human(
        reason: str,
        question: str,
        options: Optional[List[str]] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Escalate to human input when agent cannot proceed.

        Args:
            reason: Why human input is needed
            question: What to ask the human
            options: Optional list of choices
            context: Additional context for the human

        Returns:
            Escalation request for the orchestrator
        """
        return {
            "type": "escalation",
            "reason": reason,
            "question": question,
            "options": options or [],
            "context": context,
            "needs_human_input": True,
        }

    return escalate_to_human


# =============================================================================
# LARRY'S HANDOFF INSTRUCTIONS
# =============================================================================

LARRY_HANDOFF_INSTRUCTIONS = """
## How to Use Handoffs

You have access to specialized frameworks via the `delegate_to_framework` and
`delegate_to_team` tools. Here's when and how to use them:

### When to Delegate

1. **Problem is clear** - You've established What, Who, and Success (clarity > 60%)
2. **User is ready** - They've confirmed they want analysis, not more clarification
3. **Right framework exists** - You have a framework suited to their need

### When NOT to Delegate

1. **Problem is still vague** - Keep clarifying
2. **User hasn't confirmed** - Ask if they're ready for analysis
3. **Simple question** - Just answer it yourself

### How to Delegate

1. **Summarize first**: "So the problem is X, affecting Y, success means Z"
2. **Announce the handoff**: "I'm going to bring in [Framework] to help with [purpose]"
3. **Provide clear context**: Use all the What/Who/Success information
4. **Set expectations**: Tell user what output to expect

### After Receiving Results

1. **Synthesize**: Don't just pass through - interpret the results
2. **Highlight key points**: What's most important for this user?
3. **Suggest next steps**: What should they do with this information?
4. **Offer to continue**: "Would you like to challenge this with Devil's Advocate?"

### Available Frameworks

**For Validation:**
- `pws-validation` - Score opportunities (GO/PIVOT/NO-GO)
- `devil-advocate` - Stress-test ideas
- `jobs-to-be-done` - Map customer jobs

**For Exploration:**
- `cynefin` - Classify problem complexity
- `scenario-planning` - Explore futures
- `trending-absurd` - Extrapolate trends

**For Strategy:**
- `minto-pyramid` - Structure communication (SCQA)
- `business-model-canvas` - Design business model
- `golden-circle` - Articulate WHY/HOW/WHAT

**For Innovation:**
- `design-thinking` - Human-centered discovery
- `six-hats` - Multi-perspective analysis

**For Decisions:**
- `thinking-bets` - Probabilistic reasoning
- `premortem` - Failure prevention

### Available Teams

- `validation-team` - PWS → Devil → JTBD (sequential)
- `exploration-team` - Cynefin + Scenarios + Trends (parallel)
- `strategy-team` - Minto → BMC → Golden Circle (pipeline)
- `innovation-team` - Design Thinking → Six Hats → JTBD (sequential)
- `decision-team` - Cynefin + Bets + Pre-mortem (debate)
- `communication-team` - Minto → Golden Circle (pipeline)

Use individual frameworks for focused analysis.
Use teams for comprehensive multi-perspective analysis.
"""
