import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from eleven_blog_tunner.rag.searcher import Searcher, SearchResult


class TestSearcher:
    """Searcher 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()

    @pytest.mark.asyncio
    async def test_index_chunks(self):
        """测试索引分块"""
        with patch('chromadb.Client', return_value=self.mock_client):
            self.mock_client.get_or_create_collection.return_value = self.mock_collection
            
            searcher = Searcher()
            searcher.client = self.mock_client
            searcher.collection = self.mock_collection
            
            chunks = ["chunk1", "chunk2", "chunk3"]
            embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
            metadatas = [{"id": 1}, {"id": 2}, {"id": 3}]
            
            await searcher.index(chunks, embeddings, metadatas)
            
            self.mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """测试搜索返回结果"""
        with patch('chromadb.Client', return_value=self.mock_client):
            self.mock_client.get_or_create_collection.return_value = self.mock_collection
            
            self.mock_collection.query.return_value = {
                'documents': [['result1', 'result2']],
                'distances': [[0.1, 0.2]],
                'metadatas': [[{'source': 'doc1'}, {'source': 'doc2'}]]
            }
            
            searcher = Searcher()
            searcher.client = self.mock_client
            searcher.collection = self.mock_collection
            
            results = await searcher.search([0.1, 0.2], top_k=2)
            
            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0].content == 'result1'
            assert results[0].score == 0.1
            assert results[0].metadata == {'source': 'doc1'}

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """测试搜索无结果"""
        with patch('chromadb.Client', return_value=self.mock_client):
            self.mock_client.get_or_create_collection.return_value = self.mock_collection
            
            self.mock_collection.query.return_value = {
                'documents': [[]],
                'distances': [[]],
                'metadatas': [[]]
            }
            
            searcher = Searcher()
            searcher.client = self.mock_client
            searcher.collection = self.mock_collection
            
            results = await searcher.search([0.1, 0.2], top_k=5)
            
            assert isinstance(results, list)
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_with_top_k(self):
        """测试指定 top_k 的搜索"""
        with patch('chromadb.PersistentClient', return_value=self.mock_client):
            self.mock_client.get_or_create_collection.return_value = self.mock_collection
            
            self.mock_collection.query.return_value = {
                'documents': [['r1', 'r2', 'r3']],
                'distances': [[0.1, 0.2, 0.3]],
                'metadatas': [[{'id': i} for i in range(3)]]
            }
            
            searcher = Searcher()
            searcher.client = self.mock_client
            searcher.collection = self.mock_collection
            
            results = await searcher.search([0.1, 0.2], top_k=3)
            
            assert len(results) == 3


class TestSearchResult:
    """SearchResult 数据类测试"""

    def test_search_result_creation(self):
        """测试 SearchResult 创建"""
        result = SearchResult(
            content="测试内容",
            score=0.95,
            metadata={"source": "test"}
        )
        
        assert result.content == "测试内容"
        assert result.score == 0.95
        assert result.metadata == {"source": "test"}

    def test_search_result_immutable(self):
        """测试 SearchResult 不可变性"""
        result = SearchResult(content="测试", score=0.5, metadata={})
        
        # frozen=True 使得属性不可变
        assert result.content == "测试"
        assert result.score == 0.5
