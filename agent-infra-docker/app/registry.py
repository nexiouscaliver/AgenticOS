"""
AgentOS Registry — exposes tools, models, and databases to AgentOS Studio
so they appear as drag-and-drop components in the visual builder.

Agents and teams are injected automatically by AgentOS._populate_registry()
from the agents= and teams= lists; they do not need to be listed here.
"""

from agno.registry import Registry
from agno.db.postgres import PostgresDb
from agno.vectordb.pgvector import PgVector, SearchType
from agno.models.google.gemini import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.knowledge.embedder.google import GeminiEmbedder

from db.session import db_url


def get_registry() -> Registry:
    # Shared database used by all agents for session / memory storage
    shared_db = PostgresDb(id="agent-os-db", db_url=db_url)

    # RAG knowledge vector database
    rag_vector_db = PgVector(
        db_url=db_url,
        table_name="rag_documents",
        search_type=SearchType.hybrid,
        embedder=GeminiEmbedder(id="gemini-embedding-2"),
    )

    return Registry(
        name="AgenticOS Registry",
        description="All tools, models, and databases available in this AgentOS instance",
        # Tools available for Studio to wire into new/edited agents
        tools=[
            DuckDuckGoTools(),
        ],
        # Models Studio can assign to agents
        models=[
            Gemini(id="gemini-2.5-flash-lite"),
            Gemini(id="gemini-2.5-flash"),
            Gemini(id="gemini-2.5-pro"),
        ],
        # Databases Studio can attach to agents for persistence
        dbs=[shared_db],
        # Vector databases Studio can attach to agents for knowledge retrieval
        vector_dbs=[rag_vector_db],
    )
