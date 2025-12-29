"""
Mindrian AI Routes

Provides AI-powered endpoints for:
- Smart TextArea autocomplete
- Smart Paste opportunity extraction
- Text-to-Diagram conversion
- Chart insights generation
"""

import os
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

# Import Anthropic client
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

router = APIRouter()


# ----- Pydantic Models -----

class AutocompleteRequest(BaseModel):
    input: str
    role: str = "entrepreneur exploring a business opportunity"
    style: str = "larry"


class AutocompleteResponse(BaseModel):
    suggestion: str


class ExtractOpportunityRequest(BaseModel):
    text: str


class ExtractOpportunityResponse(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    target_audience: Optional[str] = None
    tags: List[str] = []
    priority: str = "medium"


class DiagramRequest(BaseModel):
    text: str
    type: str = "flowchart"  # "flowchart" or "mindmap"


class DiagramNode(BaseModel):
    id: str
    label: str
    type: str  # "start", "process", "decision", "end"


class DiagramConnection(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class DiagramResponse(BaseModel):
    nodes: List[DiagramNode]
    connections: List[DiagramConnection]
    mermaidCode: str


class ChartInsightsRequest(BaseModel):
    opportunities: List[Dict[str, Any]]


class ChartInsightsResponse(BaseModel):
    insights: List[str]


# ----- Helper Functions -----

def get_anthropic_client():
    """Get Anthropic client if available."""
    if not HAS_ANTHROPIC:
        return None
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def get_local_suggestion(input_text: str) -> str:
    """Generate local fallback suggestions (Larry-style problem clarification)."""
    lower_input = input_text.lower()

    if "i want to" in lower_input or "i need to" in lower_input:
        return " solve this problem because..."
    if "the problem is" in lower_input:
        return " and it affects..."
    if "my target" in lower_input or "my audience" in lower_input:
        return " who currently struggle with..."
    if "success would" in lower_input:
        return " look like achieving..."
    if "i think" in lower_input:
        return ", but I'm not sure about..."
    if "customers" in lower_input:
        return " are currently solving this by..."

    return ""


def extract_opportunity_local(text: str) -> ExtractOpportunityResponse:
    """Local extraction fallback."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    result = ExtractOpportunityResponse()

    # First non-empty line is likely the title
    if lines:
        result.title = lines[0][:100]

    # Look for common patterns
    for line in lines:
        lower = line.lower()
        if "problem:" in lower or "challenge:" in lower:
            result.problem_statement = line.split(":", 1)[-1].strip()
        if "target:" in lower or "audience:" in lower or "users:" in lower:
            result.target_audience = line.split(":", 1)[-1].strip()
        if "description:" in lower or "about:" in lower:
            result.description = line.split(":", 1)[-1].strip()

    # If no description, use remaining text
    if not result.description and len(lines) > 1:
        result.description = " ".join(lines[1:4])

    # Extract potential tags
    keywords = ["AI", "SaaS", "B2B", "B2C", "Mobile", "Web", "Health", "Finance", "Education"]
    result.tags = [kw for kw in keywords if kw.lower() in text.lower()]

    return result


def generate_local_diagram(text: str, diagram_type: str) -> DiagramResponse:
    """Generate a simple diagram locally."""
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 10]

    if diagram_type == "mindmap":
        nodes = [DiagramNode(id="center", label="Problem Space", type="start")]
        connections = []

        for i, sentence in enumerate(sentences[:5]):
            node_id = f"node_{i}"
            nodes.append(DiagramNode(
                id=node_id,
                label=sentence[:50],
                type="process"
            ))
            connections.append(DiagramConnection(source="center", target=node_id))

        mermaid = "mindmap\n  root((Problem Space))\n"
        for node in nodes[1:]:
            mermaid += f"    {node.label}\n"

        return DiagramResponse(nodes=nodes, connections=connections, mermaidCode=mermaid)
    else:
        # Flowchart
        nodes = [DiagramNode(id="start", label="Start", type="start")]
        connections = []

        prev_id = "start"
        for i, sentence in enumerate(sentences[:4]):
            node_id = f"step_{i}"
            nodes.append(DiagramNode(
                id=node_id,
                label=sentence[:40],
                type="process"
            ))
            connections.append(DiagramConnection(source=prev_id, target=node_id))
            prev_id = node_id

        nodes.append(DiagramNode(id="end", label="End", type="end"))
        connections.append(DiagramConnection(source=prev_id, target="end"))

        mermaid = "flowchart TD\n"
        for node in nodes:
            shape = f"(({node.label}))" if node.type in ["start", "end"] else f"[{node.label}]"
            mermaid += f"  {node.id}{shape}\n"
        for conn in connections:
            mermaid += f"  {conn.source} --> {conn.target}\n"

        return DiagramResponse(nodes=nodes, connections=connections, mermaidCode=mermaid)


def generate_local_insights(opportunities: List[Dict[str, Any]]) -> List[str]:
    """Generate insights locally."""
    if not opportunities:
        return ["No opportunities to analyze yet."]

    insights = []

    # Calculate averages
    scores = [o.get("csio_score", 0) for o in opportunities]
    avg_score = sum(scores) / len(scores) if scores else 0
    validated = len([o for o in opportunities if o.get("status") == "validated"])
    exploring = len([o for o in opportunities if o.get("status") == "exploring"])

    insights.append(
        f"Average CSIO score is {int(avg_score * 100)}% - "
        f"{'strong opportunities' if avg_score >= 0.7 else 'room for improvement'}"
    )

    if validated > 0:
        conversion = (validated / len(opportunities)) * 100
        insights.append(f"{validated} opportunities validated - {int(conversion)}% conversion rate")

    if exploring > validated:
        insights.append(f"{exploring} opportunities still exploring - consider deep dives to validate")

    # Find highest scoring
    if opportunities:
        highest = max(opportunities, key=lambda o: o.get("csio_score", 0))
        if highest.get("csio_score", 0) >= 0.8:
            insights.append(
                f'"{highest.get("name", "Top opportunity")}" shows highest potential '
                f'at {int(highest.get("csio_score", 0) * 100)}%'
            )

    return insights


# ----- API Endpoints -----

@router.post("/ai/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    """
    AI-powered autocomplete for chat input.
    Provides Larry-style suggestions to help users articulate their problems.
    """
    if len(request.input) < 10:
        return AutocompleteResponse(suggestion="")

    client = get_anthropic_client()

    if client:
        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": f"""You are helping a {request.role} complete their thought.
They've typed: "{request.input}"

Complete this sentence with a SHORT (5-15 words) suggestion that helps them articulate their problem or need more clearly. Focus on clarifying WHAT they want, WHO it's for, or HOW success looks.

Return ONLY the completion text, nothing else. Start with lowercase."""
                }]
            )
            suggestion = response.content[0].text.strip()
            return AutocompleteResponse(suggestion=suggestion)
        except Exception as e:
            print(f"Autocomplete AI error: {e}")

    # Fallback to local suggestions
    return AutocompleteResponse(suggestion=get_local_suggestion(request.input))


@router.post("/ai/extract-opportunity", response_model=ExtractOpportunityResponse)
async def extract_opportunity(request: ExtractOpportunityRequest):
    """
    Extract structured opportunity data from pasted text.
    Uses AI to identify title, problem, target audience, and tags.
    """
    if not request.text.strip():
        return ExtractOpportunityResponse()

    client = get_anthropic_client()

    if client:
        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Extract structured opportunity data from this text:

---
{request.text}
---

Return a JSON object with:
- title: A concise title (max 100 chars)
- description: Brief description (max 200 chars)
- problem_statement: The core problem being solved
- target_audience: Who this is for
- tags: Array of relevant tags (AI, SaaS, Health, Finance, Education, Mobile, B2B, B2C, etc.)
- priority: "low", "medium", or "high" based on urgency/importance indicators

Return ONLY valid JSON, nothing else."""
                }]
            )

            import json
            data = json.loads(response.content[0].text.strip())
            return ExtractOpportunityResponse(**data)
        except Exception as e:
            print(f"Extract opportunity AI error: {e}")

    # Fallback to local extraction
    return extract_opportunity_local(request.text)


@router.post("/ai/text-to-diagram", response_model=DiagramResponse)
async def text_to_diagram(request: DiagramRequest):
    """
    Convert problem description into a visual diagram.
    Supports flowcharts and mindmaps.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    client = get_anthropic_client()

    if client:
        try:
            diagram_type = "mind map" if request.type == "mindmap" else "flowchart"

            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": f"""Create a {diagram_type} from this problem description:

---
{request.text}
---

Return a JSON object with:
- nodes: Array of {{id: string, label: string (max 50 chars), type: "start"|"process"|"decision"|"end"}}
- connections: Array of {{source: string, target: string, label?: string}}
- mermaidCode: Valid Mermaid.js diagram code

For a mindmap, use a central node with branches.
For a flowchart, show logical flow from start to end.

Return ONLY valid JSON, nothing else."""
                }]
            )

            import json
            data = json.loads(response.content[0].text.strip())
            return DiagramResponse(**data)
        except Exception as e:
            print(f"Text to diagram AI error: {e}")

    # Fallback to local diagram generation
    return generate_local_diagram(request.text, request.type)


@router.post("/ai/chart-insights", response_model=ChartInsightsResponse)
async def chart_insights(request: ChartInsightsRequest):
    """
    Generate AI insights from opportunity data.
    Analyzes patterns, outliers, and provides recommendations.
    """
    if not request.opportunities:
        return ChartInsightsResponse(insights=["No opportunities to analyze yet."])

    client = get_anthropic_client()

    if client:
        try:
            # Prepare summary data
            summary = {
                "total": len(request.opportunities),
                "by_status": {},
                "by_priority": {},
                "avg_score": 0,
                "scores": []
            }

            for opp in request.opportunities:
                status = opp.get("status", "unknown")
                priority = opp.get("priority", "unknown")
                score = opp.get("csio_score", 0)

                summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
                summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1
                summary["scores"].append(score)

            if summary["scores"]:
                summary["avg_score"] = sum(summary["scores"]) / len(summary["scores"])

            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this opportunity portfolio:

{summary}

Provide 3-4 SHORT insights (max 20 words each) about:
1. Overall portfolio health
2. Notable patterns or outliers
3. Actionable recommendations

Return a JSON object with: {{"insights": ["insight1", "insight2", ...]}}

Return ONLY valid JSON, nothing else."""
                }]
            )

            import json
            data = json.loads(response.content[0].text.strip())
            return ChartInsightsResponse(insights=data.get("insights", []))
        except Exception as e:
            print(f"Chart insights AI error: {e}")

    # Fallback to local insights
    return ChartInsightsResponse(insights=generate_local_insights(request.opportunities))


# ----- Patent Search Models -----

class PatentSearchRequest(BaseModel):
    query: str
    num_results: int = 10
    inventor: Optional[str] = None
    assignee: Optional[str] = None
    country: Optional[str] = None


class PatentResult(BaseModel):
    patent_id: str
    title: str
    snippet: str
    inventor: Optional[str] = None
    assignee: Optional[str] = None
    publication_date: Optional[str] = None
    url: Optional[str] = None
    relevance: str = "0%"


class PatentSearchResponse(BaseModel):
    results: List[PatentResult]
    total_found: int


class IPLandscapeRequest(BaseModel):
    problem_description: str
    key_features: List[str] = []


class IPLandscapeResponse(BaseModel):
    query_keywords: List[str]
    total_found: int
    top_patents: List[Dict[str, Any]]
    ip_density: str
    recommendations: List[str]
    risk_level: Optional[str] = None


# ----- Patent Search Endpoints -----

# Import patent tools class (instantiated per-request for fresh env vars)
try:
    from mindrian.tools.google_patents import GooglePatentsTools
    HAS_PATENT_TOOLS = True
except ImportError:
    HAS_PATENT_TOOLS = False


def get_patent_tools():
    """Get a fresh patent tools instance with current env vars"""
    if not HAS_PATENT_TOOLS:
        return None
    return GooglePatentsTools()


@router.post("/ai/search-patents", response_model=PatentSearchResponse)
async def search_patents(request: PatentSearchRequest):
    """
    Search Google Patents for relevant prior art and IP.

    Uses SerpAPI to search the patent database.
    """
    patent_tools = get_patent_tools()
    if not patent_tools:
        raise HTTPException(status_code=503, detail="Patent search not available")

    try:
        results = await patent_tools.search_patents(
            query=request.query,
            num_results=request.num_results,
            inventor=request.inventor,
            assignee=request.assignee,
            country=request.country,
        )

        return PatentSearchResponse(
            results=[
                PatentResult(
                    patent_id=r.patent_id,
                    title=r.title,
                    snippet=r.snippet,
                    inventor=r.inventor,
                    assignee=r.assignee,
                    publication_date=r.publication_date,
                    url=r.url,
                    relevance=f"{r.relevance_score:.0%}",
                )
                for r in results
            ],
            total_found=len(results),
        )
    except Exception as e:
        print(f"Patent search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/ip-landscape", response_model=IPLandscapeResponse)
async def analyze_ip_landscape(request: IPLandscapeRequest):
    """
    Analyze the IP landscape for a problem/innovation.

    Searches for relevant patents and provides strategic analysis.
    """
    patent_tools = get_patent_tools()
    if not patent_tools:
        raise HTTPException(status_code=503, detail="Patent search not available")

    try:
        analysis = await patent_tools.analyze_ip_landscape(
            problem_description=request.problem_description,
            top_k=5,
        )

        # If key features provided, also check prior art
        if request.key_features:
            prior_art = await patent_tools.check_prior_art(
                innovation_description=request.problem_description,
                key_features=request.key_features,
            )
            analysis["risk_level"] = prior_art["risk_level"]
            analysis["recommendations"].insert(0, prior_art["recommendation"])

        return IPLandscapeResponse(**analysis)
    except Exception as e:
        print(f"IP landscape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----- PWS Brain Endpoints -----

class PWSSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    namespace: str = ""  # "" or "pws-materials"


class PWSChunkResult(BaseModel):
    id: str
    title: str
    content: str
    category: str
    score: float


class PWSSearchResponse(BaseModel):
    results: List[PWSChunkResult]
    total: int
    query: str


class PWSContextRequest(BaseModel):
    query: str
    top_k: int = 3


class PWSContextResponse(BaseModel):
    context: str
    chunks_used: int


# Import PWS Brain
try:
    from mindrian.tools.pws_brain_pinecone import PWSBrainPinecone
    HAS_PWS_BRAIN = True
except ImportError:
    HAS_PWS_BRAIN = False


@router.get("/ai/pws-brain/status")
async def pws_brain_status():
    """Get PWS Brain status and statistics."""
    if not HAS_PWS_BRAIN:
        return {"status": "not_available", "error": "PWS Brain module not found"}

    brain = PWSBrainPinecone()
    stats = await brain.get_stats()
    return stats


@router.post("/ai/pws-brain/search", response_model=PWSSearchResponse)
async def pws_brain_search(request: PWSSearchRequest):
    """
    Search the PWS knowledge base.

    This searches Larry's Personal Wisdom System for relevant
    frameworks, methodologies, and structured thinking approaches.
    """
    if not HAS_PWS_BRAIN:
        raise HTTPException(status_code=503, detail="PWS Brain not available")

    brain = PWSBrainPinecone()

    try:
        if request.namespace:
            results = await brain.search(
                request.query,
                top_k=request.top_k,
                namespace=request.namespace,
            )
        else:
            results = await brain.search_all_namespaces(
                request.query,
                top_k=request.top_k,
            )

        return PWSSearchResponse(
            results=[
                PWSChunkResult(
                    id=r.id,
                    title=r.title,
                    content=r.content,
                    category=r.category,
                    score=r.score,
                )
                for r in results
            ],
            total=len(results),
            query=request.query,
        )
    except Exception as e:
        print(f"PWS Brain search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/pws-brain/context", response_model=PWSContextResponse)
async def pws_brain_context(request: PWSContextRequest):
    """
    Get formatted PWS context for a query.

    Returns a formatted context block ready for LLM consumption.
    This is what Larry uses to enhance his responses with PWS knowledge.
    """
    if not HAS_PWS_BRAIN:
        raise HTTPException(status_code=503, detail="PWS Brain not available")

    brain = PWSBrainPinecone()

    try:
        context = await brain.get_pws_context(request.query, top_k=request.top_k)
        chunks_used = context.count("**[") if context else 0

        return PWSContextResponse(
            context=context,
            chunks_used=chunks_used,
        )
    except Exception as e:
        print(f"PWS Brain context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/pws-brain/framework/{framework_name}")
async def get_framework_info(framework_name: str):
    """Get specific framework information from PWS Brain."""
    if not HAS_PWS_BRAIN:
        raise HTTPException(status_code=503, detail="PWS Brain not available")

    brain = PWSBrainPinecone()

    try:
        chunk = await brain.get_framework_info(framework_name)
        if not chunk:
            raise HTTPException(status_code=404, detail=f"Framework '{framework_name}' not found")

        return {
            "id": chunk.id,
            "title": chunk.title,
            "content": chunk.content,
            "category": chunk.category,
            "score": chunk.score,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Framework info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/pws-brain/problem-guidance/{problem_type}")
async def get_problem_guidance(problem_type: str):
    """
    Get guidance for a specific problem type.

    Args:
        problem_type: One of "un-defined", "ill-defined", "well-defined"
    """
    if not HAS_PWS_BRAIN:
        raise HTTPException(status_code=503, detail="PWS Brain not available")

    valid_types = ["un-defined", "ill-defined", "well-defined"]
    if problem_type.lower() not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid problem type. Must be one of: {valid_types}"
        )

    brain = PWSBrainPinecone()

    try:
        guidance = await brain.get_problem_type_guidance(problem_type)
        return {
            "problem_type": problem_type,
            "guidance": guidance,
        }
    except Exception as e:
        print(f"Problem guidance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/check-context-patents")
async def check_context_patents(request: Dict[str, Any]):
    """
    Context-aware patent check.

    Analyzes conversation context to identify relevant IP and patents.
    Uses AI to extract key innovation aspects and search for prior art.
    """
    context = request.get("context", "")

    if not context:
        raise HTTPException(status_code=400, detail="Context is required")

    client = get_anthropic_client()

    # Use AI to extract innovation aspects
    innovation_aspects = {
        "problem": "",
        "solution_approach": "",
        "key_features": [],
        "technical_domain": "",
    }

    if client:
        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this conversation and extract key aspects for patent search:

---
{context}
---

Return a JSON object with:
- problem: The core problem being solved (1-2 sentences)
- solution_approach: The proposed solution approach (1-2 sentences)
- key_features: Array of 3-5 key differentiating features
- technical_domain: The technical field (e.g., "machine learning", "IoT", "healthcare")
- search_queries: Array of 2-3 patent search queries to find prior art

Return ONLY valid JSON, nothing else."""
                }]
            )

            import json
            innovation_aspects = json.loads(response.content[0].text.strip())
        except Exception as e:
            print(f"Context extraction error: {e}")

    # If patent tools available, search for prior art
    patent_results = []
    patent_tools = get_patent_tools()
    if patent_tools and innovation_aspects.get("search_queries"):
        for query in innovation_aspects["search_queries"][:2]:
            try:
                results = await patent_tools.search_patents(query, num_results=3)
                patent_results.extend([
                    {
                        "id": r.patent_id,
                        "title": r.title,
                        "snippet": r.snippet,
                        "relevance": f"{r.relevance_score:.0%}",
                    }
                    for r in results
                ])
            except Exception:
                pass

    return {
        "innovation_aspects": innovation_aspects,
        "related_patents": patent_results[:5],  # Top 5 unique
        "recommendation": (
            "Found potentially related patents - recommend detailed IP analysis"
            if patent_results
            else "No immediate prior art found - consider filing provisional patent"
        ),
    }
