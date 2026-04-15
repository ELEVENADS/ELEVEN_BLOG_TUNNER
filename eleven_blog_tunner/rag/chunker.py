"""
文档分块模块
"""
from typing import List


class Chunker:
    """文档分块器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split(self, doc: str) -> List[str]:
        """
        将文档分块
        """
        chunks = []
        start = 0
        
        while start < len(doc):
            end = start + self.chunk_size
            chunk = doc[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap
        
        return chunks
