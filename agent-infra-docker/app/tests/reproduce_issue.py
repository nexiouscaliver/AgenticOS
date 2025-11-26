
import asyncio
import os
import sys
import inspect
from app.models.glm import GLM45Provider
from agno.models.message import Message

async def reproduce():
    print(f"GLM45Provider file: {inspect.getfile(GLM45Provider)}")
    # Initialize provider
    provider = GLM45Provider(api_key="dummy", base_url="http://localhost:8000/v1")
    
    # Construct a message that mimics what Agno might send for a file
    # Based on the error "Unknown part type: file None", we suspect a part with type='file'
    
    # Scenario 1: Message with a file part
    # We use the downloaded test_doc.pdf
    pdf_path = os.path.abspath("test_doc.pdf")
    messages = [
        Message(
            role="user",
            content=[
                {"type": "text", "text": "Analyze this file"},
                {"type": "file", "file_url": {"url": f"file://{pdf_path}"}, "name": "test_doc.pdf"}
            ]
        )
    ]
    
    print("Attempting to invoke model with file part...")
    try:
        # We use ainvoke_stream as in the stack trace
        # OpenAIChat.ainvoke_stream apparently requires assistant_message as 2nd arg
        async for response in provider.ainvoke_stream(messages, None):
            print(response)
    except Exception as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
