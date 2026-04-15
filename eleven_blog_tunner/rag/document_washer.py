"""
文档清洗模块
"""
import re


class DocumentWasher:
    """文档清洗器"""
    
    def wash(self, doc: str) -> str:
        """
        清洗文档
        - 去除多余空白
        - 标准化换行
        - 去除特殊字符
        """
        # 去除多余空白
        doc = re.sub(r'\s+', ' ', doc)
        # 标准化换行
        doc = re.sub(r'\n+', '\n', doc)
        # 去除首尾空白
        doc = doc.strip()
        return doc
