# Google Gemini Deep Research API Integration

> Integrating Google's Deep Research Agent with Mindrian's Handoff Mechanism

---

## Overview

Google's **Gemini Deep Research API** (released December 2025) provides a powerful autonomous research agent that can be integrated into Mindrian's multi-agent orchestration system. This document outlines how to leverage the Interactions API to create a research agent that seamlessly works with Mindrian's `HandoffContext` and `HandoffResult` protocol.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MINDRIAN + GEMINI DEEP RESEARCH INTEGRATION                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────┐     HandoffContext      ┌────────────────────────┐           │
│   │    Larry     │ ─────────────────────► │  GeminiDeepResearch    │           │
│   │  (Clarifier) │                         │       Agent            │           │
│   └──────────────┘                         │                        │           │
│                                            │   ┌──────────────────┐ │           │
│   ┌──────────────┐                         │   │  Interactions    │ │           │
│   │    Minto     │                         │   │      API         │ │           │
│   │   Pyramid    │     Delegate            │   │  ─────────────   │ │           │
│   └──────────────┘ ──────────────────────► │   │ deep-research-   │ │           │
│                                            │   │ pro-preview-     │ │           │
│   ┌──────────────┐                         │   │ 12-2025          │ │           │
│   │    Domain    │                         │   └──────────────────┘ │           │
│   │   Analysis   │     Parallel            │                        │           │
│   └──────────────┘ ──────────────────────► │   ┌──────────────────┐ │           │
│                                            │   │   Background     │ │           │
│   ┌──────────────┐                         │   │   Execution      │ │           │
│   │    CSIO      │ ◄─────────────────────  │   │   + Polling      │ │           │
│   │              │     HandoffResult       │   └──────────────────┘ │           │
│   └──────────────┘                         └────────────────────────┘           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Google Deep Research API Summary

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Model** | `deep-research-pro-preview-12-2025` (Gemini 3 Pro backbone) |
| **Execution** | Async background mode (required) |
| **Max Duration** | 60 minutes (most complete in ~20 min) |
| **Built-in Tools** | Google Search, URL Context, File Search |
| **Pricing** | $2/1M input tokens (search free until Jan 2026) |
| **Output** | Detailed reports with citations |

### API Endpoint

```
POST https://generativelanguage.googleapis.com/v1beta/interactions
GET  https://generativelanguage.googleapis.com/v1beta/interactions/{ID}
```

### Request Structure

```python
{
    "input": "Research query...",
    "agent": "deep-research-pro-preview-12-2025",
    "background": True,  # REQUIRED - async execution
    "stream": True,      # Optional - real-time updates
    "agent_config": {
        "thinking_summaries": "auto"  # Get reasoning traces
    }
}
```

---

## Integration Architecture

### 1. New Agent: `GeminiDeepResearchAgent`

```
mindrian/agents/research/
├── __init__.py
├── beautiful_question.py
├── csio.py
├── domain_analysis.py
└── gemini_deep_research.py   # NEW
```

### 2. Handoff Protocol Mapping

The integration maps Mindrian's handoff protocol to Google's Interactions API:

| Mindrian Concept | Interactions API Equivalent |
|------------------|------------------------------|
| `HandoffContext` | `input` (research prompt) |
| `handoff_id` | `interaction_id` |
| `task_description` | Part of `input` |
| `previous_analyses` | Context in `input` |
| `HandoffResult.output` | `interaction.outputs[-1].text` |
| `HandoffResult.success` | `interaction.status == "completed"` |
| `HandoffResult.error` | `interaction.error` |
| Async polling | `background=True` + status checks |

### 3. Key Design Decisions

#### 3.1 Background Execution with Handoff Timeout

```python
@dataclass
class HandoffContext:
    timeout_seconds: int = 300  # Default 5 min

# Deep Research can take 20+ minutes
# Override timeout for this agent type
deep_research_timeout: int = 1800  # 30 minutes
```

#### 3.2 Progress Tracking via Streaming

```python
# Enable thinking_summaries to track progress
agent_config = {
    "thinking_summaries": "auto"
}

# Map to HandoffResult metadata
HandoffResult.metadata = {
    "thinking_steps": [...],
    "sources_consulted": [...],
    "search_queries_executed": [...]
}
```

#### 3.3 Handoff Chaining

```
Larry → GeminiDeepResearch → CSIO
         │
         │ Returns:
         │ - Full research report
         │ - Key findings (extracted)
         │ - Sources with citations
         │ - Confidence scores
         │
         ▼
    HandoffResult.to_analysis() → PreviousAnalysis
```

---

## Implementation

### `gemini_deep_research.py`

```python
"""
Gemini Deep Research Agent

Integrates Google's Deep Research API with Mindrian's handoff protocol.
Provides autonomous, multi-step research with citations.

Key Features:
- Background execution (async polling)
- Automatic source citation
- Progress tracking via thinking summaries
- Handoff protocol compliance
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from google import genai

from ...config import settings
from ...handoff.context import HandoffContext, HandoffResult, PreviousAnalysis
from ...handoff.types import HandoffType


@dataclass
class DeepResearchConfig:
    """Configuration for Deep Research agent"""
    max_wait_seconds: int = 1800  # 30 minutes max
    poll_interval_seconds: int = 10
    enable_thinking_summaries: bool = True
    include_sources: bool = True


class GeminiDeepResearchAgent:
    """
    Gemini Deep Research Agent with Mindrian handoff protocol.

    Uses Google's Interactions API for autonomous multi-step research.

    Usage:
        agent = GeminiDeepResearchAgent()

        # Direct use
        result = await agent.research("What are the latest trends in quantum computing?")

        # With handoff context (from orchestrator)
        result = await agent.process_handoff(handoff_context)
    """

    AGENT_ID = "gemini-deep-research"
    AGENT_NAME = "Gemini Deep Research"

    def __init__(
        self,
        config: Optional[DeepResearchConfig] = None,
    ):
        self._config = config or DeepResearchConfig()
        self._client = genai.Client(api_key=settings.llm.google_api_key)

    async def research(
        self,
        query: str,
        context: str = "",
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute deep research on a topic.

        Args:
            query: The research question
            context: Additional context from previous analyses
            focus_areas: Specific areas to investigate

        Returns:
            Dict with research results, sources, and metadata
        """
        # Build the research prompt
        prompt = self._build_research_prompt(query, context, focus_areas)

        # Create interaction (background mode)
        interaction = self._client.interactions.create(
            input=prompt,
            agent="deep-research-pro-preview-12-2025",
            background=True,
            agent_config={
                "thinking_summaries": "auto" if self._config.enable_thinking_summaries else "disabled"
            }
        )

        interaction_id = interaction.id
        start_time = time.time()
        thinking_steps = []

        # Poll for completion
        while True:
            elapsed = time.time() - start_time
            if elapsed > self._config.max_wait_seconds:
                return {
                    "success": False,
                    "error": f"Research timeout after {elapsed:.0f}s",
                    "partial_output": thinking_steps,
                }

            interaction = self._client.interactions.get(interaction_id)

            # Capture thinking steps
            if hasattr(interaction, 'thinking') and interaction.thinking:
                thinking_steps = interaction.thinking

            if interaction.status == "completed":
                return {
                    "success": True,
                    "output": interaction.outputs[-1].text,
                    "thinking_steps": thinking_steps,
                    "duration_seconds": elapsed,
                    "interaction_id": interaction_id,
                }
            elif interaction.status == "failed":
                return {
                    "success": False,
                    "error": interaction.error,
                    "thinking_steps": thinking_steps,
                    "duration_seconds": elapsed,
                }

            await asyncio.sleep(self._config.poll_interval_seconds)

    async def process_handoff(self, context: HandoffContext) -> HandoffResult:
        """
        Process a handoff from the Mindrian orchestrator.

        Converts HandoffContext to research query, executes research,
        and returns HandoffResult compatible with the protocol.
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
            focus_areas=context.focus_areas,
        )

        if result["success"]:
            # Extract key findings from output
            key_findings = self._extract_key_findings(result["output"])

            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent=self.AGENT_ID,
                to_agent=context.return_to,
                success=True,
                output=result["output"],
                output_format="markdown",
                key_findings=key_findings,
                recommendations=self._extract_recommendations(result["output"]),
                confidence=0.85,  # Deep Research is high-confidence
                suggested_next_agents=["csio", "domain-analysis", "minto-pyramid"],
                duration_seconds=result["duration_seconds"],
                metadata={
                    "thinking_steps": result.get("thinking_steps", []),
                    "interaction_id": result.get("interaction_id"),
                    "research_type": "gemini-deep-research",
                }
            )
        else:
            return HandoffResult(
                handoff_id=context.handoff_id,
                from_agent=self.AGENT_ID,
                to_agent=context.return_to,
                success=False,
                error=result.get("error", "Unknown error"),
                duration_seconds=time.time() - start_time,
                metadata={
                    "partial_thinking": result.get("thinking_steps", []),
                }
            )

    def _build_research_prompt(
        self,
        query: str,
        context: str,
        focus_areas: Optional[List[str]],
    ) -> str:
        """Build the research prompt for the API"""
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

Please provide:
1. **Executive Summary** - Key findings in 2-3 sentences
2. **Detailed Findings** - Comprehensive analysis with citations
3. **Data & Statistics** - Relevant numbers and trends
4. **Key Players** - Companies, researchers, or organizations involved
5. **Recent Developments** - Latest news and announcements (within 6 months)
6. **Recommendations** - Actionable next steps based on findings
7. **Confidence Assessment** - What's well-supported vs needs more research

Use proper citations for all claims. Include URLs where available.
""")

        return "\n".join(prompt_parts)

    def _handoff_to_query(self, context: HandoffContext) -> str:
        """Convert HandoffContext to research query"""
        parts = []

        # Main task
        parts.append(context.task_description)

        # Problem clarity
        if context.problem_clarity.what:
            parts.append(f"\nProblem: {context.problem_clarity.what}")
        if context.problem_clarity.who:
            parts.append(f"Target audience: {context.problem_clarity.who}")
        if context.problem_clarity.success:
            parts.append(f"Success criteria: {context.problem_clarity.success}")

        return "\n".join(parts)

    def _build_analysis_context(self, analyses: List[PreviousAnalysis]) -> str:
        """Build context string from previous analyses"""
        if not analyses:
            return ""

        parts = []
        for analysis in analyses[-3:]:  # Last 3 analyses to keep context manageable
            parts.append(f"### {analysis.framework_name}")
            if analysis.key_findings:
                parts.append("Key findings:")
                parts.extend([f"- {f}" for f in analysis.key_findings[:5]])
            parts.append("")

        return "\n".join(parts)

    def _extract_key_findings(self, output: str) -> List[str]:
        """Extract key findings from research output"""
        # Simple extraction - in production, could use LLM for structured extraction
        findings = []

        # Look for bullet points in Executive Summary section
        lines = output.split("\n")
        in_summary = False

        for line in lines:
            if "Executive Summary" in line or "Key Findings" in line:
                in_summary = True
                continue
            if in_summary:
                if line.startswith("##"):  # New section
                    break
                if line.strip().startswith("- ") or line.strip().startswith("* "):
                    findings.append(line.strip()[2:])
                elif line.strip().startswith("1.") or line.strip().startswith("2."):
                    findings.append(line.strip()[3:])

        return findings[:5]  # Top 5 findings

    def _extract_recommendations(self, output: str) -> List[str]:
        """Extract recommendations from research output"""
        recommendations = []
        lines = output.split("\n")
        in_recommendations = False

        for line in lines:
            if "Recommendation" in line:
                in_recommendations = True
                continue
            if in_recommendations:
                if line.startswith("##"):
                    break
                if line.strip().startswith("- ") or line.strip().startswith("* "):
                    recommendations.append(line.strip()[2:])

        return recommendations[:3]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def deep_research(
    query: str,
    context: Optional[str] = None,
    timeout_seconds: int = 1800,
) -> HandoffResult:
    """
    Convenience function for quick deep research.

    Usage:
        result = await deep_research("What are the latest AI agent frameworks?")
        print(result.output)
    """
    import uuid

    agent = GeminiDeepResearchAgent(
        config=DeepResearchConfig(max_wait_seconds=timeout_seconds)
    )

    handoff_context = HandoffContext(
        handoff_id=str(uuid.uuid4())[:8],
        task_description=query,
        from_agent="user",
        to_agent="gemini-deep-research",
        return_to="user",
    )

    if context:
        handoff_context.metadata["additional_context"] = context

    return await agent.process_handoff(handoff_context)
```

---

## Integration with Deep Research Team

### Update `deep_research_team.py`

Add Gemini Deep Research as an optional step in the research pipeline:

```python
from ..agents.research.gemini_deep_research import GeminiDeepResearchAgent

@dataclass
class DeepResearchConfig:
    enable_tavily_research: bool = False
    enable_gemini_deep_research: bool = False  # NEW
    gemini_research_queries: List[str] = field(default_factory=list)
    max_research_results: int = 5
    # ... existing fields


class DeepResearchTeam:
    def __init__(self, ...):
        # ... existing code

        # NEW: Gemini Deep Research agent
        self._gemini_researcher = GeminiDeepResearchAgent()

    async def run(self, challenge: str, config: DeepResearchConfig) -> DeepResearchResult:
        # ... existing steps 1-4

        # =================================================================
        # STEP 2.6: Gemini Deep Research (Optional - High-Quality Research)
        # =================================================================
        if config.enable_gemini_deep_research:
            gemini_context = self._create_handoff_context(
                task=f"Conduct comprehensive research on: {result.problem_clarity.what}",
                to_agent="gemini-deep-research",
                problem_clarity=result.problem_clarity,
                previous_analyses=previous_analyses,
            )

            # Override timeout for long-running research
            gemini_context.timeout_seconds = 1800  # 30 minutes

            gemini_result = await self._gemini_researcher.process_handoff(gemini_context)
            handoff_count += 1

            if gemini_result.success:
                result.gemini_research_output = gemini_result.output
                previous_analyses.append(gemini_result.to_analysis())

                # Extract metadata for synthesis
                result.metadata["gemini_thinking_steps"] = gemini_result.metadata.get("thinking_steps", [])
            else:
                result.errors.append(f"Gemini Deep Research: {gemini_result.error}")

        # ... continue with existing steps
```

---

## Handoff Flow Examples

### Example 1: Larry → Gemini Deep Research → CSIO

```python
# Larry clarifies the problem
larry_result = await larry.process_handoff(initial_context)

# Handoff to Gemini Deep Research
research_context = HandoffContext.from_larry(
    problem_what=larry_result.key_findings[0],
    problem_who="B2B SaaS companies",
    problem_success="Reduce churn by 50%",
    task="Research market trends, competitor solutions, and academic studies on this problem",
    to_agent="gemini-deep-research",
)
research_context.timeout_seconds = 1800  # Allow 30 minutes

research_result = await gemini_researcher.process_handoff(research_context)

# Pass research to CSIO for cross-sectional opportunities
csio_context = HandoffContext(
    handoff_id="csio-after-research",
    problem_clarity=research_context.problem_clarity,
    previous_analyses=[research_result.to_analysis()],
    task_description="Find cross-sectional innovation opportunities based on the research",
    from_agent="gemini-deep-research",
    to_agent="csio",
    return_to="synthesizer",
)
```

### Example 2: Parallel Research with Handoff Mode

```python
from ..handoff.types import HandoffMode

# Create parallel research handoffs
research_handoffs = [
    HandoffContext(
        handoff_id="market-research",
        task_description="Research market size and growth trends",
        to_agent="gemini-deep-research",
        # ...
    ),
    HandoffContext(
        handoff_id="competitor-research",
        task_description="Research competitor solutions and their approaches",
        to_agent="gemini-deep-research",
        # ...
    ),
    HandoffContext(
        handoff_id="academic-research",
        task_description="Research academic papers and scientific studies",
        to_agent="gemini-deep-research",
        # ...
    ),
]

# Execute in parallel
results = await asyncio.gather(*[
    gemini_researcher.process_handoff(ctx) for ctx in research_handoffs
])

# Merge results
combined_analysis = PreviousAnalysis(
    framework_id="gemini-deep-research-combined",
    framework_name="Combined Deep Research",
    output="\n\n---\n\n".join([r.output for r in results if r.success]),
    key_findings=[f for r in results if r.success for f in r.key_findings],
)
```

---

## Configuration

### Environment Variables

```bash
# .env
# Google API (already configured for Gemini)
GOOGLE_API_KEY=AIza...

# Deep Research specific settings (optional)
DEEP_RESEARCH_MAX_WAIT_SECONDS=1800
DEEP_RESEARCH_POLL_INTERVAL=10
DEEP_RESEARCH_ENABLE_THINKING=true
```

### Settings Update (`settings.py`)

```python
class LLMConfig(BaseSettings):
    # ... existing fields

    # Deep Research configuration
    deep_research_max_wait: int = Field(
        default=1800,
        alias="DEEP_RESEARCH_MAX_WAIT_SECONDS"
    )
    deep_research_poll_interval: int = Field(
        default=10,
        alias="DEEP_RESEARCH_POLL_INTERVAL"
    )
```

---

## Comparison: Tavily vs Gemini Deep Research

| Aspect | Tavily | Gemini Deep Research |
|--------|--------|----------------------|
| **Speed** | Fast (seconds) | Slow (minutes to ~20 min) |
| **Depth** | Surface-level search | Multi-step autonomous research |
| **Citations** | Basic URLs | Rich citations with context |
| **Cost** | Per search | $2/1M tokens (search free until 2026) |
| **Best For** | Quick fact-checking, current news | Comprehensive analysis, due diligence |
| **Handoff Fit** | Inline enhancement | Dedicated research step |

### Recommended Usage

- **Use Tavily** for: Quick validation, news checks, simple data points
- **Use Gemini Deep Research** for: Market analysis, competitive intelligence, academic research, complex multi-faceted questions

---

## Future Considerations

### 1. MCP Support (Coming Soon)

Google has announced MCP support for Deep Research. When available:

```python
# Future: Deep Research with MCP tools
interaction = client.interactions.create(
    agent="deep-research-pro-preview-12-2025",
    tools=[
        {"type": "mcp", "server": "neo4j"},  # Access Neo4j knowledge graph
        {"type": "mcp", "server": "supabase"},  # Access Supabase data
    ],
    input="Research using both web and our internal knowledge...",
)
```

### 2. File Search for Internal Knowledge

```python
# Use File Search to include internal documents
interaction = client.interactions.create(
    agent="deep-research-pro-preview-12-2025",
    tools=[
        {"type": "file_search", "corpus_id": "mindrian-knowledge-base"}
    ],
    input="Research this topic using our internal documents...",
)
```

### 3. Vertex AI Enterprise Integration

When available on Vertex AI, add enterprise features:
- Private data access
- Compliance controls
- Enhanced audit logging

---

## Sources

- [Gemini Deep Research Agent Documentation](https://ai.google.dev/gemini-api/docs/deep-research)
- [Build with Gemini Deep Research](https://blog.google/technology/developers/deep-research-agent-gemini-api/)
- [Google AI Studio's Interactions API](https://blog.google/technology/developers/interactions-api/)
- [Building agents with the ADK and Interactions API](https://developers.googleblog.com/building-agents-with-the-adk-and-the-new-interactions-api/)

---

*Mindrian Gemini Deep Research Integration v1.0*
