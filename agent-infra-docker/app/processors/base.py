from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProcessedChunk:
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata
        }

class BaseProcessor(ABC):
    """Abstract base class for all document processors."""
    
    @abstractmethod
    def can_process(self, file_path: str, mime_type: str) -> bool:
        """Determine if this processor can handle the given file."""
        pass

    @abstractmethod
    async def process(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        """Process the file and return a list of chunks."""
        pass
