from agno.agent import Agent
from agno.models.google import Gemini
import os

def get_vision_agent(model_id: str = "gemini-1.5-flash", debug_mode: bool = False) -> Agent:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not found. Vision Agent may not work correctly.")
        
    return Agent(
        name="Vision Analyst",
        model=Gemini(id=model_id, api_key=api_key),
        instructions="You are an expert at analyzing images. Describe them in detail, extracting text and explaining visual elements.",
        markdown=True,
        debug_mode=debug_mode
    )
