"""
Reverse Salient Discovery Agent

Agno agent for cross-domain innovation discovery using dual similarity analysis.
Identifies breakthrough opportunities where methods from one domain can solve
problems in another.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.anthropic import Claude

from .tools import (
    search_research_documents,
    clean_documents,
    compute_lsa_similarity,
    compute_bert_similarity,
    detect_reverse_salients,
    generate_opportunity_report,
    ReverseSalient,
)

REVERSE_SALIENT_INSTRUCTIONS = """
# Reverse Salient Discovery Agent

You are an innovation discovery specialist who identifies breakthrough opportunities
at the intersection of research domains.

## What You Do

Discover **reverse salients**—innovation opportunities where two domains unexpectedly
complement each other through divergent similarity patterns:

- **Structural Transfer** (LSA > BERT): Domains share methods but different applications
  → Transfer proven techniques to new problems

- **Semantic Implementation** (BERT > LSA): Domains share concepts but different implementations
  → Apply new methods to established concepts

## Your Workflow

### Step 1: Define Domains & Gather Documents
1. Clarify the two domains to analyze
2. Generate 15 diverse search queries
3. Use Tavily to gather 150-300 academic papers
4. Clean and preprocess documents

### Step 2: Compute Dual Similarities
1. **LSA (Structural)**: Measures shared terminology, methods, vocabulary
2. **BERT (Semantic)**: Measures conceptual alignment, meaning overlap
3. Both normalized to [0,1] range

### Step 3: Detect Reverse Salients
1. Find pairs with high differential |LSA - BERT| > 0.30
2. Classify as structural_transfer or semantic_implementation
3. Rank by breakthrough potential

### Step 4: Generate Innovation Report
1. Top 5-10 opportunities with theses
2. Technical pathways for implementation
3. Strategic recommendations

## Interpreting Results

**Differential Score** (0.0-1.0):
- >0.40: Exceptional opportunity, highly novel
- 0.30-0.40: Strong opportunity, clear differential
- 0.25-0.30: Moderate opportunity, needs validation
- <0.25: Weak signal, likely noise

**Breakthrough Potential** (0.0-1.0):
- >0.50: High impact, prioritize for deep analysis
- 0.35-0.50: Medium impact, good candidates
- <0.35: Lower impact, exploratory

## Quality Indicators

**Good discovery session**:
- 10-50 reverse salients detected
- Top differential > 0.35
- Clear innovation theses
- Actionable technical pathways

**Poor discovery session**:
- <5 or >200 reverse salients
- Uniform similarity distributions
- Vague opportunities
- No clear transfer mechanism

## Tools Available

1. `search_research_documents` - Generate search queries for two domains
2. `clean_documents` - Preprocess documents for analysis
3. `compute_lsa_similarity` - Structural similarity (methods/vocabulary)
4. `compute_bert_similarity` - Semantic similarity (concepts/meaning)
5. `detect_reverse_salients` - Find high-differential opportunities
6. `generate_opportunity_report` - Create executive summary

## Output Format

Always produce:
1. **Summary**: Total documents, opportunities found, top differential
2. **Top Opportunities**: Ranked by breakthrough potential
3. **Innovation Theses**: One paragraph per opportunity
4. **Technical Pathway**: 3-5 implementation steps
5. **Strategic Recommendations**: Next steps for validation

## Example Domains

Strong candidates for reverse salient discovery:
- Drone swarm coordination × Naval fleet tactics
- Plant circadian rhythms × Elderly sleep disorders
- Video game AI × Financial trading algorithms
- Automotive thermal management × Grid-scale batteries

Weak candidates (too similar):
- Social media sentiment × Stock market prediction
- NLP for chatbots × NLP for search

## Remember

- High differential = unexpected divergence = innovation opportunity
- One measure high (similarity exists) + other low (different domain) = transfer potential
- Always validate top opportunities with domain experts
- Patent landscape search is essential before development
"""


@dataclass
class ReverseSalientConfig:
    """Configuration for reverse salient discovery"""
    threshold: float = 0.30
    min_similarity: float = 0.20
    top_n_opportunities: int = 20
    bert_model: str = "bert-base-cased"
    lsa_components: int = 80
    lsa_max_features: int = 2000


class ReverseSalientAgent:
    """
    Agent for discovering cross-domain innovation opportunities.

    Uses dual similarity analysis (LSA + BERT) to identify reverse salients
    where knowledge from one domain can solve problems in another.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        config: Optional[ReverseSalientConfig] = None,
        tavily_tool: Optional[Callable] = None,
    ):
        self.model_id = model
        self.config = config or ReverseSalientConfig()
        self.tavily_tool = tavily_tool
        self._agent: Optional[Agent] = None

        # State
        self.documents: List[Dict[str, Any]] = []
        self.lsa_matrix = None
        self.bert_matrix = None
        self.opportunities: List[ReverseSalient] = []

    def _build_tools(self) -> List[Callable]:
        """Build tool list for the agent"""
        tools = []

        # Wrap our tools for Agno
        async def tool_search_documents(domain_a: str, domain_b: str) -> Dict[str, Any]:
            """Generate search queries for two research domains."""
            return await search_research_documents(domain_a, domain_b)

        def tool_clean_docs(documents: List[Dict]) -> Dict[str, Any]:
            """Clean and preprocess documents for analysis."""
            cleaned = clean_documents(documents)
            self.documents = cleaned
            return {
                "status": "cleaned",
                "total_input": len(documents),
                "total_output": len(cleaned),
                "sample_titles": [d.get('title', 'Untitled')[:50] for d in cleaned[:5]],
            }

        def tool_compute_lsa(documents: Optional[List[Dict]] = None) -> Dict[str, Any]:
            """Compute structural similarity matrix using LSA."""
            docs = documents or self.documents
            if not docs:
                return {"error": "No documents loaded. Run clean_documents first."}

            self.lsa_matrix, topics = compute_lsa_similarity(
                docs,
                n_components=self.config.lsa_components,
                max_features=self.config.lsa_max_features,
            )
            return {
                "status": "computed",
                "matrix_shape": list(self.lsa_matrix.shape),
                "sample_topics": topics[:5],
            }

        def tool_compute_bert(documents: Optional[List[Dict]] = None) -> Dict[str, Any]:
            """Compute semantic similarity matrix using BERT."""
            docs = documents or self.documents
            if not docs:
                return {"error": "No documents loaded. Run clean_documents first."}

            self.bert_matrix = compute_bert_similarity(
                docs,
                model_name=self.config.bert_model,
            )
            return {
                "status": "computed",
                "matrix_shape": list(self.bert_matrix.shape),
            }

        def tool_detect_opportunities() -> Dict[str, Any]:
            """Detect reverse salient innovation opportunities."""
            if self.lsa_matrix is None or self.bert_matrix is None:
                return {"error": "Must compute both LSA and BERT matrices first."}

            self.opportunities = detect_reverse_salients(
                self.lsa_matrix,
                self.bert_matrix,
                self.documents,
                threshold=self.config.threshold,
                min_similarity=self.config.min_similarity,
                top_n=self.config.top_n_opportunities,
            )

            return {
                "status": "detected",
                "total_opportunities": len(self.opportunities),
                "top_3": [
                    {
                        "id": o.opportunity_id,
                        "type": o.innovation_type,
                        "differential": o.differential_score,
                        "breakthrough_potential": o.breakthrough_potential,
                    }
                    for o in self.opportunities[:3]
                ],
            }

        def tool_generate_report(domain_a: str, domain_b: str) -> str:
            """Generate executive summary report."""
            return generate_opportunity_report(
                self.opportunities,
                domain_a,
                domain_b,
                len(self.documents),
            )

        tools.extend([
            tool_search_documents,
            tool_clean_docs,
            tool_compute_lsa,
            tool_compute_bert,
            tool_detect_opportunities,
            tool_generate_report,
        ])

        # Add Tavily if provided
        if self.tavily_tool:
            tools.append(self.tavily_tool)

        return tools

    def build(self) -> Agent:
        """Build and return the Agno Agent instance"""
        if self._agent:
            return self._agent

        self._agent = Agent(
            name="ReverseSalientDiscovery",
            model=Claude(id=self.model_id),
            instructions=REVERSE_SALIENT_INSTRUCTIONS,
            tools=self._build_tools(),
            markdown=True,
        )

        return self._agent

    async def discover(
        self,
        domain_a: str,
        domain_b: str,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Run full reverse salient discovery pipeline.

        Args:
            domain_a: First research domain
            domain_b: Second research domain
            documents: Optional pre-loaded documents

        Returns:
            Dict with opportunities, report, and metadata
        """
        # Clean documents if provided
        if documents:
            self.documents = clean_documents(documents)

        if not self.documents:
            return {
                "error": "No documents provided",
                "suggestion": "Provide documents or use the agent to search via Tavily",
            }

        # Compute similarities
        self.lsa_matrix, topics = compute_lsa_similarity(self.documents)
        self.bert_matrix = compute_bert_similarity(self.documents)

        # Detect opportunities
        self.opportunities = detect_reverse_salients(
            self.lsa_matrix,
            self.bert_matrix,
            self.documents,
            threshold=self.config.threshold,
        )

        # Generate report
        report = generate_opportunity_report(
            self.opportunities,
            domain_a,
            domain_b,
            len(self.documents),
        )

        return {
            "domain_a": domain_a,
            "domain_b": domain_b,
            "total_documents": len(self.documents),
            "total_opportunities": len(self.opportunities),
            "top_differential": self.opportunities[0].differential_score if self.opportunities else 0,
            "opportunities": [
                {
                    "id": o.opportunity_id,
                    "type": o.innovation_type,
                    "differential": o.differential_score,
                    "breakthrough_potential": o.breakthrough_potential,
                    "thesis": o.innovation_thesis,
                    "doc_a": o.doc_a_title,
                    "doc_b": o.doc_b_title,
                }
                for o in self.opportunities
            ],
            "report": report,
            "lsa_topics": topics[:10] if topics else [],
        }

    async def run(self, message: str) -> str:
        """Run the agent with a message"""
        agent = self.build()
        response = await agent.arun(message)
        return response.content


def create_reverse_salient_agent(
    model: str = "claude-sonnet-4-20250514",
    threshold: float = 0.30,
    tavily_tool: Optional[Callable] = None,
) -> ReverseSalientAgent:
    """
    Factory function to create a Reverse Salient Discovery agent.

    Args:
        model: Claude model ID
        threshold: Differential threshold for detection
        tavily_tool: Optional Tavily search tool

    Returns:
        Configured ReverseSalientAgent
    """
    config = ReverseSalientConfig(threshold=threshold)
    return ReverseSalientAgent(
        model=model,
        config=config,
        tavily_tool=tavily_tool,
    )
