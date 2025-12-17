"""
Gemini Deep Research Agent

Integrates Google's Deep Research API (Interactions API) with Mindrian's handoff protocol.
Provides autonomous, multi-step research with citations.

Key Features:
- Background execution (async polling)
- Automatic source citation
- Progress tracking via thinking summaries
- Full HandoffContext/HandoffResult protocol compliance

API Reference:
    https://ai.google.dev/gemini-api/docs/deep-research

Usage:
    # Direct research
    agent = GeminiDeepResearchAgent()
    result = await agent.research("What are the latest AI agent frameworks?")

    # With handoff context (from orchestrator)
    result = await agent.process_handoff(handoff_context)

    # Convenience function
    result = await deep_research("Market trends in quantum computing")
"""

import asyncio
import time
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from ...handoff.context import HandoffContext, HandoffResult, PreviousAnalysis
from ...handoff.types import HandoffType


@dataclass
class DeepResearchConfig:
    """Configuration for Gemini Deep Research agent"""

    # Timing
    max_wait_seconds: int = 1800  # 30 minutes max (API supports up to 60)
    poll_interval_seconds: int = 10

    # Features
    enable_thinking_summaries: bool = True
    include_sources: bool = True

    # Output
    extract_findings: bool = True
    max_findings: int = 10


class GeminiDeepResearchAgent:
    """
    Gemini Deep Research Agent with Mindrian handoff protocol.

    Uses Google's Interactions API for autonomous multi-step research.
    The agent automatically:
    - Plans research queries
    - Executes searches
    - Reads and synthesizes results
    - Identifies knowledge gaps
    - Iterates until comprehensive

    Attributes:
        AGENT_ID: Unique identifier for handoff routing
        AGENT_NAME: Human-readable name
    """

    AGENT_ID = "gemini-deep-research"
    AGENT_NAME = "Gemini Deep Research"
    AGENT_MODEL = "deep-research-pro-preview-12-2025"

    def __init__(
        self,
        config: Optional[DeepResearchConfig] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Gemini Deep Research agent.

        Args:
            config: Optional configuration override
            api_key: Optional API key (defaults to GOOGLE_API_KEY env var)
        """
        self._config = config or DeepResearchConfig()
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self._api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable required for Gemini Deep Research"
            )

        # Lazy import to avoid dependency issues
        self._client = None

    def _get_client(self):
        """Lazy initialization of Google GenAI client"""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "google-generativeai package required. "
                    "Install with: pip install google-generativeai>=0.8.0"
                )
        return self._client

    async def research(
        self,
        query: str,
        context: str = "",
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute deep research on a topic.

        This method:
        1. Builds a structured research prompt
        2. Submits to Interactions API in background mode
        3. Polls for completion
        4. Returns structured results

        Args:
            query: The research question
            context: Additional context from previous analyses
            focus_areas: Specific areas to investigate

        Returns:
            Dict with:
                - success: bool
                - output: str (research report)
                - thinking_steps: List[str] (reasoning trace)
                - duration_seconds: float
                - interaction_id: str
                - error: str (if failed)
        """
        client = self._get_client()

        # Build the research prompt
        prompt = self._build_research_prompt(query, context, focus_areas)

        # Create interaction (background mode required for Deep Research)
        try:
            interaction = client.interactions.create(
                input=prompt,
                agent=self.AGENT_MODEL,
                background=True,
                agent_config={
                    "thinking_summaries": "auto" if self._config.enable_thinking_summaries else "disabled"
                }
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create interaction: {str(e)}",
                "duration_seconds": 0,
            }

        interaction_id = interaction.id
        start_time = time.time()
        thinking_steps = []

        # Poll for completion
        while True:
            elapsed = time.time() - start_time

            if elapsed > self._config.max_wait_seconds:
                return {
                    "success": False,
                    "error": f"Research timeout after {elapsed:.0f} seconds",
                    "partial_output": thinking_steps,
                    "duration_seconds": elapsed,
                    "interaction_id": interaction_id,
                }

            try:
                interaction = client.interactions.get(interaction_id)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to get interaction status: {str(e)}",
                    "duration_seconds": elapsed,
                    "interaction_id": interaction_id,
                }

            # Capture thinking steps if available
            if hasattr(interaction, 'thinking') and interaction.thinking:
                thinking_steps = interaction.thinking

            if interaction.status == "completed":
                output = ""
                if interaction.outputs and len(interaction.outputs) > 0:
                    output = interaction.outputs[-1].text

                return {
                    "success": True,
                    "output": output,
                    "thinking_steps": thinking_steps,
                    "duration_seconds": elapsed,
                    "interaction_id": interaction_id,
                }

            elif interaction.status == "failed":
                error_msg = getattr(interaction, 'error', 'Unknown error')
                return {
                    "success": False,
                    "error": str(error_msg),
                    "thinking_steps": thinking_steps,
                    "duration_seconds": elapsed,
                    "interaction_id": interaction_id,
                }

            # Wait before next poll
            await asyncio.sleep(self._config.poll_interval_seconds)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """
        Process a handoff from the Mindrian orchestrator.

        Converts HandoffContext to research query, executes research,
        and returns HandoffResult compatible with the handoff protocol.

        Args:
            context: HandoffContext with task description, problem clarity, etc.

        Returns:
            HandoffResult with research output, findings, and metadata
        """
        start_time = time.time()

        # Build research query from handoff context
        query = self._handoff_to_query(context)

        # Build additional context from previous analyses
        additional_context = self._build_analysis_context(context.previous_analyses)

        # Execute research
        result = await self.research(
            query=query,
            context=additional_context,
            focus_areas=context.focus_areas if context.focus_areas else None,
        )

        if result["success"]:
            # Extract structured data from output
            key_findings = []
            recommendations = []

            if self._config.extract_findings:
                key_findings = self._extract_key_findings(result["output"])
                recommendations = self._extract_recommendations(result["output"])

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent=self.AGENT_ID,
                to_agent=context.return_to,
                success=True,
                output=result["output"],
                output_format="markdown",
                key_findings=key_findings,
                recommendations=recommendations,
                confidence=0.85,  # Deep Research produces high-confidence results
                suggested_next_agents=["csio", "domain-analysis", "minto-pyramid"],
                duration_seconds=result["duration_seconds"],
                metadata={
                    "thinking_steps": result.get("thinking_steps", []),
                    "interaction_id": result.get("interaction_id"),
                    "research_type": "gemini-deep-research",
                    "model": self.AGENT_MODEL,
                }
            )
        else:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent=self.AGENT_ID,
                to_agent=context.return_to,
                success=False,
                error=result.get("error", "Unknown research error"),
                duration_seconds=time.time() - start_time,
                metadata={
                    "partial_thinking": result.get("thinking_steps", []),
                    "interaction_id": result.get("interaction_id"),
                }
            )

    def _build_research_prompt(
        self,
        query: str,
        context: str,
        focus_areas: Optional[List[str]],
    ) -> str:
        """Build the research prompt for the Interactions API"""
        prompt_parts = [
            f"# Research Request\n\n{query}",
        ]

        if context:
            prompt_parts.append(f"\n## Context from Previous Analysis\n{context}")

        if focus_areas:
            prompt_parts.append("\n## Focus Areas")
            prompt_parts.extend([f"- {area}" for area in focus_areas])

        prompt_parts.append("""
## Output Requirements

Please provide a comprehensive research report with:

1. **Executive Summary** - Key findings in 2-3 sentences

2. **Detailed Findings** - Comprehensive analysis organized by topic
   - Include citations for all claims
   - Note source credibility

3. **Data & Statistics** - Relevant numbers, trends, and metrics
   - Market size, growth rates, benchmarks
   - Include date/source for all statistics

4. **Key Players** - Companies, researchers, or organizations
   - What they're doing
   - Their approach/solution

5. **Recent Developments** - Latest news and announcements
   - Focus on last 6-12 months
   - Note significance of each development

6. **Expert Perspectives** - Quotes and viewpoints from authorities
   - Academic researchers
   - Industry practitioners
   - Thought leaders

7. **Recommendations** - Actionable next steps based on findings
   - Prioritized by impact and feasibility

8. **Research Gaps** - What we still don't know
   - Areas needing deeper investigation
   - Conflicting information found

9. **Confidence Assessment**
   - What's well-supported by multiple sources
   - What's speculative or from single sources

Use proper citations for all claims. Include URLs where available.
Format as clean markdown for readability.
""")

        return "\n".join(prompt_parts)

    def _handoff_to_query(self, context: HandoffContext) -> str:
        """Convert HandoffContext to research query string"""
        parts = []

        # Main task description
        if context.task_description:
            parts.append(context.task_description)

        # Problem clarity provides structure
        if context.problem_clarity:
            pc = context.problem_clarity

            if pc.what:
                parts.append(f"\n**Problem/Topic:** {pc.what}")
            if pc.who:
                parts.append(f"**Target Audience:** {pc.who}")
            if pc.success:
                parts.append(f"**Success Criteria:** {pc.success}")

            if pc.assumptions:
                parts.append("\n**Assumptions to Validate:**")
                parts.extend([f"- {a}" for a in pc.assumptions])

            if pc.open_questions:
                parts.append("\n**Questions to Answer:**")
                parts.extend([f"- {q}" for q in pc.open_questions])

        # Expected output format
        if context.expected_output:
            parts.append(f"\n**Expected Output:** {context.expected_output}")

        return "\n".join(parts)

    def _build_analysis_context(self, analyses: List[PreviousAnalysis]) -> str:
        """Build context string from previous analyses"""
        if not analyses:
            return ""

        parts = ["## Previous Analyses\n"]

        # Include last 3 analyses to keep context manageable
        for analysis in analyses[-3:]:
            parts.append(f"### {analysis.framework_name}")

            if analysis.key_findings:
                parts.append("\n**Key Findings:**")
                parts.extend([f"- {f}" for f in analysis.key_findings[:5]])

            if analysis.recommendations:
                parts.append("\n**Recommendations:**")
                parts.extend([f"- {r}" for r in analysis.recommendations[:3]])

            parts.append("")

        return "\n".join(parts)

    def _extract_key_findings(self, output: str) -> List[str]:
        """Extract key findings from research output"""
        findings = []
        lines = output.split("\n")
        in_findings_section = False

        for line in lines:
            lower_line = line.lower()

            # Detect findings sections
            if any(marker in lower_line for marker in [
                "executive summary", "key findings", "main findings",
                "summary", "highlights"
            ]):
                in_findings_section = True
                continue

            # Exit on new major section
            if in_findings_section and line.startswith("## "):
                in_findings_section = False
                continue

            # Extract bullet points
            if in_findings_section:
                stripped = line.strip()
                if stripped.startswith("- ") or stripped.startswith("* "):
                    findings.append(stripped[2:])
                elif stripped and stripped[0].isdigit() and ". " in stripped[:4]:
                    # Numbered list: "1. Finding"
                    findings.append(stripped.split(". ", 1)[-1])

        return findings[:self._config.max_findings]

    def _extract_recommendations(self, output: str) -> List[str]:
        """Extract recommendations from research output"""
        recommendations = []
        lines = output.split("\n")
        in_recommendations = False

        for line in lines:
            lower_line = line.lower()

            if "recommendation" in lower_line or "next step" in lower_line:
                in_recommendations = True
                continue

            if in_recommendations and line.startswith("## "):
                break

            if in_recommendations:
                stripped = line.strip()
                if stripped.startswith("- ") or stripped.startswith("* "):
                    recommendations.append(stripped[2:])
                elif stripped and stripped[0].isdigit() and ". " in stripped[:4]:
                    recommendations.append(stripped.split(". ", 1)[-1])

        return recommendations[:5]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def deep_research(
    query: str,
    context: Optional[str] = None,
    focus_areas: Optional[List[str]] = None,
    timeout_seconds: int = 1800,
) -> HandoffResult:
    """
    Convenience function for quick deep research.

    Usage:
        result = await deep_research("What are the latest AI agent frameworks?")
        if result.success:
            print(result.output)
            print("Key findings:", result.key_findings)
        else:
            print("Error:", result.error)

    Args:
        query: The research question
        context: Optional additional context
        focus_areas: Optional list of specific areas to focus on
        timeout_seconds: Max wait time (default 30 minutes)

    Returns:
        HandoffResult with research output
    """
    import uuid

    agent = GeminiDeepResearchAgent(
        config=DeepResearchConfig(max_wait_seconds=timeout_seconds)
    )

    handoff_context = HandoffContext(
        handoff_id=str(uuid.uuid4())[:8],
        task_description=query,
        focus_areas=focus_areas or [],
        from_agent="user",
        to_agent="gemini-deep-research",
        return_to="user",
        timeout_seconds=timeout_seconds,
    )

    if context:
        # Add context via conversation summary
        handoff_context.conversation.key_points.append(context)

    return await agent.process_handoff(handoff_context)


# =============================================================================
# REGISTRATION HELPER
# =============================================================================

def register_with_handoff_manager(manager) -> None:
    """
    Register the Gemini Deep Research agent with a HandoffManager.

    Usage:
        from mindrian.handoff.manager import HandoffManager
        from mindrian.agents.research.gemini_deep_research import register_with_handoff_manager

        manager = HandoffManager()
        register_with_handoff_manager(manager)
    """
    agent = GeminiDeepResearchAgent()
    manager.register_agent(GeminiDeepResearchAgent.AGENT_ID, agent)
