import os
import google.generativeai as genai
from typing import List
from .base import BaseProcessor, ProcessedChunk
from PIL import Image

class ImageProcessor(BaseProcessor):
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            # Using gemini-1.5-flash as a reliable default for vision tasks
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def can_process(self, file_path: str, mime_type: str) -> bool:
        return mime_type.startswith("image/") or file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

    async def process(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        if not self.model:
            return [ProcessedChunk(content="[Image processing unavailable: No API Key]", metadata={"source": file_path})]
        
        try:
            img = Image.open(file_path)
            response = self.model.generate_content(["Describe this image in detail, extracting any visible text and explaining charts or diagrams.", img])
            return [ProcessedChunk(
                content=response.text,
                metadata={"source": file_path, "type": "image"}
            )]
        except Exception as e:
            return [ProcessedChunk(content=f"[Error processing image: {str(e)}]", metadata={"source": file_path})]
