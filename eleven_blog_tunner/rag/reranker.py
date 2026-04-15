"""
重排序模块
"""
from typing import List
from eleven_blog_tunner.rag.searcher import SearchResult


class Reranker:
    """结果重排序器"""
    
    def __init__(self):
        # TODO: 初始化重排序模型
        pass
    
    async def rerank(self, query: str, candidates: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """
        对候选结果进行重排序
        """
        # TODO: 实现重排序逻辑
        return candidates[:top_k]
