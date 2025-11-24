from agno.agent import Agent
from agno.models.google import Gemini
from agno.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder
from app.db.session import db_url
import os

def get_rag_agent(model_id: str = "gemini-1.5-flash", debug_mode: bool = False) -> Agent:
    api_key = os.getenv("GOOGLE_API_KEY")
    
    return Agent(
        name="RAG Assistant",
        model=Gemini(id=model_id, api_key=api_key),
        knowledge=Knowledge(
            vector_db=PgVector(
                db_url=db_url,
                table_name="rag_documents",
                embedder=OpenAIEmbedder(id="text-embedding-3-small"),
            ),
        ),
        search_knowledge=True,
        instructions="You are a helpful assistant that answers questions based on the provided documents. Always cite your sources.",
        markdown=True,
        debug_mode=debug_mode
    )
