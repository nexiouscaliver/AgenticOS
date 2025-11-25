from typing import List, Optional
from .base import BaseProcessor, ProcessedChunk
from .pdf_processor import PDFProcessor
from .image_processor import ImageProcessor
from .structured_processor import StructuredProcessor

class ProcessorManager:
    def __init__(self):
        self.processors: List[BaseProcessor] = [
            PDFProcessor(),
            ImageProcessor(),
            StructuredProcessor()
        ]

    async def process_file(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        for processor in self.processors:
            if processor.can_process(file_path, mime_type):
                return await processor.process(file_path, mime_type)
        raise ValueError(f"No processor found for file: {file_path} ({mime_type})")
