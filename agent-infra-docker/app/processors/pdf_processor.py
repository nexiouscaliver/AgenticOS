import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import List
from .base import BaseProcessor, ProcessedChunk

class PDFProcessor(BaseProcessor):
    def can_process(self, file_path: str, mime_type: str) -> bool:
        return mime_type == "application/pdf" or file_path.lower().endswith(".pdf")

    async def process(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        doc = fitz.open(file_path)
        chunks = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # If no text found, try OCR
            if not text.strip():
                try:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    text = pytesseract.image_to_string(img)
                except Exception as e:
                    print(f"OCR failed for page {page_num} in {file_path}: {e}")
            
            if text.strip():
                chunks.append(ProcessedChunk(
                    content=text,
                    metadata={
                        "page": page_num + 1, 
                        "source": file_path,
                        "type": "pdf"
                    }
                ))
                
        return chunks
