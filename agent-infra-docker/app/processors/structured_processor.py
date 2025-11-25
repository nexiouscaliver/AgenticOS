from typing import List
from .base import BaseProcessor, ProcessedChunk

class StructuredProcessor(BaseProcessor):
    def can_process(self, file_path: str, mime_type: str) -> bool:
        return file_path.lower().endswith(('.csv', '.xlsx', '.json'))

    async def process(self, file_path: str, mime_type: str) -> List[ProcessedChunk]:
        try:
            import pandas as pd
        except ImportError:
            return [ProcessedChunk(
                content=f"[Structured data processing unavailable: pandas not installed. Install with 'pip install pandas openpyxl']",
                metadata={"source": file_path, "type": "structured", "error": "missing_dependency"}
            )]
        
        chunks = []
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.lower().endswith('.json'):
                df = pd.read_json(file_path)
            else:
                return []
            
            # Chunking large tables by rows
            rows_per_chunk = 50 # Smaller chunks for better RAG retrieval
            for i in range(0, len(df), rows_per_chunk):
                chunk_df = df.iloc[i:i+rows_per_chunk]
                chunks.append(ProcessedChunk(
                    content=chunk_df.to_markdown(index=False),
                    metadata={
                        "source": file_path, 
                        "type": "structured", 
                        "rows": f"{i}-{i+len(chunk_df)}"
                    }
                ))
        except Exception as e:
             chunks.append(ProcessedChunk(
                 content=f"[Error processing structured file: {str(e)}]",
                 metadata={"source": file_path, "type": "structured", "error": str(e)}
             ))
        
        return chunks

