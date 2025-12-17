"""
Mindrian Configuration Settings
Central configuration for all services, MCPs, and agents

Environment Variables (.env):
- LLM: ANTHROPIC_API_KEY, GOOGLE_API_KEY, DEFAULT_LLM_PROVIDER
- Neo4j: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
- Supabase: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
- Embeddings: EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS
"""

from enum import Enum
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers"""
    GOOGLE = "google"
    OPENAI = "openai"


class LLMConfig(BaseSettings):
    """
    Multi-provider LLM configuration

    Supports Anthropic Claude (primary for complex reasoning)
    and Google Gemini (secondary for speed/cost optimization)
    """

    # Anthropic Claude
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_default_model: str = Field(
        default="claude-sonnet-4-20250514",
        alias="ANTHROPIC_DEFAULT_MODEL"
    )

    # Google Gemini
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_default_model: str = Field(
        default="gemini-2.0-flash-exp",
        alias="GOOGLE_DEFAULT_MODEL"
    )

    # Default provider selection
    default_provider: LLMProvider = Field(
        default=LLMProvider.ANTHROPIC,
        alias="DEFAULT_LLM_PROVIDER"
    )

    # Model mappings for different agent types
    model_routing: dict = Field(default_factory=lambda: {
        # Complex reasoning tasks → Claude
        "complex_reasoning": ("anthropic", "claude-sonnet-4-20250514"),
        "clarification": ("anthropic", "claude-sonnet-4-20250514"),
        "synthesis": ("anthropic", "claude-sonnet-4-20250514"),
        # Fast/simple tasks → Gemini
        "classification": ("google", "gemini-2.0-flash-exp"),
        "summarization": ("google", "gemini-2.0-flash-exp"),
        "extraction": ("google", "gemini-2.0-flash-exp"),
    })

    def get_model_for_task(self, task_type: str) -> tuple[str, str]:
        """Get (provider, model_id) for a task type"""
        if task_type in self.model_routing:
            return self.model_routing[task_type]
        # Default to configured provider
        if self.default_provider == LLMProvider.ANTHROPIC:
            return ("anthropic", self.anthropic_default_model)
        return ("google", self.google_default_model)

    class Config:
        env_file = ".env"
        extra = "ignore"


class Neo4jConfig(BaseSettings):
    """Neo4j Knowledge Graph configuration"""

    uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    user: str = Field(default="neo4j", alias="NEO4J_USER")
    password: str = Field(default="", alias="NEO4J_PASSWORD")

    # MCP enabled flag
    mcp_enabled: bool = Field(default=True, alias="MCP_NEO4J_ENABLED")

    class Config:
        env_file = ".env"
        extra = "ignore"


class SupabaseConfig(BaseSettings):
    """Supabase configuration for conversation memory + pgvector"""

    url: str = Field(default="", alias="SUPABASE_URL")
    anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")
    database_url: str = Field(default="", alias="DATABASE_URL")

    # MCP enabled flag
    mcp_enabled: bool = Field(default=True, alias="MCP_SUPABASE_ENABLED")

    class Config:
        env_file = ".env"
        extra = "ignore"


class EmbeddingConfig(BaseSettings):
    """Embedding configuration for vector search"""

    provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.GOOGLE,
        alias="EMBEDDING_PROVIDER"
    )
    model: str = Field(default="text-embedding-004", alias="EMBEDDING_MODEL")
    dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class ApplicationConfig(BaseSettings):
    """Application-level settings"""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")

    # API Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # Session
    session_timeout_minutes: int = Field(default=60, alias="SESSION_TIMEOUT_MINUTES")
    max_conversation_turns: int = Field(default=100, alias="MAX_CONVERSATION_TURNS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class PathConfig(BaseSettings):
    """Path configuration for skills and output"""

    skills_path: str = Field(
        default="/home/jsagi/Mindrian/mindrian-platform/skills",
        alias="SKILLS_PATH"
    )
    agents_output_path: str = Field(
        default="/home/jsagi/Mindrian/mindrian-agno/mindrian/agents",
        alias="AGENTS_OUTPUT_PATH"
    )
    agno_db_path: str = Field(default="tmp/mindrian.db", alias="AGNO_DB_PATH")

    class Config:
        env_file = ".env"
        extra = "ignore"


class MindrianSettings(BaseSettings):
    """
    Main Mindrian settings - aggregates all configurations

    Usage:
        from mindrian.config import settings

        # Get LLM for a task
        provider, model = settings.llm.get_model_for_task("complex_reasoning")

        # Check if Neo4j MCP is enabled
        if settings.neo4j.mcp_enabled:
            # Use Neo4j MCP tools
            pass
    """

    app_name: str = "Mindrian"
    version: str = "1.0.0"

    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    app: ApplicationConfig = Field(default_factory=ApplicationConfig)
    paths: PathConfig = Field(default_factory=PathConfig)

    @computed_field
    @property
    def mcp_servers_enabled(self) -> list[str]:
        """List of enabled MCP servers"""
        servers = []
        if self.neo4j.mcp_enabled:
            servers.append("neo4j")
        if self.supabase.mcp_enabled:
            servers.append("supabase")
        return servers

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = MindrianSettings()


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Engine Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_anthropic_client():
    """Get configured Anthropic client"""
    from anthropic import Anthropic
    return Anthropic(api_key=settings.llm.anthropic_api_key)


def get_google_client():
    """Get configured Google Generative AI client"""
    import google.generativeai as genai
    genai.configure(api_key=settings.llm.google_api_key)
    return genai


def get_embedding_model():
    """Get configured embedding model based on provider"""
    if settings.embedding.provider == EmbeddingProvider.GOOGLE:
        import google.generativeai as genai
        genai.configure(api_key=settings.llm.google_api_key)
        return genai.embed_content
    elif settings.embedding.provider == EmbeddingProvider.OPENAI:
        from openai import OpenAI
        client = OpenAI()
        return lambda text: client.embeddings.create(
            input=text,
            model=settings.embedding.model
        ).data[0].embedding
    raise ValueError(f"Unknown embedding provider: {settings.embedding.provider}")
