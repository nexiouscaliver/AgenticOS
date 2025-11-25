import os
from typing import List
from .base import BaseProcessor, ProcessedChunk

class ImageProcessor(BaseProcessor):
    def __init__(self):
        self.model = None
        self._initialized = False

    def _init_model(self):
        """Lazy initialization of the model."""
        if self._initialized:
            return
        
        self._initialized = True
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                # Using gemini-1.5-flash as a reliable default for vision tasks
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                self.model = None
        except ImportError:
            print("WARNING: google-generativeai not installed. Image processing unavailable.")
            self.model = None

    def can_process(self, file_path: str, mime_type: str) -> bool:
        return mime_type.startswith("image/") or file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

    async def process(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        self._init_model()
        
        if not self.model:
            return [ProcessedChunk(
                content="[Image processing unavailable: Google API Key not set or google-generativeai not installed. Set GOOGLE_API_KEY environment variable and install with 'pip install google-generativeai']",
                metadata={"source": file_path, "type": "image", "error": "missing_dependency_or_api_key"}
            )]
        
        try:
            from PIL import Image
            img = Image.open(file_path)
            response = self.model.generate_content(["Describe this image in detail, extracting any visible text and explaining charts or diagrams.", img])
            return [ProcessedChunk(
                content=response.text,
                metadata={"source": file_path, "type": "image"}
            )]
        except ImportError:
            return [ProcessedChunk(
                content="[Image processing unavailable: Pillow not installed. Install with 'pip install Pillow']",
                metadata={"source": file_path, "type": "image", "error": "missing_pillow"}
            )]
        except Exception as e:
            return [ProcessedChunk(
                content=f"[Error processing image: {str(e)}]",
                metadata={"source": file_path, "type": "image", "error": str(e)}
            )]

