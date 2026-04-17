import pytest
from unittest.mock import patch, MagicMock
from eleven_blog_tunner.rag.reranker import Reranker
from eleven_blog_tunner.rag.searcher import SearchResult


class TestReranker:
    """Reranker 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.reranker = Reranker()

    def test_reranker_initialization(self):
        """测试 Reranker 初始化"""
        assert self.reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert self.reranker.model is None

    @pytest.mark.asyncio
    async def test_simple_rerank_fallback(self):
        """测试简单重排序降级方案"""
        candidates = [
            SearchResult(content="Python 编程", score=0.5, metadata={}),
            SearchResult(content="Java 编程", score=0.6, metadata={}),
            SearchResult(content="编程语言", score=0.4, metadata={}),
        ]
        
        result = await self.reranker.rerank("编程", candidates, top_k=2)
        
        assert len(result) == 2
        assert isinstance(result[0], SearchResult)

    @pytest.mark.asyncio
    async def test_simple_rerank_keyword_match(self):
        """测试简单重排序关键词匹配"""
        candidates = [
            SearchResult(content="Python教程", score=0.3, metadata={}),
            SearchResult(content="Java教程", score=0.5, metadata={}),
            SearchResult(content="编程指南", score=0.4, metadata={}),
        ]
        
        result = await self.reranker.rerank("Python", candidates, top_k=2)
        
        assert len(result) == 2
        assert result[0].content == "Python教程"

    @pytest.mark.asyncio
    async def test_rerank_with_cross_encoder(self):
        """测试 Cross-encoder 重排序"""
        reranker = Reranker()
        reranker.model = MagicMock()
        reranker.model.predict.return_value = [0.9, 0.7, 0.5]
        
        candidates = [
            SearchResult(content="Python编程", score=0.5, metadata={}),
            SearchResult(content="Java编程", score=0.6, metadata={}),
            SearchResult(content="其他内容", score=0.4, metadata={}),
        ]
        
        result = await reranker.rerank("Python", candidates, top_k=2)
        
        assert len(result) == 2
        assert result[0].content == "Python编程"

    @pytest.mark.asyncio
    async def test_rerank_top_k_less_than_candidates(self):
        """测试 top_k 小于候选数量"""
        reranker = Reranker()
        reranker.model = MagicMock()
        reranker.model.predict.return_value = [0.3, 0.6, 0.9]
        
        candidates = [
            SearchResult(content="低分", score=0.3, metadata={}),
            SearchResult(content="中分", score=0.6, metadata={}),
            SearchResult(content="高分", score=0.9, metadata={}),
        ]
        
        result = await reranker.rerank("测试", candidates, top_k=1)
        
        assert len(result) == 1
        assert result[0].content == "高分"

    @pytest.mark.asyncio
    async def test_rerank_top_k_greater_than_candidates(self):
        """测试 top_k 大于候选数量"""
        candidates = [
            SearchResult(content="内容1", score=0.5, metadata={}),
            SearchResult(content="内容2", score=0.6, metadata={}),
        ]
        
        result = await self.reranker.rerank("测试", candidates, top_k=10)
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_rerank_empty_candidates(self):
        """测试空候选列表"""
        result = await self.reranker.rerank("测试", [], top_k=5)
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_rerank_preserves_metadata(self):
        """测试重排序保留元数据"""
        candidates = [
            SearchResult(content="内容1", score=0.5, metadata={"id": 1, "source": "doc1"}),
            SearchResult(content="内容2", score=0.6, metadata={"id": 2, "source": "doc2"}),
        ]
        
        result = await self.reranker.rerank("测试", candidates, top_k=2)
        
        for r in result:
            assert "id" in r.metadata
            assert "source" in r.metadata
