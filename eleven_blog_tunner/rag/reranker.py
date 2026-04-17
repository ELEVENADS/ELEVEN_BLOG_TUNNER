"""
重排序模块
"""
from typing import List
from eleven_blog_tunner.rag.searcher import SearchResult


class Reranker:
    """结果重排序器"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """
        加载 Cross-encoder 模型
        """
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
        except ImportError:
            # 如果没有安装 sentence-transformers，使用简单的排序
            self.model = None
    
    async def rerank(self, query: str, candidates: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """
        对候选结果进行重排序
        """
        if self.model is not None:
            return await self._cross_encoder_rerank(query, candidates, top_k)
        else:
            return self._simple_rerank(query, candidates, top_k)
    
    async def _cross_encoder_rerank(self, query: str, candidates: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """
        使用 Cross-encoder 进行重排序
        """
        # 准备输入对
        pairs = [(query, candidate.content) for candidate in candidates]
        
        # 获取相关性分数
        scores = self.model.predict(pairs)
        
        # 按分数排序
        scored_candidates = list(zip(candidates, scores))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前 top_k 个结果
        return [candidate for candidate, _ in scored_candidates[:top_k]]
    
    def _simple_rerank(self, query: str, candidates: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """
        简单重排序（当 Cross-encoder 不可用时）
        """
        # 基于字符串匹配的简单排序
        def score_candidate(candidate):
            content = candidate.content.lower()
            query_terms = query.lower().split()
            score = 0
            for term in query_terms:
                if term in content:
                    score += 1
            # 结合原始相似度分数
            return score - candidate.score
        
        sorted_candidates = sorted(candidates, key=score_candidate, reverse=True)
        return sorted_candidates[:top_k]
