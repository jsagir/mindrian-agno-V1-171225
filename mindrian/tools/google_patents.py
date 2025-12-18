"""
Google Patents Tools - Patent search and IP analysis

Uses SerpAPI to search Google Patents for relevant prior art,
existing patents, and IP landscape analysis.

Features:
- Search patents by keywords
- Filter by inventor, assignee, country
- Date range filtering
- Context-aware patent relevance checking
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PatentResult:
    """A patent search result"""
    patent_id: str
    title: str
    snippet: str
    inventor: Optional[str] = None
    assignee: Optional[str] = None
    publication_date: Optional[str] = None
    filing_date: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = 0.0


class GooglePatentsTools:
    """
    Google Patents search tools using SerpAPI.

    Provides patent search and IP landscape analysis for innovation validation.
    """

    SERPAPI_BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy load HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def search_patents(
        self,
        query: str,
        num_results: int = 10,
        inventor: Optional[str] = None,
        assignee: Optional[str] = None,
        country: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None,  # "GRANT" or "APPLICATION"
    ) -> List[PatentResult]:
        """
        Search Google Patents.

        Args:
            query: Search query (supports advanced syntax)
            num_results: Number of results (10-100)
            inventor: Filter by inventor name
            assignee: Filter by assignee/company
            country: Filter by country code (US, EP, WO, etc.)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            status: Patent status (GRANT or APPLICATION)

        Returns:
            List of PatentResult objects
        """
        if not self.api_key:
            return self._mock_search(query, num_results)

        # Build query with filters
        full_query = query
        if inventor:
            full_query += f" inventor:{inventor}"
        if assignee:
            full_query += f" assignee:{assignee}"
        if country:
            full_query += f" country:{country}"

        params = {
            "engine": "google_patents",
            "q": full_query,
            "api_key": self.api_key,
            "num": min(num_results, 100),
        }

        if status:
            params["status"] = status

        # Date filtering
        if date_from or date_to:
            if date_from and date_to:
                params["after"] = date_from
                params["before"] = date_to

        try:
            response = await self.client.get(self.SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic_results", []):
                results.append(PatentResult(
                    patent_id=item.get("patent_id", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    inventor=item.get("inventor"),
                    assignee=item.get("assignee"),
                    publication_date=item.get("publication_date"),
                    filing_date=item.get("filing_date"),
                    url=item.get("link"),
                ))

            return results

        except Exception as e:
            print(f"Patent search error: {e}")
            return self._mock_search(query, num_results)

    async def analyze_ip_landscape(
        self,
        problem_description: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Analyze the IP landscape for a problem/innovation.

        Searches for relevant patents and provides analysis.

        Args:
            problem_description: Description of the problem or innovation
            top_k: Number of top results to analyze

        Returns:
            Dict with patents, analysis, and recommendations
        """
        # Extract key terms for patent search
        keywords = self._extract_keywords(problem_description)
        query = " OR ".join(keywords[:5])  # Use top 5 keywords

        patents = await self.search_patents(query, num_results=top_k * 2)

        # Score relevance
        scored_patents = self._score_relevance(patents, problem_description)
        top_patents = sorted(scored_patents, key=lambda p: p.relevance_score, reverse=True)[:top_k]

        # Generate analysis
        analysis = {
            "query_keywords": keywords,
            "total_found": len(patents),
            "top_patents": [
                {
                    "id": p.patent_id,
                    "title": p.title,
                    "snippet": p.snippet,
                    "assignee": p.assignee,
                    "relevance": f"{p.relevance_score:.0%}",
                    "url": p.url,
                }
                for p in top_patents
            ],
            "ip_density": self._assess_ip_density(len(patents)),
            "recommendations": self._generate_recommendations(top_patents, problem_description),
        }

        return analysis

    async def check_prior_art(
        self,
        innovation_description: str,
        key_features: List[str],
    ) -> Dict[str, Any]:
        """
        Check for prior art related to an innovation.

        Args:
            innovation_description: Description of the innovation
            key_features: List of key differentiating features

        Returns:
            Prior art assessment with risk level
        """
        # Search for each key feature
        all_results = []
        for feature in key_features[:3]:  # Limit to 3 features
            results = await self.search_patents(
                f"{innovation_description} {feature}",
                num_results=5,
            )
            all_results.extend(results)

        # Deduplicate
        seen_ids = set()
        unique_results = []
        for r in all_results:
            if r.patent_id not in seen_ids:
                seen_ids.add(r.patent_id)
                unique_results.append(r)

        # Assess risk
        scored = self._score_relevance(unique_results, innovation_description)
        high_relevance = [p for p in scored if p.relevance_score > 0.7]

        risk_level = "low"
        if len(high_relevance) > 3:
            risk_level = "high"
        elif len(high_relevance) > 0:
            risk_level = "medium"

        return {
            "prior_art_found": len(unique_results),
            "high_relevance_count": len(high_relevance),
            "risk_level": risk_level,
            "key_patents": [
                {
                    "id": p.patent_id,
                    "title": p.title,
                    "relevance": f"{p.relevance_score:.0%}",
                }
                for p in high_relevance[:5]
            ],
            "recommendation": self._get_risk_recommendation(risk_level),
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for patent search"""
        # Simple keyword extraction (could be enhanced with NLP)
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "to", "of", "in", "for", "on", "with", "at",
            "by", "from", "as", "into", "through", "during", "before",
            "after", "above", "below", "between", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "each", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "just", "and", "but", "if", "or",
            "because", "until", "while", "about", "against", "this", "that",
        }

        words = text.lower().split()
        keywords = [
            w.strip(".,!?;:'\"()[]{}")
            for w in words
            if len(w) > 3 and w.lower() not in stop_words
        ]

        # Count frequency
        freq = {}
        for w in keywords:
            freq[w] = freq.get(w, 0) + 1

        # Sort by frequency
        sorted_keywords = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
        return sorted_keywords[:10]

    def _score_relevance(
        self,
        patents: List[PatentResult],
        reference_text: str,
    ) -> List[PatentResult]:
        """Score patent relevance to reference text"""
        ref_words = set(reference_text.lower().split())

        for patent in patents:
            patent_text = f"{patent.title} {patent.snippet}".lower()
            patent_words = set(patent_text.split())

            # Simple Jaccard similarity
            intersection = len(ref_words & patent_words)
            union = len(ref_words | patent_words)
            patent.relevance_score = intersection / union if union > 0 else 0

        return patents

    def _assess_ip_density(self, count: int) -> str:
        """Assess IP density in the space"""
        if count > 50:
            return "high - crowded patent landscape"
        elif count > 20:
            return "medium - some existing IP"
        elif count > 5:
            return "low - limited prior art"
        else:
            return "very low - potentially novel space"

    def _generate_recommendations(
        self,
        patents: List[PatentResult],
        problem: str,
    ) -> List[str]:
        """Generate IP strategy recommendations"""
        recommendations = []

        if len(patents) == 0:
            recommendations.append("Novel space - consider filing provisional patent")
        elif len(patents) < 3:
            recommendations.append("Limited prior art - good opportunity for differentiation")
        else:
            recommendations.append("Existing patents found - focus on differentiated claims")

        # Check for major assignees
        assignees = [p.assignee for p in patents if p.assignee]
        if assignees:
            top_assignee = max(set(assignees), key=assignees.count)
            recommendations.append(f"Key player in space: {top_assignee}")

        recommendations.append("Recommend professional IP counsel before filing")

        return recommendations

    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "low": "Low prior art risk. Consider filing a provisional patent to establish priority date.",
            "medium": "Some relevant prior art exists. Recommend detailed freedom-to-operate analysis before proceeding.",
            "high": "Significant prior art found. Consult patent attorney to assess infringement risk and design-around options.",
        }
        return recommendations.get(risk_level, "Consult IP professional for detailed analysis.")

    def _mock_search(self, query: str, num_results: int) -> List[PatentResult]:
        """Return mock results when API is unavailable"""
        return [
            PatentResult(
                patent_id="US20230001234A1",
                title=f"[Mock] System and method related to: {query[:50]}",
                snippet="This is a mock patent result. Configure SERPAPI_API_KEY for real results.",
                assignee="Mock Corp",
                publication_date="2023-01-01",
                relevance_score=0.5,
            )
        ]


# Convenience function
def get_patent_tools() -> GooglePatentsTools:
    """Get a configured Google Patents tools instance"""
    return GooglePatentsTools()
