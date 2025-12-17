"""
Framework Team Registry

Manages bundles of frameworks that work together as coordinated teams.
Each team has a specific purpose and execution mode.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb


class TeamMode(str, Enum):
    """How team members execute"""

    SEQUENTIAL = "sequential"      # One after another, each builds on previous
    PARALLEL = "parallel"          # All at once, results combined
    COLLABORATIVE = "collaborative"  # Back-and-forth discussion
    PIPELINE = "pipeline"          # Output of one feeds into next
    DEBATE = "debate"              # Opposing views synthesized


@dataclass
class TeamMember:
    """A framework agent within a team"""

    agent_id: str
    name: str
    role: str  # What this member contributes to the team
    instructions: str

    # Execution config
    receives_from: List[str] = field(default_factory=list)  # Agent IDs that feed into this
    required: bool = True  # Must complete for team to succeed
    timeout_seconds: int = 120

    # Runtime
    agent: Optional[Agent] = None
    output: Optional[str] = None


@dataclass
class FrameworkTeam:
    """A coordinated bundle of framework agents"""

    team_id: str
    name: str
    description: str
    purpose: str  # What problem this team solves

    # Team composition
    members: List[TeamMember] = field(default_factory=list)
    mode: TeamMode = TeamMode.SEQUENTIAL

    # Execution config
    synthesizer_prompt: str = ""  # How to combine outputs
    success_criteria: str = ""     # What makes a successful team run

    # Problem type mapping
    suited_for: List[str] = field(default_factory=list)  # Problem types this team handles

    # Metadata
    tags: List[str] = field(default_factory=list)

    def get_member(self, agent_id: str) -> Optional[TeamMember]:
        """Get a team member by ID"""
        for member in self.members:
            if member.agent_id == agent_id:
                return member
        return None


@dataclass
class TeamExecutionResult:
    """Result of running a team"""

    team_id: str
    success: bool
    mode: TeamMode

    # Individual outputs
    member_outputs: Dict[str, str] = field(default_factory=dict)

    # Synthesized output
    synthesis: str = ""

    # Execution metadata
    execution_order: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0


class TeamRegistry:
    """Registry and executor for framework teams"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self._teams: Dict[str, FrameworkTeam] = {}
        self._model = model
        self._db = SqliteDb(db_file="tmp/mindrian.db")

    def register(self, team: FrameworkTeam) -> None:
        """Register a team"""
        self._teams[team.team_id] = team

    def get(self, team_id: str) -> Optional[FrameworkTeam]:
        """Get a team by ID"""
        return self._teams.get(team_id)

    def list_all(self) -> List[str]:
        """List all registered team IDs"""
        return list(self._teams.keys())

    def list_by_purpose(self, purpose_keyword: str) -> List[FrameworkTeam]:
        """Find teams by purpose"""
        return [
            team for team in self._teams.values()
            if purpose_keyword.lower() in team.purpose.lower()
            or purpose_keyword.lower() in team.description.lower()
        ]

    def get_team_for_problem(self, problem_type: str) -> Optional[FrameworkTeam]:
        """Get the best team for a problem type"""
        for team in self._teams.values():
            if problem_type.lower() in [s.lower() for s in team.suited_for]:
                return team
        return None

    def _create_agent(self, member: TeamMember) -> Agent:
        """Create an Agno agent from a team member"""
        return Agent(
            name=member.name,
            id=member.agent_id,  # v2: agent_id → id
            model=Claude(id=self._model),
            description=member.role,
            instructions=[member.instructions] if member.instructions else [],
            db=self._db,
            add_history_to_context=True,
            markdown=True,
        )

    async def execute(
        self,
        team_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TeamExecutionResult:
        """
        Execute a team on a task.

        Args:
            team_id: ID of the team to execute
            task: The task/problem to work on
            context: Optional context from Larry's clarification

        Returns:
            TeamExecutionResult with all outputs
        """
        import time
        start_time = time.time()

        team = self.get(team_id)
        if not team:
            return TeamExecutionResult(
                team_id=team_id,
                success=False,
                mode=TeamMode.SEQUENTIAL,
                errors={"team": f"Team '{team_id}' not found"},
            )

        # Build context prompt
        context_prompt = ""
        if context:
            context_prompt = f"""
## Context from Clarification

**Problem:** {context.get('problem', 'Not specified')}
**Who:** {context.get('who', 'Not specified')}
**Success:** {context.get('success', 'Not specified')}
**Problem Type:** {context.get('problem_type', 'Not specified')}
"""

        # Execute based on mode
        if team.mode == TeamMode.SEQUENTIAL:
            result = await self._execute_sequential(team, task, context_prompt)
        elif team.mode == TeamMode.PARALLEL:
            result = await self._execute_parallel(team, task, context_prompt)
        elif team.mode == TeamMode.PIPELINE:
            result = await self._execute_pipeline(team, task, context_prompt)
        elif team.mode == TeamMode.DEBATE:
            result = await self._execute_debate(team, task, context_prompt)
        else:
            result = await self._execute_collaborative(team, task, context_prompt)

        result.duration_seconds = time.time() - start_time

        # Synthesize outputs
        if result.success and result.member_outputs:
            result.synthesis = await self._synthesize(team, result.member_outputs, task)

        return result

    async def _execute_sequential(
        self,
        team: FrameworkTeam,
        task: str,
        context: str,
    ) -> TeamExecutionResult:
        """Execute members one after another"""
        result = TeamExecutionResult(
            team_id=team.team_id,
            success=True,
            mode=TeamMode.SEQUENTIAL,
        )

        accumulated_context = context

        for member in team.members:
            try:
                agent = self._create_agent(member)

                prompt = f"""
# Task
{task}

{accumulated_context}

## Your Role: {member.role}

Please analyze this task using your framework and provide your output.
"""

                response = await agent.arun(prompt)
                output = response.content if hasattr(response, 'content') else str(response)

                result.member_outputs[member.agent_id] = output
                result.execution_order.append(member.agent_id)

                # Add to accumulated context for next member
                accumulated_context += f"\n\n## {member.name}'s Analysis\n{output}"

            except Exception as e:
                result.errors[member.agent_id] = str(e)
                if member.required:
                    result.success = False
                    break

        return result

    async def _execute_parallel(
        self,
        team: FrameworkTeam,
        task: str,
        context: str,
    ) -> TeamExecutionResult:
        """Execute all members simultaneously"""
        result = TeamExecutionResult(
            team_id=team.team_id,
            success=True,
            mode=TeamMode.PARALLEL,
        )

        async def run_member(member: TeamMember) -> tuple:
            try:
                agent = self._create_agent(member)

                prompt = f"""
# Task
{task}

{context}

## Your Role: {member.role}

Please analyze this task using your framework and provide your output.
"""

                response = await agent.arun(prompt)
                output = response.content if hasattr(response, 'content') else str(response)
                return (member.agent_id, output, None)

            except Exception as e:
                return (member.agent_id, None, str(e))

        # Run all members in parallel
        tasks = [run_member(member) for member in team.members]
        results = await asyncio.gather(*tasks)

        for agent_id, output, error in results:
            if output:
                result.member_outputs[agent_id] = output
                result.execution_order.append(agent_id)
            if error:
                result.errors[agent_id] = error
                member = team.get_member(agent_id)
                if member and member.required:
                    result.success = False

        return result

    async def _execute_pipeline(
        self,
        team: FrameworkTeam,
        task: str,
        context: str,
    ) -> TeamExecutionResult:
        """Execute as a pipeline where each output feeds the next"""
        result = TeamExecutionResult(
            team_id=team.team_id,
            success=True,
            mode=TeamMode.PIPELINE,
        )

        previous_output = ""

        for i, member in enumerate(team.members):
            try:
                agent = self._create_agent(member)

                if i == 0:
                    # First member gets original task
                    prompt = f"""
# Task
{task}

{context}

## Your Role: {member.role}

Please analyze this task and provide your output for the next stage.
"""
                else:
                    # Subsequent members get previous output
                    prompt = f"""
# Task
{task}

{context}

## Input from Previous Stage
{previous_output}

## Your Role: {member.role}

Build on the previous analysis and add your perspective.
"""

                response = await agent.arun(prompt)
                output = response.content if hasattr(response, 'content') else str(response)

                result.member_outputs[member.agent_id] = output
                result.execution_order.append(member.agent_id)
                previous_output = output

            except Exception as e:
                result.errors[member.agent_id] = str(e)
                if member.required:
                    result.success = False
                    break

        return result

    async def _execute_debate(
        self,
        team: FrameworkTeam,
        task: str,
        context: str,
    ) -> TeamExecutionResult:
        """Execute as a debate with opposing views"""
        result = TeamExecutionResult(
            team_id=team.team_id,
            success=True,
            mode=TeamMode.DEBATE,
        )

        # Round 1: Initial positions
        positions = {}
        for member in team.members:
            try:
                agent = self._create_agent(member)

                prompt = f"""
# Task
{task}

{context}

## Your Role: {member.role}

Take your position on this task. Be clear about your perspective.
"""

                response = await agent.arun(prompt)
                output = response.content if hasattr(response, 'content') else str(response)
                positions[member.agent_id] = output

            except Exception as e:
                result.errors[member.agent_id] = str(e)

        # Round 2: Responses to each other
        all_positions = "\n\n---\n\n".join([
            f"**{team.get_member(aid).name}:** {pos}"
            for aid, pos in positions.items()
        ])

        for member in team.members:
            try:
                agent = self._create_agent(member)

                prompt = f"""
# Task
{task}

## All Positions
{all_positions}

## Your Role: {member.role}

Respond to the other perspectives. What do you agree with? What do you challenge?
Provide your refined position.
"""

                response = await agent.arun(prompt)
                output = response.content if hasattr(response, 'content') else str(response)

                result.member_outputs[member.agent_id] = f"**Initial:**\n{positions.get(member.agent_id, '')}\n\n**After Debate:**\n{output}"
                result.execution_order.append(member.agent_id)

            except Exception as e:
                result.errors[member.agent_id] = str(e)

        return result

    async def _execute_collaborative(
        self,
        team: FrameworkTeam,
        task: str,
        context: str,
    ) -> TeamExecutionResult:
        """Execute collaboratively with back-and-forth"""
        # For now, use sequential as fallback
        return await self._execute_sequential(team, task, context)

    async def _synthesize(
        self,
        team: FrameworkTeam,
        outputs: Dict[str, str],
        task: str,
    ) -> str:
        """Synthesize all team outputs into a coherent result"""

        # Build synthesis prompt
        all_outputs = "\n\n---\n\n".join([
            f"## {team.get_member(aid).name if team.get_member(aid) else aid}\n{output}"
            for aid, output in outputs.items()
        ])

        synthesizer = Agent(
            name="Team Synthesizer",
            id="team-synthesizer",  # v2: agent_id → id
            model=Claude(id=self._model),
            instructions=[team.synthesizer_prompt] if team.synthesizer_prompt else [
                "You are a synthesis expert.",
                "Combine multiple framework analyses into a coherent, actionable summary.",
                "Identify: 1. Key insights that multiple frameworks agree on",
                "2. Tensions or contradictions to resolve",
                "3. Clear recommendations and next steps",
                "4. What's still uncertain or needs more exploration",
            ],
            db=self._db,
            markdown=True,
        )

        prompt = f"""
# Original Task
{task}

# Team Analysis ({team.name})

{all_outputs}

---

# Your Task

Synthesize these analyses into a coherent summary. What are the key takeaways?
What should the user do next?
"""

        response = await synthesizer.arun(prompt)
        return response.content if hasattr(response, 'content') else str(response)


# Global registry instance
team_registry = TeamRegistry()
