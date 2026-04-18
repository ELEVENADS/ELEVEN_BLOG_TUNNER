"""
RAG 集成测试
测试 RAG 模块各组件的集成功能
"""
import asyncio
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from eleven_blog_tunner.rag.pipeline import RAGPipeline
from eleven_blog_tunner.rag.searcher import SearchResult
from eleven_blog_tunner.core.config import get_settings


class TestRAGIntegration:
    """RAG 集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试设置"""
        self.settings = get_settings()
        self.test_vector_db_path = "./data/test_vector_db_integration"
        yield
        self._cleanup()

    def _cleanup(self):
        """清理测试数据"""
        if Path(self.test_vector_db_path).exists():
            shutil.rmtree(self.test_vector_db_path, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_full_rag_pipeline(self):
        """测试 1: 完整 RAG 管道集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # Mock 外部依赖
            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
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

            # 测试文档处理
            test_doc = """
            人工智能是计算机科学的一个分支，旨在创造智能机器。
            机器学习是人工智能的一个子领域。
            深度学习是机器学习的一个分支。
            """

            process_result = await pipeline.process_document(
                doc=test_doc,
                metadata={"source": "test_integration", "category": "AI"},
                file_type="txt",
                chunk_strategy="semantic"
            )

            assert process_result is True
            mock_embedder.embed_batch.assert_called_once()
            mock_searcher.index.assert_called_once()

            # 测试搜索
            search_results = await pipeline.search("人工智能", top_k=3)

            assert len(search_results) == 1
            assert all(isinstance(r, SearchResult) for r in search_results)
            mock_embedder.embed.assert_called_once_with("人工智能")
            mock_searcher.search.assert_called_once()
            mock_reranker.rerank.assert_called_once()

            print("✓ 完整 RAG 管道集成测试通过")

    @pytest.mark.asyncio
    async def test_all_components_integration(self):
        """测试 2: 所有组件集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # 测试文档清洗
            test_markdown = """
            # 标题
            **粗体** and *斜体*
            [链接](http://example.com)
            `代码`
            """
            cleaned = pipeline.washer.wash(test_markdown, file_type="markdown")
            assert "标题" in cleaned
            assert "**" not in cleaned

            # 测试分块
            test_doc = """
            第一段内容。
            第二段内容。
            第三段内容。
            """
            chunks_with_meta = pipeline.chunker.split(test_doc, strategy="semantic", metadata={"source": "test"})
            assert len(chunks_with_meta) > 0
            assert all(isinstance(chunk, str) and isinstance(meta, dict) for chunk, meta in chunks_with_meta)

            # 测试元数据处理
            for chunk, meta in chunks_with_meta:
                assert "source" in meta
                assert "chunk_index" in meta

            print("✓ 所有组件集成测试通过")

    @pytest.mark.asyncio
    async def test_pipeline_config_integration(self):
        """测试 3: 配置集成"""
        settings = get_settings()
        
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # 验证配置传递
            assert hasattr(pipeline.chunker, 'chunk_size')
            assert hasattr(pipeline.chunker, 'chunk_overlap')
            assert pipeline.chunker.chunk_size == settings.chunk_size
            assert pipeline.chunker.chunk_overlap == settings.chunk_overlap

            # 验证 Reranker 配置
            assert hasattr(pipeline.reranker, 'model_name')

            print("✓ 配置集成测试通过")

    @pytest.mark.asyncio
    async def test_document_types_integration(self):
        """测试 4: 不同文档类型集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # Mock 外部依赖
            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            mock_searcher.search = AsyncMock(return_value=[])
            pipeline.searcher = mock_searcher

            # 测试不同文件类型
            document_types = [
                ("txt", "纯文本内容"),
                ("markdown", "# Markdown 标题\n**粗体**内容"),
            ]

            for file_type, content in document_types:
                result = await pipeline.process_document(
                    doc=content,
                    metadata={"file_type": file_type},
                    file_type=file_type
                )
                assert result is True
                print(f"  - {file_type} 文档处理成功")

            print("✓ 不同文档类型集成测试通过")

    @pytest.mark.asyncio
    async def test_chunking_strategies_integration(self):
        """测试 5: 分块策略集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # Mock 外部依赖
            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            mock_searcher.search = AsyncMock(return_value=[])
            pipeline.searcher = mock_searcher

            # 测试不同分块策略
            strategies = ["semantic", "recursive", "fixed"]
            test_doc = """
            第一段内容。这是一个比较长的段落，用于测试分块功能。
            第二段内容。这里继续添加一些文本，确保文档足够长。
            第三段内容。测试分块是否能正确处理多个段落。
            """

            for strategy in strategies:
                result = await pipeline.process_document(
                    doc=test_doc,
                    metadata={"strategy": strategy},
                    chunk_strategy=strategy
                )
                assert result is True
                print(f"  - {strategy} 分块策略成功")

            print("✓ 分块策略集成测试通过")

    @pytest.mark.asyncio
    async def test_metadata_flow_integration(self):
        """测试 6: 元数据流程集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # Mock 外部依赖
            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2]])
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            # 模拟搜索结果包含元数据
            mock_searcher.search = AsyncMock(return_value=[
                SearchResult(
                    content="测试内容",
                    score=0.95,
                    metadata={"source": "test", "author": "test_author"}
                )
            ])
            pipeline.searcher = mock_searcher

            mock_reranker = MagicMock()
            mock_reranker.rerank = AsyncMock(side_effect=lambda query, candidates, top_k: candidates)
            pipeline.reranker = mock_reranker

            # 测试元数据传递
            metadata = {
                "source": "test_integration",
                "author": "test_author",
                "custom_field": "custom_value"
            }

            await pipeline.process_document(
                doc="测试文档",
                metadata=metadata
            )

            # 验证元数据被传递到 searcher.index
            call_args = mock_searcher.index.call_args
            assert call_args is not None
            chunks, embeddings, metadatas = call_args[0]
            assert len(metadatas) > 0
            for meta in metadatas:
                assert "source" in meta
                assert "author" in meta
                assert "custom_field" in meta

            # 测试搜索时元数据返回
            results = await pipeline.search("测试")
            assert len(results) > 0
            result_metadata = results[0].metadata
            assert "source" in result_metadata
            assert "author" in result_metadata

            print("✓ 元数据流程集成测试通过")

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """测试 7: 错误处理集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # 测试空文档
            result = await pipeline.process_document(doc="")
            assert result is False  # 空文档应该返回 False

            print("✓ 错误处理集成测试通过")

    @pytest.mark.asyncio
    async def test_search_workflow_integration(self):
        """测试 8: 搜索工作流集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # Mock 外部依赖
            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
            mock_embedder.embed = AsyncMock(return_value=[0.4, 0.5])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            mock_searcher.search = AsyncMock(return_value=[
                SearchResult(content="机器学习是AI的重要分支。", score=0.2, metadata={"id": "ml"}),
                SearchResult(content="深度学习是机器学习的重要方法。", score=0.3, metadata={"id": "dl"}),
                SearchResult(content="人工智能正在改变我们的生活。", score=0.1, metadata={"id": "ai"}),
            ])
            pipeline.searcher = mock_searcher

            mock_reranker = MagicMock()
            mock_reranker.rerank = AsyncMock(side_effect=lambda query, candidates, top_k: candidates[:top_k])
            pipeline.reranker = mock_reranker

            # 测试文档处理
            documents = [
                ("人工智能是计算机科学的一个分支。", {"topic": "AI"}),
                ("机器学习是人工智能的核心技术。", {"topic": "ML"}),
                ("深度学习是机器学习的重要方法。", {"topic": "DL"}),
            ]

            for content, metadata in documents:
                result = await pipeline.process_document(
                    doc=content,
                    metadata=metadata
                )
                assert result is True

            # 测试搜索流程
            query = "人工智能和机器学习"
            results = await pipeline.search(query, top_k=2)

            assert len(results) == 2
            assert all(isinstance(r, SearchResult) for r in results)
            assert all(hasattr(r, 'content') for r in results)
            assert all(hasattr(r, 'score') for r in results)
            assert all(hasattr(r, 'metadata') for r in results)

            print(f"✓ 搜索工作流集成测试通过")
            print(f"  查询: '{query}'")
            print(f"  返回结果数: {len(results)}")

    @pytest.mark.asyncio
    async def test_end_to_end_integration(self):
        """测试 9: 端到端集成"""
        with patch('eleven_blog_tunner.rag.reranker.Reranker._load_model'):
            pipeline = RAGPipeline()

            # Mock 外部依赖
            mock_embedder = MagicMock()
            mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2]] * 5)
            mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2])
            pipeline.embedder = mock_embedder

            mock_searcher = MagicMock()
            mock_searcher.index = AsyncMock()
            mock_searcher.search = AsyncMock(return_value=[
                SearchResult(
                    content="量子计算是一种利用量子力学原理进行计算的技术。",
                    score=0.9,
                    metadata={"title": "量子计算简介", "category": "技术"}
                )
            ])
            pipeline.searcher = mock_searcher

            mock_reranker = MagicMock()
            mock_reranker.rerank = AsyncMock(side_effect=lambda query, candidates, top_k: candidates)
            pipeline.reranker = mock_reranker

            # 模拟真实使用场景
            articles = [
                ("量子计算是一种利用量子力学原理进行计算的技术。",
                 {"title": "量子计算简介", "category": "技术"}),
                ("人工智能正在改变我们的生活方式和工作方式。",
                 {"title": "AI的影响", "category": "科技"}),
                ("机器学习算法可以从数据中学习和改进。",
                 {"title": "机器学习基础", "category": "教育"}),
                ("深度学习在图像识别和自然语言处理方面取得突破。",
                 {"title": "深度学习应用", "category": "技术"}),
                ("区块链技术提供了去中心化的数据存储方案。",
                 {"title": "区块链概述", "category": "金融科技"}),
            ]

            # 处理所有文档
            for content, metadata in articles:
                result = await pipeline.process_document(
                    doc=content,
                    metadata=metadata,
                    file_type="txt",
                    chunk_strategy="semantic"
                )
                assert result is True

            # 执行搜索
            queries = [
                "量子计算",
                "人工智能",
                "机器学习",
                "深度学习",
                "区块链"
            ]

            for query in queries:
                results = await pipeline.search(query, top_k=3)
                assert isinstance(results, list)
                print(f"  - 查询 '{query}' 返回 {len(results)} 个结果")

            print("✓ 端到端集成测试通过")


def run_integration_tests():
    """运行集成测试的主函数"""
    print("=" * 60)
    print("RAG 集成测试")
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
        print("✓ 所有集成测试通过!")
    else:
        print("✗ 部分集成测试失败")
    print("=" * 60)

    return exit_code


if __name__ == "__main__":
    exit(run_integration_tests())
