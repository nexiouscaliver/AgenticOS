"""
AgentOS Registry — exposes tools, models, and databases to AgentOS Studio
so they appear as drag-and-drop components in the visual builder.

NOTE: Agents and teams are NOT listed here — they appear automatically in
the Studio "Agents" and "Teams" sidebar sections (injected by
AgentOS._populate_registry() from the agents= and teams= lists in main.py).
The Registry page in Studio is only a component catalog for building new agents.
"""

from agno.registry import Registry
from agno.db.postgres import PostgresDb
from agno.vectordb.pgvector import PgVector, SearchType
from agno.models.google.gemini import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.calculator import CalculatorTools
from agno.tools.file import FileTools
from agno.tools.python import PythonTools
from agno.tools.csv_toolkit import CsvTools
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
        tools=[
            DuckDuckGoTools(),    # web search + news search
            CalculatorTools(),   # math operations
            FileTools(),         # read/write/search files
            PythonTools(),       # run python code snippets
            CsvTools(),          # read and query CSV files
        ],
        models=[
            Gemini(id="gemini-2.5-flash-lite"),
            Gemini(id="gemini-2.5-flash"),
            Gemini(id="gemini-2.5-pro"),
        ],
        dbs=[shared_db],
        vector_dbs=[rag_vector_db],
    )
