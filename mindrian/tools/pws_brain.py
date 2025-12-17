"""
PWS Brain Tools - Personal Wisdom System retrieval

This is a wrapper around the existing LarryPWSBrain functionality,
integrated with the Mindrian MCP architecture.

The PWS Brain provides Larry's perspective - 1400+ chunks of
frameworks, methodologies, and structured thinking approaches.
"""

from typing import Dict, List, Optional, Any
import os


class PWSBrainTools:
    """
    Personal Wisdom System (PWS) knowledge retrieval.

    Uses Supabase pgvector for semantic search across Larry's
    curated knowledge base.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
    ):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")

        self._client = None
        self._gemini = None

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                print(f"Failed to initialize Supabase: {e}")
        return self._client

    @property
    def gemini(self):
        """Lazy load Gemini client for embeddings"""
        if self._gemini is None:
            try:
                from google import genai
                self._gemini = genai.Client(api_key=self.google_api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
        return self._gemini

    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            if not self.supabase:
                return {"status": "not_connected"}

            result = self.supabase.table('knowledge_base') \
                .select('*', count='exact') \
                .limit(0) \
                .execute()

            return {
                'total_chunks': result.count or 0,
                'embedding_model': 'text-embedding-004',
                'dimensions': 768,
                'status': 'connected'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant PWS knowledge for a query.

        Args:
            query: User's question or topic
            top_k: Number of results (default 5)
            threshold: Minimum similarity (0.0-1.0)

        Returns:
            List of relevant chunks with content, similarity
        """
        try:
            if not self.gemini or not self.supabase:
                return []

            # Generate embedding
            result = self.gemini.models.embed_content(
                model="models/text-embedding-004",
                contents=query
            )
            query_embedding = result.embeddings[0].values

            # Search Supabase
            response = self.supabase.rpc(
                'search_knowledge_base',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': top_k
                }
            ).execute()

            return [
                {
                    'content': r['content'],
                    'title': r.get('title') or 'PWS Knowledge',
                    'source': r.get('source') or 'Larry PWS',
                    'similarity': r['similarity']
                }
                for r in response.data
            ]
        except Exception as e:
            print(f"Error retrieving PWS context: {e}")
            return []

    async def get_pws_perspective(
        self,
        query: str,
        top_k: int = 3,
    ) -> str:
        """
        Get formatted PWS perspective for inclusion in prompts.

        Returns a formatted context block ready for LLM consumption.
        """
        chunks = await self.retrieve_context(query, top_k=top_k, threshold=0.4)

        if not chunks:
            return ""

        perspective = "## Larry's PWS Perspective\n"
        perspective += "*Relevant frameworks and methodologies from Personal Wisdom System:*\n\n"

        for i, chunk in enumerate(chunks, 1):
            perspective += f"### [{i}] {chunk['title']}\n"
            perspective += f"{chunk['content']}\n\n"

        return perspective

    async def enhance_prompt(
        self,
        user_query: str,
        base_prompt: str = "",
    ) -> str:
        """
        Enhance any prompt with PWS perspective.

        Use this to inject Larry's wisdom into agent conversations.
        """
        pws_context = await self.get_pws_perspective(user_query)

        if not pws_context:
            return base_prompt

        return f"""{base_prompt}

{pws_context}

---
*Use the PWS perspective above to inform your response, applying relevant frameworks and methodologies.*
"""


# Convenience function
def get_pws_brain() -> PWSBrainTools:
    """Get a configured PWS brain instance"""
    return PWSBrainTools()
