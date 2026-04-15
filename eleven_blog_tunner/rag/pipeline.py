"""
RAG 处理管道
"""
from typing import List
from eleven_blog_tunner.rag.document_washer import DocumentWasher
from eleven_blog_tunner.rag.chunker import Chunker
from eleven_blog_tunner.rag.embedding import EmbeddingService
from eleven_blog_tunner.rag.searcher import Searcher, SearchResult
from eleven_blog_tunner.rag.reranker import Reranker
from eleven_blog_tunner.core.config import get_settings


class RAGPipeline:
    """RAG 处理管道"""
    
    def __init__(self):
        settings = get_settings()
        self.washer = DocumentWasher()
        self.chunker = Chunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.embedder = EmbeddingService(model_name=settings.embedding_model)
        self.searcher = Searcher()
        self.reranker = Reranker()
    
    async def process_document(self, doc: str) -> bool:
        """
        处理并存储文档
        """
        try:
            # 清洗
            clean_doc = self.washer.wash(doc)
            # 分块
            chunks = self.chunker.split(clean_doc)
            # 向量化并存储
            embeddings = await self.embedder.embed_batch(chunks)
            await self.searcher.index(chunks, embeddings)
            return True
        except Exception as e:
            # TODO: 添加日志
            print(f"文档处理失败: {e}")
            return False
    
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        检索流程
        """
        # 向量化查询
        query_emb = await self.embedder.embed(query)
        # 初步检索
        candidates = await self.searcher.search(query_emb, top_k=top_k*2)
        # 重排序
        results = await self.reranker.rerank(query, candidates, top_k=top_k)
        return results
