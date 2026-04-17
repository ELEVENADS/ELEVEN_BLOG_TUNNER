import pytest
from eleven_blog_tunner.rag.document_washer import DocumentWasher


class TestDocumentWasher:
    """DocumentWasher 单元测试"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.washer = DocumentWasher()

    def test_wash_basic(self):
        """测试基本清洗功能"""
        dirty_text = "这是    一个   测试   文本"
        result = self.washer.wash(dirty_text)
        assert "    " not in result
        assert "   " not in result

    def test_wash_newlines(self):
        """测试换行标准化"""
        dirty_text = "第一段\n\n\n\n第二段"
        result = self.washer.wash(dirty_text)
        assert result.count('\n') <= 1

    def test_wash_strip(self):
        """测试首尾空白去除"""
        dirty_text = "   测试文本   "
        result = self.washer.wash(dirty_text)
        assert result.strip() == result
        assert result.startswith("测试")
        assert result.endswith("文本")

    def test_wash_markdown(self):
        """测试 Markdown 清洗"""
        markdown_text = """# 这是一个标题

**这是粗体文本**

*这是斜体文本*

[这是一个链接](http://example.com)

- 列表项1
- 列表项2
"""
        result = self.washer.wash(markdown_text, file_type="markdown")
        assert "#" not in result
        assert "**" not in result
        assert "*" not in result
        assert "[" not in result
        assert "!" not in result
        assert "-" not in result
        assert "这是一个标题" in result

    def test_wash_code_blocks(self):
        """测试代码块去除"""
        markdown_text = """这是普通文本

```
def hello():
    print("Hello World")
```

更多普通文本
"""
        result = self.washer.wash(markdown_text, file_type="markdown")
        assert "def hello" not in result
        assert "print" not in result
        assert "Hello World" not in result
        assert "这是普通文本" in result

    def test_wash_inline_code(self):
        """测试行内代码去除"""
        markdown_text = "使用 `print()` 函数输出"
        result = self.washer.wash(markdown_text, file_type="markdown")
        assert "`" not in result
        assert "print()" in result

    def test_wash_txt(self):
        """测试 TXT 文件清洗"""
        txt_text = "   普通   文本   内容   "
        result = self.washer.wash(txt_text, file_type="txt")
        assert result.strip() == result
        assert "   " not in result

    def test_wash_empty(self):
        """测试空文本"""
        result = self.washer.wash("")
        assert result == ""

    def test_wash_chinese(self):
        """测试中文文本"""
        chinese_text = "这是   一个   中文   测试   文本"
        result = self.washer.wash(chinese_text, file_type="txt")
        assert result == "这是 一个 中文 测试 文本"
