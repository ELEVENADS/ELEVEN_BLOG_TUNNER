"""
向量检索模块
"""
from typing import List, Dict, Any
from dataclasses import dataclass
import chromadb
from eleven_blog_tunner.core.config import get_settings


@dataclass(frozen=True)
class SearchResult:
    """搜索结果"""
    content: str
    score: float
    metadata: Dict[str, Any]


class Searcher:
    """向量检索器"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_path
        )
        self.collection = self.client.get_or_create_collection("documents")
    
    async def index(self, chunks: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]] = None):
        """建立索引"""
        if metadatas is None:
            metadatas = [{} for _ in chunks]
        
        # 生成唯一ID
        ids = [f"doc_{i}" for i in range(len(chunks))]
        
        # 向量化存储
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    async def search(self, query_embedding: List[float], top_k: int = 10) -> List[SearchResult]:
        """向量检索"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            result = SearchResult(
                content=results['documents'][0][i],
                score=results['distances'][0][i],
                metadata=results['metadatas'][0][i]
            )
            search_results.append(result)
        
        return search_results
