from typing import List
from .base import BaseProcessor, ProcessedChunk

class PDFProcessor(BaseProcessor):
    def can_process(self, file_path: str, mime_type: str) -> bool:
        return mime_type == "application/pdf" or file_path.lower().endswith(".pdf")

    async def process(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return [ProcessedChunk(
                content=f"[PDF processing unavailable: PyMuPDF not installed. Install with 'pip install pymupdf']",
                metadata={"source": file_path, "type": "pdf", "error": "missing_dependency"}
            )]
        
        try:
            doc = fitz.open(file_path)
            chunks = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # If no text found, try OCR
                if not text.strip():
                    try:
                        import pytesseract
                        from PIL import Image
                        import io
                        
                        pix = page.get_pixmap()
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        text = pytesseract.image_to_string(img)
                    except ImportError:
                        text = "[OCR unavailable: pytesseract or Pillow not installed]"
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
        except Exception as e:
            return [ProcessedChunk(
                content=f"[Error processing PDF: {str(e)}]",
                metadata={"source": file_path, "type": "pdf", "error": str(e)}
            )]

