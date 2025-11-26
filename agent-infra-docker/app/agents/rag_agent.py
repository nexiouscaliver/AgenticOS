import os
import json
import logging
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
import pandas as pd

from agno.agent import Agent
from agno.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.text_reader import TextReader
from agno.knowledge.reader.json_reader import JSONReader
from agno.knowledge.reader.website_reader import WebsiteReader
from agno.knowledge.reader.youtube_reader import YouTubeReader
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.response import ModelResponse

from app.models.factory import ModelFactory


from db.session import db_url

load_dotenv()

logger = logging.getLogger(__name__)

class UniversalIngestor:
    """
    Handles ingestion of various file formats into the Knowledge Base.
    """

    def __init__(self, knowledge_base: Knowledge, captioning_model: Any):
        self.knowledge_base = knowledge_base
        self.captioning_model = captioning_model

    def ingest_file(self, file_path: str):
        """
        Detects file type and routes to the appropriate handler.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return

        ext = path.suffix.lower()

        if ext == ".pdf":
            self._handle_document(file_path, reader=PDFReader())
        elif ext == ".txt":
            self._handle_document(file_path, reader=TextReader())
        elif ext == ".json":
            self._handle_document(file_path, reader=JSONReader())
        elif ext == ".sql":
            # Treat SQL as text for now
            self._handle_document(file_path, reader=TextReader())
        elif ext in [".png", ".jpg", ".jpeg"]:
            self._handle_image(file_path)
        elif ext in [".csv", ".xlsx", ".xls"]:
            self._handle_structured(file_path)
        else:
            logger.warning(f"Unsupported file extension: {ext} for file {file_path}")

    def ingest_url(self, url: str):
        """
        Ingests content from a URL (YouTube or Website).
        """
        if "youtube.com" in url or "youtu.be" in url:
            self._handle_youtube(url)
        else:
            self._handle_website(url)

    def _handle_document(self, file_path: str, reader):
        """
        Handles standard text-based documents using Agno readers.
        """
        logger.info(f"Ingesting document: {file_path}")
        self.knowledge_base.add_content(path=file_path, reader=reader)

    def _handle_image(self, file_path: str):
        """
        Generates a caption for the image using GLM and ingests the caption.
        """
        logger.info(f"Ingesting image: {file_path}")
        
        # Create a temporary agent for captioning
        caption_agent = Agent(
            model=self.captioning_model,
            instructions="Describe this image in extreme detail for the purpose of future retrieval. Include all visible text, objects, colors, and spatial relationships.",
            markdown=False
        )
        
        # Read image bytes (GLM provider handles image bytes/urls if supported, 
        # but here we might need to pass it as a message content part)
        # Assuming GLM45Provider supports local file paths or we need to convert to base64/bytes
        # For simplicity, we'll try passing the path if the provider supports it, 
        # or we might need to implement a helper. 
        # Looking at GLM provider code, it handles 'image_url' or 'text'. 
        # We will construct a message with the image.
        
        # Note: The GLM provider implementation we saw earlier handles list content with "type": "image_url".
        # We'll assume we can pass the local path as a data URL or similar if needed, 
        # but for now let's try to use the Agent's multimodal capability if available.
        # If the Agent class supports `images` argument in `print_response` or `run`, we use that.
        
        # We'll use a simple approach: read file as bytes/base64 if needed, but Agno's `Image` class is the standard way.
        from agno.media import Image
        
        response: ModelResponse = caption_agent.run(
            "Describe this image.",
            images=[Image(filepath=file_path)]
        )
        
        caption = response.content
        if caption:
            # Add the caption as a text document to the knowledge base
            # We create a virtual "text file" content
            from agno.knowledge.document import Document
            
            doc = Document(
                content=caption,
                meta_data={"source": file_path, "type": "image_caption"}
            )
            self.knowledge_base.add_document(doc)
            logger.info(f"Generated and indexed caption for {file_path}")

    def _handle_structured(self, file_path: str):
        """
        Converts CSV/Excel to Markdown and ingests it.
        """
        logger.info(f"Ingesting structured data: {file_path}")
        path = Path(file_path)
        ext = path.suffix.lower()
        
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Convert to markdown
            markdown_table = df.to_markdown(index=False)
            
            # Add as text document
            from agno.knowledge.document import Document
            doc = Document(
                content=markdown_table,
                meta_data={"source": file_path, "type": "structured_data"}
            )
            self.knowledge_base.add_document(doc)
            
        except Exception as e:
            logger.error(f"Error processing structured file {file_path}: {e}")

    def _handle_website(self, url: str):
        logger.info(f"Ingesting website: {url}")
        self.knowledge_base.add_content(url=url, reader=WebsiteReader())

    def _handle_youtube(self, url: str):
        logger.info(f"Ingesting YouTube video: {url}")
        self.knowledge_base.add_content(url=url, reader=YouTubeReader())


def get_rag_agent(
    model_id: str = "glm-4.5-air",
    debug_mode: bool = False,
) -> Agent:
    """
    Returns a configured RAG Agent with universal ingestion capabilities.
    """
    
    # Define Knowledge Base
    knowledge_base = Knowledge(
        vector_db=PgVector(
            db_url=db_url,
            table_name="rag_documents",
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"), # Using OpenAI for embeddings as per plan/standard
        ),
    )
    
    # Define Model
    model = ModelFactory.create_model(model_id=model_id)
    
    # Create Agent
    agent = Agent(
        id="versatile-rag-agent",
        name="Versatile RAG Agent",
        model=model,
        knowledge=knowledge_base,
        search_knowledge=True,
        # tools=[DuckDuckGoTools()],
        description=dedent("""\
            You are a versatile RAG agent capable of retrieving information from a wide variety of sources 
            including documents, images, spreadsheets, and the web.
            
            When asked about images, you rely on the detailed captions stored in your knowledge base.
            When asked about data, you rely on the markdown representations of spreadsheets.
        """),
        instructions=dedent("""\
            - Always search your knowledge base first before answering.
            - If the user asks about a specific file, look for it in the metadata.
            - Provide citations or references to the source file when possible.
            - If the information is not in the knowledge base, use DuckDuckGo to search the web.
        """),
        markdown=True,
        debug_mode=debug_mode,
        add_datetime_to_context=True,
    )
    
    # Attach the ingestor to the agent instance for easy access
    # This is a bit of a monkey-patch/custom attribute, but useful for the user
    agent.ingestor = UniversalIngestor(knowledge_base, model)
    
    return agent

# Example usage block (commented out)
# if __name__ == "__main__":
#     agent = get_rag_agent()
#     # agent.ingestor.ingest_file("path/to/file.pdf")
#     # agent.print_response("What is in the file?")
