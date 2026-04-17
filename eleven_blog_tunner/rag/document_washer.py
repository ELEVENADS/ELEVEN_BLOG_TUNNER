"""
文档清洗模块
"""
import re
from typing import Optional


class DocumentWasher:
    """文档清洗器"""
    
    def wash(self, doc: str, file_type: str = "txt") -> str:
        """
        清洗文档
        - 去除多余空白
        - 标准化换行
        - 去除特殊字符
        - 支持不同文件格式
        """
        if file_type == "markdown":
            doc = self._wash_markdown(doc)
        elif file_type == "pdf":
            doc = self._wash_pdf(doc)
        
        # 通用清洗
        # 去除多余空白
        doc = re.sub(r'\s+', ' ', doc)
        # 标准化换行
        doc = re.sub(r'\n+', '\n', doc)
        # 去除首尾空白
        doc = doc.strip()
        return doc
    
    def _wash_markdown(self, doc: str) -> str:
        """
        清洗 Markdown 文档
        - 保留文本内容
        - 去除 Markdown 标记
        """
        # 去除标题标记
        doc = re.sub(r'^#{1,6}\s+', '', doc, flags=re.MULTILINE)
        # 去除粗体和斜体
        doc = re.sub(r'\*\*(.*?)\*\*', r'\1', doc)
        doc = re.sub(r'\*(.*?)\*', r'\1', doc)
        # 去除代码块
        doc = re.sub(r'```[\s\S]*?```', '', doc)
        # 去除行内代码
        doc = re.sub(r'`(.*?)`', r'\1', doc)
        # 去除链接
        doc = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', doc)
        # 去除图片
        doc = re.sub(r'!\[(.*?)\]\(.*?\)', '', doc)
        # 去除列表标记
        doc = re.sub(r'^[\*\-\+]\s+', '', doc, flags=re.MULTILINE)
        doc = re.sub(r'^\d+\.\s+', '', doc, flags=re.MULTILINE)
        return doc
    
    def _wash_pdf(self, doc: str) -> str:
        """
        清洗 PDF 文档
        - 去除多余空行
        - 去除页眉页脚
        - 去除页码
        """
        # 去除页码
        doc = re.sub(r'^\s*\d+\s*$', '', doc, flags=re.MULTILINE)
        # 去除页眉页脚（简单处理）
        lines = doc.split('\n')
        cleaned_lines = []
        for line in lines:
            # 跳过可能的页眉页脚
            if len(line.strip()) < 50:
                # 简单判断：短行可能是页眉页脚
                continue
            cleaned_lines.append(line)
        doc = '\n'.join(cleaned_lines)
        return doc
