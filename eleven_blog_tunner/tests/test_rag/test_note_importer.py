import pytest
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from eleven_blog_tunner.rag.note_importer import NoteImporter


class TestNoteImporter:
    """NoteImporter 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.importer = NoteImporter()

    def test_detect_file_type_markdown(self):
        """测试检测 Markdown 文件类型"""
        assert self.importer._detect_file_type("test.md") == "markdown"
        assert self.importer._detect_file_type("test.markdown") == "markdown"

    def test_detect_file_type_txt(self):
        """测试检测 TXT 文件类型"""
        assert self.importer._detect_file_type("test.txt") == "txt"

    def test_detect_file_type_pdf(self):
        """测试检测 PDF 文件类型"""
        assert self.importer._detect_file_type("test.pdf") == "pdf"

    def test_detect_file_type_unsupported(self):
        """测试不支持的文件类型"""
        assert self.importer._detect_file_type("test.doc") is None
        assert self.importer._detect_file_type("test.xlsx") is None

    @pytest.mark.asyncio
    async def test_import_note_success(self):
        """测试成功导入笔记"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_document = AsyncMock(return_value=True)
        
        with patch.object(self.importer, 'pipeline', mock_pipeline):
            with patch('builtins.open', mock_open(read_data="测试内容")):
                with patch('os.path.getsize', return_value=100):
                    with patch('os.path.basename', return_value="test.md"):
                        result = await self.importer.import_note(
                            "/path/to/test.md",
                            metadata={"category": "tech"}
                        )
            
            assert result is True

    @pytest.mark.asyncio
    async def test_import_note_unsupported_type(self):
        """测试导入不支持的文件类型"""
        result = await self.importer.import_note("/path/to/test.doc")
        assert result is False

    def test_read_file_utf8(self):
        """测试读取 UTF-8 文本文件"""
        content = "测试内容"
        m = mock_open(read_data=content)
        
        with patch('builtins.open', m):
            result = self.importer._read_file("/path/to/test.txt", "txt")
            
            assert result == content
            m.assert_called_with("/path/to/test.txt", 'r', encoding='utf-8')

    def test_read_file_with_exception(self):
        """测试文件读取异常"""
        with patch('builtins.open', side_effect=Exception("Read error")):
            result = self.importer._read_file("/path/to/test.txt", "txt")
            
            assert result == ""

    def test_read_pdf_not_installed(self):
        """测试 PDF 库未安装时的处理"""
        with patch('builtins.open', side_effect=ImportError()):
            result = self.importer._read_pdf("/path/to/test.pdf")
            
            assert result == ""

    @pytest.mark.asyncio
    async def test_import_directory_results(self):
        """测试导入目录返回结果"""
        mock_walk = [
            ("/path", [], ["test1.md", "test2.txt"]),
        ]
        
        mock_pipeline = MagicMock()
        mock_pipeline.process_document = AsyncMock(return_value=True)
        
        with patch('os.walk', return_value=mock_walk):
            with patch.object(self.importer, 'pipeline', mock_pipeline):
                with patch('builtins.open', mock_open(read_data="内容")):
                    with patch('os.path.getsize', return_value=100):
                        with patch('os.path.basename', side_effect=lambda x: x.split('/')[-1]):
                            results = await self.importer.import_directory("/path")
            
            assert isinstance(results, dict)
            assert len(results) == 2


class TestNoteImporterIntegration:
    """NoteImporter 集成测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.importer = NoteImporter()

    @pytest.mark.asyncio
    async def test_import_with_metadata(self):
        """测试带元数据导入"""
        mock_pipeline = MagicMock()
        mock_pipeline.process_document = AsyncMock(return_value=True)
        
        with patch.object(self.importer, 'pipeline', mock_pipeline):
            with patch('builtins.open', mock_open(read_data="测试")):
                with patch('os.path.getsize', return_value=50):
                    with patch('os.path.basename', return_value="test.md"):
                        await self.importer.import_note(
                            "/path/test.md",
                            metadata={"author": "test", "tags": ["ai"]}
                        )
            
            call_args = mock_pipeline.process_document.call_args
            assert call_args[1]["metadata"]["author"] == "test"
