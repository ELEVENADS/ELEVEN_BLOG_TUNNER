import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from eleven_blog_tunner.rag.embedding import EmbeddingService


class TestEmbeddingService:
    """EmbeddingService 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.embedder = EmbeddingService(model_name="text-embedding-3-small", use_local=False)

    @pytest.mark.asyncio
    async def test_embed_openai_returns_vector(self):
        """测试 OpenAI embed 返回向量"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3, 0.4]}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await self.embedder.embed("测试文本")

            assert isinstance(result, list)
            assert len(result) == 4
            assert result == [0.1, 0.2, 0.3, 0.4]

    @pytest.mark.asyncio
    async def test_embed_batch_openai(self):
        """测试 OpenAI 批量向量化"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await self.embedder.embed_batch(["文本1", "文本2"])

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_embed_local_ollama(self):
        """测试本地 Ollama 向量化"""
        local_embedder = EmbeddingService(use_local=True)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embedding": [0.7, 0.8, 0.9]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await local_embedder.embed("本地测试文本")

            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [0.7, 0.8, 0.9]

    @pytest.mark.asyncio
    async def test_embed_local_batch(self):
        """测试本地模型批量向量化"""
        local_embedder = EmbeddingService(use_local=True)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await local_embedder.embed_batch(["文本1", "文本2"])

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.1, 0.2, 0.3]

    def test_embedder_has_correct_model(self):
        """测试 embedder 配置了正确的模型"""
        embedder = EmbeddingService(model_name="text-embedding-3-small", use_local=False)
        assert embedder.model_name == "text-embedding-3-small"

    @pytest.mark.asyncio
    async def test_embed_empty_text(self):
        """测试空文本向量化"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": []}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await self.embedder.embed("")

            assert isinstance(result, list)
            assert len(result) == 0
