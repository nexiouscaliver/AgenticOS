import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[2]))
sys.path.append(str(Path(__file__).parents[1]))

from app.agents.rag_agent import get_rag_agent

def test_rag_agent():
    print("Initializing RAG Agent...")
    agent = get_rag_agent(debug_mode=True)
    
    # Test Ingestion (Mocking file paths for now, or we can create dummy files)
    # For this test, we will just check if the ingestor is attached and methods exist
    print("Verifying Ingestor...")
    assert hasattr(agent, "ingestor")
    assert hasattr(agent.ingestor, "ingest_file")
    assert hasattr(agent.ingestor, "ingest_url")
    
    print("RAG Agent initialized and verified successfully.")
    
    # Optional: Try a simple query if the DB is up
    try:
        response = agent.run("Hello, who are you?")
        print("Agent Response:", response.content)
    except Exception as e:
        print(f"Agent run failed (expected if DB not ready): {e}")

if __name__ == "__main__":
    test_rag_agent()
