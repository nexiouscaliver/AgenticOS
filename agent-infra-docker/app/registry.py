"""
AgentOS Registry — exposes tools, models, and databases to AgentOS Studio
so they appear as drag-and-drop components in the visual builder.

NOTE: Agents and teams are NOT listed here — they appear automatically in
the Studio "Agents" and "Teams" sidebar sections (injected by
AgentOS._populate_registry() from the agents= and teams= lists in main.py).
The Registry page in Studio is only a component catalog for building new agents.

Model naming convention:
  - Non-thinking entries: default Gemini instance (no thinking_budget)
  - Thinking entries:     thinking_budget=5000, include_thoughts=True
  Studio agents that pick a thinking model will automatically get native
  Gemini chain-of-thought reasoning on every run.
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

THINKING_BUDGET = 5000


def _thinking(model_id: str) -> Gemini:
    """Return a Gemini model with native thinking enabled."""
    return Gemini(
        id=model_id,
        name=f"{model_id} (thinking)",
        thinking_budget=THINKING_BUDGET,
        include_thoughts=True,
    )


def _standard(model_id: str) -> Gemini:
    """Return a standard Gemini model without thinking."""
    return Gemini(id=model_id)


def get_registry() -> Registry:
    shared_db = PostgresDb(id="agent-os-db", db_url=db_url)

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
            # ── Standard (no thinking) ──────────────────────────────────
            _standard("gemini-2.5-flash-lite"),
            _standard("gemini-2.5-flash"),
            _standard("gemini-2.5-pro"),
            # ── Thinking variants (5 000 token budget) ──────────────────
            _thinking("gemini-2.5-flash-lite"),
            _thinking("gemini-2.5-flash"),
            _thinking("gemini-2.5-pro"),
        ],
        dbs=[shared_db],
        vector_dbs=[rag_vector_db],
    )
