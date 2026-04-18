"""
RAG Pipeline 端到端测试
测试完整的文档处理和检索流程
"""
import asyncio
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from eleven_blog_tunner.rag.pipeline import RAGPipeline
from eleven_blog_tunner.rag.searcher import SearchResult
from eleven_blog_tunner.core.config import get_settings


class TestRAGPipelineE2E:
    """RAG Pipeline 端到端测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试设置"""
        self.settings = get_settings()
        self.test_vector_db_path = "./data/test_vector_db_e2e"
        yield
        self._cleanup()

    def _cleanup(self):
        """清理测试数据"""
        if Path(self.test_vector_db_path).exists():
            shutil.rmtree(self.test_vector_db_path, ignore_errors=True)

    def test_config_loading(self):
        """测试 1: 配置加载"""
        assert self.settings.chunk_size > 0
        assert self.settings.chunk_overlap >= 0
        assert self.settings.embedding_model
        print(f"✓ 配置加载成功: chunk_size={self.settings.chunk_size}, embedding_model={self.settings.embedding_model}")

    def test_pipeline_initialization(self):
        """测试 2: Pipeline 初始化（使用 Mock 避免加载模型）"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()
            assert pipeline is not None
            assert pipeline.washer is not None
            assert pipeline.chunker is not None
            assert pipeline.embedder is not None
            assert pipeline.searcher is not None
            assert pipeline.reranker is not None
            print("✓ Pipeline 初始化成功，所有组件已加载")

    @pytest.mark.asyncio
    async def test_document_washer_integration(self):
        """测试 3: 文档清洗组件集成"""
        pipeline = RAGPipeline()

        markdown_doc = """
        # 标题
        **粗体** and *斜体*
        [链接](http://example.com)
        `代码`
        """
        cleaned = pipeline.washer.wash(markdown_doc, file_type="markdown")
        assert "标题" in cleaned
        assert "**" not in cleaned
        assert "[链接]" not in cleaned
        print(f"✓ 文档清洗组件正常工作")

    @pytest.mark.asyncio
    async def test_chunker_integration(self):
        """测试 4: 分块组件集成"""
        pipeline = RAGPipeline()

        test_doc = """
        第一段内容。这是一个比较长的段落，用于测试分块功能。
        第二段内容。这里继续添加一些文本，确保文档足够长。
        第三段内容。测试分块是否能正确处理多个段落。
        第四段内容。再添加一些内容以确保有足够的文本进行分块。
        第五段内容。这是文档的最后一段。
        """

        chunks_with_meta = pipeline.chunker.split(test_doc, strategy="semantic", metadata={"source": "test"})
        assert len(chunks_with_meta) > 0
        assert all(isinstance(chunk, str) and isinstance(meta, dict) for chunk, meta in chunks_with_meta)
        print(f"✓ 分块组件正常工作，生成 {len(chunks_with_meta)} 个块")

    @pytest.mark.asyncio
    async def test_document_processing_full_flow(self):
        """测试 5: 文档处理完整流程（Mock embedder 和 searcher）"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            mock_searcher.search = AsyncMock(return_value=[])
            pipeline.searcher = mock_searcher

            test_doc = """
            这是一篇关于人工智能的测试文章。
            人工智能是计算机科学的一个分支，旨在创造智能机器。
            机器学习是人工智能的一个子领域。
            深度学习是机器学习的一个分支。
            """

            result = await pipeline.process_document(
                doc=test_doc,
                metadata={"source": "test_e2e", "category": "AI"},
                file_type="txt",
                chunk_strategy="semantic"
            )

            assert result is True
            mock_embedder.embed_batch.assert_called_once()
            mock_searcher.index.assert_called_once()
            print("✓ 文档处理完整流程测试通过")

    @pytest.mark.asyncio
    async def test_search_full_flow(self):
        """测试 6: 搜索完整流程"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            mock_embedder = MagicMock()
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.search = AsyncMock(return_value=[
                SearchResult(content="result1", score=0.1, metadata={}),
                SearchResult(content="result2", score=0.2, metadata={})
            ])
            pipeline.searcher = mock_searcher

            mock_reranker = MagicMock()
            mock_reranker.rerank = AsyncMock(return_value=[
                SearchResult(content="reranked1", score=0.9, metadata={})
            ])
            pipeline.reranker = mock_reranker

            results = await pipeline.search("人工智能", top_k=3)

            assert len(results) == 1
            mock_embedder.embed.assert_called_once_with("人工智能")
            mock_searcher.search.assert_called_once()
            mock_reranker.rerank.assert_called_once()
            print("✓ 搜索完整流程测试通过")

    @pytest.mark.asyncio
    async def test_search_with_mock_results(self):
        """测试 7: 搜索结果结构验证"""
        result = SearchResult(
            content="人工智能是计算机科学的一个重要分支。",
            score=0.95,
            metadata={"topic": "AI", "id": "1"}
        )

        assert result.content == "人工智能是计算机科学的一个重要分支。"
        assert result.score == 0.95
        assert result.metadata == {"topic": "AI", "id": "1"}
        assert hasattr(result, 'content')
        assert hasattr(result, 'score')
        assert hasattr(result, 'metadata')
        print("✓ 搜索结果结构正确")

    @pytest.mark.asyncio
    async def test_chunking_strategies(self):
        """测试 8: 不同分块策略"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            long_doc = """
            第一段内容。这是一个比较长的段落，用于测试分块功能。
            第二段内容。这里继续添加一些文本，确保文档足够长。
            第三段内容。测试分块是否能正确处理多个段落。
            第四段内容。再添加一些内容以确保有足够的文本进行分块。
            第五段内容。这是文档的最后一段。
            """

            strategies = ["semantic", "recursive", "fixed"]
            for strategy in strategies:
                chunks_with_meta = pipeline.chunker.split(long_doc, strategy=strategy, metadata={})
                assert len(chunks_with_meta) > 0, f"分块策略 {strategy} 失败"
                print(f"  - {strategy} 分块: {len(chunks_with_meta)} 块")

            print(f"✓ 所有分块策略 ({', '.join(strategies)}) 测试通过")

    @pytest.mark.asyncio
    async def test_metadata_enhanced(self):
        """测试 9: 元数据增强"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            test_doc = "这是一段测试元数据的文档。"
            metadata = {
                "source": "test_metadata",
                "author": "test_author"
            }

            chunks_with_meta = pipeline.chunker.split(test_doc, strategy="semantic", metadata=metadata)
            for chunk, chunk_meta in chunks_with_meta:
                assert chunk_meta["source"] == "test_metadata"
                assert chunk_meta["author"] == "test_author"
                assert "chunk_index" in chunk_meta
                print(f"✓ 元数据增强正确: {chunk_meta}")

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_mocked(self):
        """测试 10: 完整端到端工作流（Mock 模式）"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
            mock_embedder.embed = AsyncMock(return_value=[0.4, 0.5])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            mock_searcher.search = AsyncMock(return_value=[
                SearchResult(content="机器学习是AI的重要分支。", score=0.2, metadata={"id": "ml"}),
                SearchResult(content="深度学习是机器学习的重要方法。", score=0.3, metadata={"id": "dl"}),
            ])
            pipeline.searcher = mock_searcher

            mock_reranker = MagicMock()
            mock_reranker.rerank = AsyncMock(return_value=[
                SearchResult(content="机器学习是AI的重要分支。", score=0.95, metadata={"id": "ml"})
            ])
            pipeline.reranker = mock_reranker

            articles = [
                ("量子计算是一种利用量子力学原理进行计算的技术。", {"title": "量子计算简介"}),
                ("人工智能正在改变我们的生活方式。", {"title": "AI的影响"}),
                ("机器学习算法可以从数据中学习和改进。", {"title": "机器学习基础"}),
            ]

            for doc_text, metadata in articles:
                result = await pipeline.process_document(
                    doc=doc_text,
                    metadata=metadata,
                    file_type="txt",
                    chunk_strategy="semantic"
                )
                assert result is True

            query = "人工智能和机器学习"
            results = await pipeline.search(query, top_k=3)

            assert len(results) > 0
            assert all(isinstance(r, SearchResult) for r in results)

            print(f"✓ 端到端工作流测试成功")
            print(f"  查询: '{query}'")
            print(f"  返回结果数: {len(results)}")

    @pytest.mark.asyncio
    async def test_empty_document_handling(self):
        """测试 11: 空文档处理"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            chunks_with_meta = pipeline.chunker.split("", strategy="semantic", metadata={})
            assert isinstance(chunks_with_meta, list)
            print("✓ 空文档处理正常")

    @pytest.mark.asyncio
    async def test_special_characters_handling(self):
        """测试 12: 特殊字符处理"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            special_doc = """
            测试特殊字符：@#$%^&*()_+-=[]{}|;':",./<>?
            英文标点: !?.,;:'"()
            中文标点：，。！？；：""''（）【】《》
            """

            cleaned = pipeline.washer.wash(special_doc, file_type="txt")
            assert isinstance(cleaned, str)
            print("✓ 特殊字符处理正常")


class TestRAGPipelineIntegration:
    """RAG Pipeline 集成测试（需要实际服务）"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试设置"""
        self.settings = get_settings()
        yield

    def test_embedder_config(self):
        """测试 13: Embedder 配置验证"""
        settings = get_settings()
        assert settings.embedding_model is not None
        print(f"✓ Embedder 配置: model={settings.embedding_model}, use_local={settings.use_local_embedding}")

    def test_vector_db_config(self):
        """测试 14: Vector DB 配置验证"""
        settings = get_settings()
        assert settings.vector_db_path is not None
        print(f"✓ Vector DB 配置: path={settings.vector_db_path}")

    @pytest.mark.asyncio
    async def test_washer_markdown(self):
        """测试 15: Markdown 清洗"""
        pipeline = RAGPipeline()

        markdown_doc = """
        # 人工智能简介

        ## 什么是人工智能

        **人工智能**（AI）是计算机科学的一个分支。

        - 机器学习
        - 深度学习
        - 自然语言处理
        """

        cleaned = pipeline.washer.wash(markdown_doc, file_type="markdown")
        assert "#" not in cleaned
        assert "**" not in cleaned
        assert "[" not in cleaned or "(" not in cleaned
        print("✓ Markdown 清洗功能正常")


class TestRAGPipelineEdgeCases:
    """边界情况测试"""

    def test_search_result_dataclass(self):
        """测试 16: SearchResult 数据类"""
        result = SearchResult(
            content="测试内容",
            score=0.95,
            metadata={"source": "test"}
        )

        assert result.content == "测试内容"
        assert result.score == 0.95
        assert result.metadata == {"source": "test"}
        assert isinstance(result, SearchResult)
        print("✓ SearchResult 数据类正常")

    def test_pipeline_components_exist(self):
        """测试 17: Pipeline 组件存在性"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            assert hasattr(pipeline, 'washer')
            assert hasattr(pipeline, 'chunker')
            assert hasattr(pipeline, 'embedder')
            assert hasattr(pipeline, 'searcher')
            assert hasattr(pipeline, 'reranker')

            assert callable(pipeline.washer.wash)
            assert callable(pipeline.chunker.split)
            print("✓ Pipeline 组件完整性检查通过")


def run_e2e_tests():
    """运行端到端测试的主函数"""
    print("=" * 60)
    print("RAG Pipeline 端到端测试")
    print("=" * 60)
    print()

    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
    ]

    exit_code = pytest.main(pytest_args)

    print()
    print("=" * 60)
    if exit_code == 0:
        print("✓ 所有端到端测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return exit_code


if __name__ == "__main__":
    exit(run_e2e_tests())
