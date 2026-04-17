import pytest
from eleven_blog_tunner.rag.chunker import Chunker


class TestChunker:
    """Chunker 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.chunker = Chunker(chunk_size=100, chunk_overlap=20)

    def test_fixed_split_basic(self):
        """测试固定长度分块基本功能"""
        text = "这" * 150
        chunks = self.chunker.split(text, strategy="fixed")
        
        assert len(chunks) == 2
        # 由于有重叠，实际块长度可能不同
        assert len(chunks[0][0]) <= 100
        assert len(chunks[1][0]) <= 100

    def test_fixed_split_with_metadata(self):
        """测试固定长度分块返回元数据"""
        text = "这" * 150
        chunks = self.chunker.split(text, strategy="fixed", metadata={"source": "test"})
        
        assert len(chunks) == 2
        for chunk, metadata in chunks:
            assert "source" in metadata
            assert metadata["source"] == "test"
            assert "chunk_index" in metadata
            assert "chunk_length" in metadata

    def test_semantic_split_paragraphs(self):
        """测试语义分块按段落分割"""
        text = "第一段内容\n\n第二段内容\n\n第三段内容"
        chunks = self.chunker.split(text, strategy="semantic")
        
        assert len(chunks) >= 1
        for chunk, metadata in chunks:
            assert "paragraph_index" in metadata

    def test_semantic_split_preserves_content(self):
        """测试语义分块保留内容"""
        text = "这是第一段的内容。\n\n这是第二段的内容。"
        chunks = self.chunker.split(text, strategy="semantic")
        
        content = "".join(chunk for chunk, _ in chunks)
        assert "第一段" in content
        assert "第二段" in content

    def test_recursive_split_basic(self):
        """测试递归分块基本功能"""
        text = "这是测试文本" * 50
        chunks = self.chunker.split(text, strategy="recursive")
        
        assert len(chunks) >= 1
        for chunk, metadata in chunks:
            assert len(chunk) <= self.chunker.chunk_size + 50

    def test_recursive_split_short_text(self):
        """测试递归分块处理短文本"""
        text = "短文本"
        chunks = self.chunker.split(text, strategy="recursive")
        
        assert len(chunks) == 1
        assert chunks[0][0] == "短文本"

    def test_chunk_metadata_positions(self):
        """测试块元数据包含位置信息"""
        text = "这是测试内容" * 20
        chunks = self.chunker.split(text, strategy="fixed", metadata={"source": "test"})
        
        for i, (chunk, metadata) in enumerate(chunks):
            assert metadata["chunk_index"] == i
            assert "start_pos" in metadata
            assert "end_pos" in metadata
            assert metadata["start_pos"] < metadata["end_pos"]

    def test_chunk_index_sequential(self):
        """测试块索引是连续的"""
        text = "测试内容" * 50
        chunks = self.chunker.split(text, strategy="fixed")
        
        indices = [metadata["chunk_index"] for _, metadata in chunks]
        assert indices == list(range(len(chunks)))

    def test_small_text_no_split(self):
        """测试小于块大小的文本不分割"""
        text = "短文本"
        chunks = self.chunker.split(text, strategy="semantic")
        
        assert len(chunks) == 1

    def test_empty_text(self):
        """测试空文本"""
        chunks = self.chunker.split("", strategy="fixed")
        assert len(chunks) == 0
