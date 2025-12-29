"""
Ingest Reverse Salient Discovery methodology into PWS Brain (Pinecone)

This script adds the Reverse Salient discovery framework to the knowledge base
for RAG-enhanced innovation conversations.
"""

import os
import asyncio
import httpx
from typing import List, Dict, Any

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_HOST = "neo4j-knowledge-base-bc1849d.svc.aped-4627-b74a.pinecone.io"
NAMESPACE = "pws-materials"


REVERSE_SALIENT_CONTENT: List[Dict[str, Any]] = [
    # Core Concept
    {
        "id": "framework-reverse-salient-overview",
        "title": "Reverse Salient Discovery Framework - Overview",
        "category": "Framework",
        "type": "framework",
        "source": "reverse-salient-discovery-skill",
        "tags": "framework, reverse-salient, innovation, cross-domain, breakthrough",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Discovery Framework - Systematic cross-domain innovation discovery

PURPOSE:
Identify breakthrough innovation opportunities at the intersection of research domains
by detecting "reverse salients"—unexpected complementarities where structural and
semantic similarities diverge significantly.

WHAT IS A REVERSE SALIENT:
A reverse salient is an innovation opportunity that emerges when two research domains
exhibit divergent patterns between:
1. Structural Similarity (LSA) - Shared terminology, methods, technical approaches
2. Semantic Similarity (BERT) - Conceptual alignment and meaning overlap

The term comes from technology history, referring to components that lag behind.
In this framework, we identify where DIVERGENCE between structural and semantic
similarity indicates untapped innovation potential.

INNOVATION SIGNAL:
High differential |LSA - BERT| > 0.30 indicates transferable knowledge waiting
to be applied. One measure is high (similarity exists) while the other is low
(different domain), creating an asymmetry that signals opportunity.

WHEN TO USE:
- R&D strategy and technology roadmapping
- Cross-domain innovation scouting
- Technology transfer analysis between fields
- Research gap identification with commercial potential
- Competitive positioning across domain boundaries
- Generating novel product/service concepts from academic literature
"""
    },

    # Innovation Types
    {
        "id": "framework-reverse-salient-types",
        "title": "Reverse Salient - Innovation Types",
        "category": "Framework",
        "type": "framework",
        "source": "reverse-salient-discovery-skill",
        "tags": "framework, reverse-salient, structural-transfer, semantic-implementation",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Innovation Types

TWO TYPES OF REVERSE SALIENTS:

1. STRUCTURAL TRANSFER (LSA > BERT)
   Pattern: Domains share methods but serve different purposes

   Characteristics:
   - High structural similarity (shared technical vocabulary, methods)
   - Lower semantic similarity (different problem domains, applications)
   - Innovation opportunity: Transfer proven methods to new applications

   Example: Drone Swarm Algorithms → Naval Fleet Tactics
   - Shared methods: Distributed decision-making, coordination protocols
   - Different applications: Aerial vs maritime operations
   - Innovation: Apply lightweight swarm algorithms to heavy naval vessels

   Signal: "These domains use the same tools for different jobs"

2. SEMANTIC IMPLEMENTATION (BERT > LSA)
   Pattern: Domains share concepts but use different implementations

   Characteristics:
   - High semantic similarity (related concepts, problem types)
   - Lower structural similarity (different technical approaches)
   - Innovation opportunity: Implement established concepts with new techniques

   Example: Plant Circadian Rhythms → Elderly Sleep Disorders
   - Shared concepts: Biological timing mechanisms, environmental responsiveness
   - Different methods: Photoreceptor proteins vs wearable sensors
   - Innovation: Adapt plant timing mechanisms for human health applications

   Signal: "These domains solve the same problem with different tools"

HOW TO IDENTIFY:
- Structural Transfer: LSA similarity > BERT similarity
- Semantic Implementation: BERT similarity > LSA similarity
- Both require differential > 0.30 for confidence
"""
    },

    # Methodology Steps
    {
        "id": "framework-reverse-salient-methodology",
        "title": "Reverse Salient - Methodology Steps",
        "category": "Framework",
        "type": "framework",
        "source": "reverse-salient-discovery-skill",
        "tags": "framework, reverse-salient, methodology, process",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Discovery Methodology

8-STEP WORKFLOW:

STEP 1: DOCUMENT ACQUISITION (30-60 min)
- Define two domains with potential complementarity
- Generate 15 diverse queries:
  * 5 direct intersection queries
  * 5 A→B transfer queries
  * 5 B→A transfer queries
- Gather 150-300 academic papers via Tavily
- Sources: arxiv.org, nature.com, ieee.org, pubmed

STEP 2: DOCUMENT PROCESSING (15-20 min)
- Remove metadata and boilerplate
- Filter documents without abstracts
- Create cleaned_text (for BERT) and nostop_text (for LSA)

STEP 3: COMPUTE LSA SIMILARITY (10-20 min)
- TF-IDF vectorization (max 2000 features)
- SVD decomposition (80 latent topics)
- Pairwise L1 distance computation
- Measures: shared vocabulary, methods, terminology

STEP 4: COMPUTE BERT SIMILARITY (30-60 min GPU, 2-4h CPU)
- Contextual embeddings using BERT
- Segment-wise processing for long documents
- Pairwise cosine similarity
- Measures: conceptual alignment, meaning overlap

STEP 5: DETECT REVERSE SALIENTS (10-15 min)
- Compute differential = |BERT - LSA|
- Filter: differential > 0.30 AND both > 0.20
- Classify as structural_transfer or semantic_implementation
- Rank by breakthrough_potential = (novelty × 0.7) + (feasibility × 0.3)

STEP 6: GENERATE VISUALIZATIONS
- Similarity comparison matrix
- Top opportunities chart
- Opportunity landscape (novelty vs feasibility)

STEP 7: DEEP DIVE TOP OPPORTUNITIES
- Patent landscape search
- Existing implementation search
- Market analysis

STEP 8: GENERATE FINAL REPORT
- Executive summary
- Top 5-10 opportunities with theses
- Technical pathways
- Strategic recommendations
"""
    },

    # Scoring & Thresholds
    {
        "id": "framework-reverse-salient-scoring",
        "title": "Reverse Salient - Scoring and Thresholds",
        "category": "Framework",
        "type": "framework",
        "source": "reverse-salient-discovery-skill",
        "tags": "framework, reverse-salient, scoring, validation",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Scoring and Interpretation

DIFFERENTIAL SCORE (0.0-1.0):
- >0.40: Exceptional opportunity, highly novel
- 0.30-0.40: Strong opportunity, clear differential
- 0.25-0.30: Moderate opportunity, needs validation
- <0.25: Weak signal, likely noise

BREAKTHROUGH POTENTIAL (0.0-1.0):
Formula: breakthrough = (novelty × 0.7) + (feasibility × 0.3)
Where:
- novelty = differential_score
- feasibility = min(LSA_similarity, BERT_similarity)

Interpretation:
- >0.50: High impact, prioritize for deep analysis
- 0.35-0.50: Medium impact, good candidates
- 0.25-0.35: Lower impact, exploratory
- <0.25: Low priority

THRESHOLD SELECTION:
- 0.30: Standard (balanced discovery) - RECOMMENDED
- 0.35: Conservative (fewer, higher-confidence)
- 0.25: Exploratory (more opportunities, requires validation)

Dynamic threshold adjustment:
- Closely related domains: Use higher threshold (0.35+)
- Distant domains: Use lower threshold (0.25)

QUALITY INDICATORS:

Good discovery session:
- 10-50 reverse salients detected
- Top differential > 0.35
- LSA topics are coherent and domain-relevant
- Clear clustering in similarity matrices

Poor discovery session:
- <5 or >200 reverse salients
- Topics are random words
- Uniform similarity distributions
- Top opportunities are vague or obvious
"""
    },

    # Examples
    {
        "id": "framework-reverse-salient-examples",
        "title": "Reverse Salient - Real-World Examples",
        "category": "Case Study",
        "type": "case-study",
        "source": "reverse-salient-discovery-skill",
        "tags": "reverse-salient, examples, case-study, innovation",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Real-World Examples

EXAMPLE 1: STRUCTURAL TRANSFER
Domains: Drone Swarm Coordination × Naval Fleet Tactics
Documents: 180 papers
LSA: 0.65 (high - shared vocabulary)
BERT: 0.32 (low - different contexts)
Differential: 0.33 ✓

Innovation Thesis:
Apply lightweight swarm coordination protocols from drone operations to naval
fleet tactics, achieving 10x faster tactical response. The shared algorithmic
foundations can be adapted from aerial to maritime contexts.

Technical Pathway:
1. Adapt communication protocols for naval frequency bands
2. Adjust collision avoidance for vessel momentum/turning radius
3. Implement hierarchical coordination (vessel groups)
4. Test in simulated naval exercises

Market: Navy modernization ($2B+)

EXAMPLE 2: SEMANTIC IMPLEMENTATION
Domains: Plant Circadian Rhythms × Elderly Sleep Disorders
Documents: 145 papers
LSA: 0.28 (low - different vocabularies)
BERT: 0.61 (high - similar concepts)
Differential: 0.33 ✓

Innovation Thesis:
Implement plant photoreceptor principles in wearable devices for elderly care,
enabling non-pharmaceutical sleep regulation. The shared biological timing
concepts can be realized through novel sensor technologies.

Technical Pathway:
1. Miniaturize phytochrome-inspired optical sensors
2. Develop algorithms mapping plant responses to human circadian needs
3. Create wearable form factor with ambient light control
4. Clinical trials with elderly populations

Market: Elderly care ($400B+ globally)

UNSUCCESSFUL EXAMPLE (Learning Case):
Domains: Social Media Sentiment × Stock Market Prediction
LSA: 0.82 (very high)
BERT: 0.79 (very high)
Differential: 0.03 ✗

Why no opportunity: Domains are too similar, already heavily cross-pollinated
in research. Low differential indicates existing knowledge transfer.
"""
    },

    # Domain Selection
    {
        "id": "framework-reverse-salient-domains",
        "title": "Reverse Salient - Domain Selection Guide",
        "category": "Framework",
        "type": "framework",
        "source": "reverse-salient-discovery-skill",
        "tags": "framework, reverse-salient, domain-selection, strategy",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Domain Selection Guide

STRONG CANDIDATES FOR DISCOVERY:

Choose domains that:
- Have active research (>100 recent papers each)
- Share some concepts but different methods
- Are not already heavily cross-pollinated
- Have clear commercial applications

Good domain pairs:
- Drone swarm coordination × Naval fleet tactics
- Plant circadian rhythms × Elderly sleep disorders
- Video game AI × Financial trading algorithms
- Automotive thermal management × Grid-scale batteries
- Swarm robotics × Supply chain logistics
- Biomimicry × Architecture materials

WEAK CANDIDATES (Avoid):

Domains that are too similar:
- Social media sentiment × Stock market prediction (already connected)
- NLP for chatbots × NLP for search (same field)
- Machine learning × Deep learning (same domain)

Domains that are too distant:
- Medieval history × Quantum computing (no connection mechanism)
- Poetry analysis × Nuclear physics (implausible transfer)

QUERY STRATEGY:

Effective query patterns:
- "[domain A method] for [domain B problem]"
- "[domain B concept] using [domain A technique]"
- "cross-disciplinary [A] [B] applications"
- "[A] AND [B] research innovation"

Include variations:
- Technical terms and plain language
- Method names and problem descriptions
- Both domain-specific and general terms

VALIDATION CHECKLIST:

Before finalizing opportunities:
□ Domain experts find them novel and interesting
□ Patent search shows no existing implementations
□ Technical pathway is clear and feasible
□ Market need is identifiable
□ Value proposition exceeds current alternatives
"""
    },

    # Integration with PWS
    {
        "id": "framework-reverse-salient-pws-integration",
        "title": "Reverse Salient - Integration with PWS Methodology",
        "category": "Core Methodology",
        "type": "methodology",
        "source": "reverse-salient-discovery-skill",
        "tags": "reverse-salient, pws, integration, problem-worth-solving",
        "problem_type": "un-defined",
        "framework_name": "reverse-salient",
        "content": """
Reverse Salient Integration with PWS Methodology

WHERE IT FITS IN PWS:

Reverse Salient Discovery is a powerful tool for UNDEFINED PROBLEMS—
the 5-15 year horizon where we're searching for breakthrough opportunities
that don't yet have clear definitions.

PROBLEM CLASSIFICATION:
- Undefined Problems (5-15 years): Use Reverse Salient for discovery
- Ill-defined Problems (1-5 years): Use JTBD + Minto for structuring
- Well-defined Problems (0-12 months): Use Issue Trees for validation

WORKFLOW INTEGRATION:

1. DISCOVERY PHASE (Reverse Salient)
   - Scan across domain boundaries
   - Identify high-differential opportunities
   - Generate innovation theses

2. STRUCTURING PHASE (Minto + JTBD)
   - Apply SCQA to top opportunities
   - Map jobs-to-be-done in target domain
   - Identify unmet needs

3. VALIDATION PHASE (PWS Scorecard)
   - Score on 4 pillars:
     * Problem (market evidence)
     * Solution (technical feasibility)
     * Business Case (unit economics)
     * People (team capability)
   - GO/PIVOT/NO-GO decision

CHAINING WITH OTHER FRAMEWORKS:

Reverse Salient → Beautiful Question
- Use opportunities as prompts for "What if...?" questions

Reverse Salient → Scenario Analysis
- Map opportunities to 2x2 uncertainty matrices

Reverse Salient → Cynefin
- Classify opportunity complexity before pursuit

Reverse Salient → Trending to Absurd
- Extrapolate opportunities 10+ years forward

OUTPUT FORMAT:
Each validated reverse salient becomes a PWS Opportunity with:
- Innovation thesis
- Market size estimate
- Technical pathway
- Competitive moat analysis
- Team requirements
"""
    },
]


async def upsert_records(records: List[Dict[str, Any]], namespace: str = NAMESPACE):
    """Upsert records to Pinecone"""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not set")

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {
            "Api-Key": PINECONE_API_KEY,
            "Content-Type": "application/json",
        }

        url = f"https://{INDEX_HOST}/records/namespaces/{namespace}/upsert"

        # Prepare records
        pinecone_records = []
        for record in records:
            pinecone_records.append({
                "_id": record["id"],
                "content": record["content"].strip(),
                "title": record["title"],
                "category": record["category"],
                "type": record["type"],
                "source": record["source"],
                "tags": record.get("tags", ""),
                "problem_type": record.get("problem_type", "all"),
                "framework_name": record.get("framework_name", ""),
            })

        response = await client.post(
            url,
            headers=headers,
            json={"records": pinecone_records},
        )
        response.raise_for_status()

        print(f"Upserted {len(pinecone_records)} records to {namespace}")
        return len(pinecone_records)


async def main(dry_run: bool = True):
    """Main function"""
    print(f"Found {len(REVERSE_SALIENT_CONTENT)} content blocks")

    # Show summary
    categories = {}
    for r in REVERSE_SALIENT_CONTENT:
        cat = r["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    if dry_run:
        print("\n[DRY RUN] Would upsert the following records:")
        for r in REVERSE_SALIENT_CONTENT:
            print(f"  - {r['id']}: {r['title']}")
        print("\nRun with --upsert to actually upload to Pinecone")
    else:
        print(f"\nUpserting to Pinecone namespace: {NAMESPACE}")
        count = await upsert_records(REVERSE_SALIENT_CONTENT)
        print(f"\nSuccessfully upserted {count} records")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest Reverse Salient to PWS Brain")
    parser.add_argument("--upsert", action="store_true", help="Actually upsert to Pinecone")
    args = parser.parse_args()

    asyncio.run(main(dry_run=not args.upsert))
