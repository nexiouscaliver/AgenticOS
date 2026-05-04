"""
Knowledge Base Curator Agent - Manages the shared research knowledge base
with admin approval required for every modification.
"""

from textwrap import dedent
from dotenv import load_dotenv

load_dotenv()

from agno.agent import Agent
from agno.approval import approval
from agno.db.postgres import PostgresDb
from agno.knowledge import Knowledge
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.tools import tool
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.pgvector import PgVector, SearchType

from db.session import db_url

_DB_ID = "advanced-research-storage"
_TABLE = "advanced_research_knowledge"
_EMBEDDER_ID = "gemini-embedding-2"


def _vector_db() -> PgVector:
    return PgVector(
        db_url=db_url,
        table_name=_TABLE,
        search_type=SearchType.hybrid,
        embedder=GeminiEmbedder(id=_EMBEDDER_ID),
    )


def _knowledge() -> Knowledge:
    return Knowledge(
        name="kb-curator-knowledge",
        contents_db=PostgresDb(id=_DB_ID, db_url=db_url),
        vector_db=_vector_db(),
    )


@approval
@tool(requires_confirmation=True)
def add_to_knowledge_base(url: str, doc_name: str, description: str = "") -> str:
    """
    Add a document URL to the shared research knowledge base.
    Affects all agents that search this KB — requires admin approval.
    """
    _knowledge().add_content(
        name=doc_name,
        description=description or None,
        url=url,
        upsert=True,
    )
    return f"Added '{doc_name}' from {url} to the knowledge base."


@approval
@tool(requires_confirmation=True)
def remove_from_knowledge_base(doc_name: str) -> str:
    """
    Remove a document from the knowledge base by name.
    Deletes both the vector embeddings and the metadata record shown in Studio.
    IRREVERSIBLE — requires admin approval before execution.
    """
    kb = _knowledge()
    contents, _ = kb.get_content()

    match = next((c for c in contents if c.name == doc_name), None)
    if match is None:
        return f"No document named '{doc_name}' found in the knowledge base — nothing removed."

    kb.remove_content_by_id(match.id)
    return f"Removed '{doc_name}' from the knowledge base (vectors + metadata)."


def get_kb_curator_agent(
    model_id: str = "gemini-2.5-flash-lite",
    debug_mode: bool = False,
) -> Agent:
    """
    Knowledge Base Curator with approval-gated add and remove operations.
    Uses the same DB and vector table as the web research agent.
    """
    from models.factory import ModelFactory, TaskType

    model_instance = ModelFactory.create_model(
        ModelFactory.get_optimal_model(task_type=TaskType.ANALYSIS, priority="balanced")
    )

    return Agent(
        id="kb-curator-agent",
        name="Knowledge Base Curator",
        model=model_instance,
        tools=[DuckDuckGoTools(), add_to_knowledge_base, remove_from_knowledge_base],
        description=dedent("""\
            You manage the shared research knowledge base used by all agents in the system.
            You can add new documents (by URL) or remove outdated ones by name.
            Every modification — add or remove — requires admin approval before it executes.
            This is enforced automatically and cannot be bypassed.
        """),
        instructions=dedent("""\
            You are the Knowledge Base Curator. Your job is to keep the shared research
            knowledge base accurate, current, and relevant.

            ## Adding a document
            1. Confirm the URL and a clear, descriptive document name with the user.
            2. Optionally accept a brief description of what the document covers.
            3. Call add_to_knowledge_base — the run pauses for admin approval.
            4. After approval executes, confirm the document was added.

            ## Removing a document
            1. Confirm the exact document name the user wants to remove.
            2. Remind the user this is irreversible and affects every agent on the system.
            3. Call remove_from_knowledge_base — the run pauses for admin approval.
            4. After approval executes, confirm what was removed.

            ## Rules
            - Never modify the KB without explicit user instruction.
            - If unsure about the document name, ask before calling any tool.
            - You can search the KB to verify what is currently in it before making changes.
            - Approvals are resolved externally — do not attempt to skip or re-trigger them.
        """),
        db=PostgresDb(id=_DB_ID, db_url=db_url),
        knowledge=Knowledge(
            name="kb-curator-knowledge",
            contents_db=PostgresDb(id=_DB_ID, db_url=db_url),
            vector_db=PgVector(
                db_url=db_url,
                table_name=_TABLE,
                search_type=SearchType.hybrid,
                embedder=GeminiEmbedder(id=_EMBEDDER_ID),
            ),
        ),
        search_knowledge=True,
        add_history_to_context=True,
        num_history_runs=3,
        markdown=True,
        add_datetime_to_context=True,
        debug_mode=debug_mode,
    )
