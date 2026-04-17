import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from eleven_blog_tunner.rag.pipeline import RAGPipeline


class TestRAGPipeline:
    """RAGPipeline 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.mock_embedder = MagicMock()
        self.mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
        self.mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])

    @pytest.mark.asyncio
    async def test_process_document_basic(self):
        """测试处理文档基本功能"""
        mock_searcher = MagicMock()
        mock_searcher.index = AsyncMock()
        
        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.washer.wash = MagicMock(return_value="清洗后的文本")
            pipeline.chunker = MagicMock()
            pipeline.chunker.split = MagicMock(return_value=[
                ("chunk1", {"chunk_index": 0}),
                ("chunk2", {"chunk_index": 1})
            ])
            pipeline.embedder = self.mock_embedder
            pipeline.searcher = mock_searcher
            pipeline.reranker = MagicMock()
            
            result = await pipeline.process_document(
                doc="原始文档",
                metadata={"source": "test"},
                file_type="markdown",
                chunk_strategy="semantic"
            )
            
            assert result is True
            pipeline.searcher.index.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_with_metadata(self):
        """测试处理文档时元数据传递"""
        mock_searcher = MagicMock()
        mock_searcher.index = AsyncMock()
        
        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.washer.wash = MagicMock(return_value="清洗后的文本")
            pipeline.chunker = MagicMock()
            pipeline.chunker.split = MagicMock(return_value=[
                ("chunk1", {"chunk_index": 0, "source": "test"}),
                ("chunk2", {"chunk_index": 1, "source": "test"})
            ])
            pipeline.embedder = self.mock_embedder
            pipeline.searcher = mock_searcher
            pipeline.reranker = MagicMock()
            
            await pipeline.process_document(
                doc="原始文档",
                metadata={"source": "test", "category": "tech"}
            )
            
            call_args = pipeline.searcher.index.call_args
            chunks, embeddings, metadatas = call_args[0]
            
            for metadata in metadatas:
                assert "source" in metadata
                assert "category" in metadata
                assert metadata["file_type"] == "txt"

    @pytest.mark.asyncio
    async def test_process_document_handles_exception(self):
        """测试处理文档异常处理"""
        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.washer.wash = MagicMock(side_effect=Exception("Wash failed"))
            pipeline.chunker = MagicMock()
            pipeline.embedder = self.mock_embedder
            pipeline.searcher = MagicMock()
            pipeline.reranker = MagicMock()
            
            result = await pipeline.process_document(doc="原始文档")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_search_basic(self):
        """测试搜索基本功能"""
        mock_searcher = MagicMock()
        mock_searcher.search = AsyncMock(return_value=[
            MagicMock(content="result1", score=0.1, metadata={}),
            MagicMock(content="result2", score=0.2, metadata={})
        ])
        
        mock_reranker = MagicMock()
        mock_reranker.rerank = AsyncMock(return_value=[
            MagicMock(content="reranked1", score=0.9, metadata={})
        ])
        
        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.chunker = MagicMock()
            pipeline.embedder = self.mock_embedder
            pipeline.searcher = mock_searcher
            pipeline.reranker = mock_reranker
            
            results = await pipeline.search("查询", top_k=5)
            
            assert len(results) == 1
            pipeline.searcher.search.assert_called_once()
            pipeline.reranker.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_calls_embedder(self):
        """测试搜索调用 embedder"""
        mock_searcher = MagicMock()
        mock_searcher.search = AsyncMock(return_value=[])

        mock_reranker = MagicMock()
        mock_reranker.rerank = AsyncMock(return_value=[])

        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.chunker = MagicMock()
            pipeline.embedder = MagicMock()
            pipeline.embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.searcher = mock_searcher
            pipeline.reranker = mock_reranker

            await pipeline.search("查询")

            pipeline.embedder.embed.assert_called_once_with("查询")

    @pytest.mark.asyncio
    async def test_search_uses_top_k_for_initial_search(self):
        """测试搜索使用 2*top_k 进行初步检索"""
        mock_searcher = MagicMock()
        mock_searcher.search = AsyncMock(return_value=[])

        mock_reranker = MagicMock()
        mock_reranker.rerank = AsyncMock(return_value=[])

        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.chunker = MagicMock()
            pipeline.embedder = MagicMock()
            pipeline.embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.searcher = mock_searcher
            pipeline.reranker = mock_reranker

            await pipeline.search("查询", top_k=5)

            pipeline.searcher.search.assert_called_once()
            # search 方法被调用时使用 top_k*2，即 5*2=10
            call_args = pipeline.searcher.search.call_args
            # call_args[0] 是位置参数 (query_emb,), call_args[1] 是 kwargs {'top_k': 10}
            assert call_args[1]['top_k'] == 10

    @pytest.mark.asyncio
    async def test_search_reranks_candidates(self):
        """测试搜索对候选结果重排序"""
        candidates = [
            MagicMock(content="c1", score=0.1),
            MagicMock(content="c2", score=0.2),
            MagicMock(content="c3", score=0.3),
        ]
        
        mock_searcher = MagicMock()
        mock_searcher.search = AsyncMock(return_value=candidates)
        
        mock_reranker = MagicMock()
        mock_reranker.rerank = AsyncMock(return_value=candidates[::-1])
        
        with patch('eleven_blog_tunner.rag.pipeline.RAGPipeline.__init__', return_value=None):
            pipeline = RAGPipeline()
            pipeline.washer = MagicMock()
            pipeline.chunker = MagicMock()
            pipeline.embedder = self.mock_embedder
            pipeline.searcher = mock_searcher
            pipeline.reranker = mock_reranker
            
            await pipeline.search("查询", top_k=3)
            
            pipeline.reranker.rerank.assert_called_once()
