"""
笔记导入模块
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from eleven_blog_tunner.rag.pipeline import RAGPipeline


class NoteImporter:
    """笔记导入器"""
    
    def __init__(self):
        self.pipeline = RAGPipeline()
    
    async def import_note(self, file_path: str, metadata: Dict[str, Any] = None) -> bool:
        """
        导入笔记
        
        Args:
            file_path: 文件路径
            metadata: 元数据
        
        Returns:
            是否导入成功
        """
        try:
            # 检测文件类型
            file_type = self._detect_file_type(file_path)
            if not file_type:
                print(f"不支持的文件类型: {file_path}")
                return False
            
            # 读取文件内容
            content = self._read_file(file_path, file_type)
            if not content:
                print(f"文件读取失败: {file_path}")
                return False
            
            # 生成元数据
            if metadata is None:
                metadata = {}
            metadata['file_name'] = os.path.basename(file_path)
            metadata['file_path'] = file_path
            metadata['file_size'] = os.path.getsize(file_path)
            
            # 处理文档
            result = await self.pipeline.process_document(
                doc=content,
                metadata=metadata,
                file_type=file_type
            )
            
            return result
        except Exception as e:
            print(f"导入笔记失败: {e}")
            return False
    
    def _detect_file_type(self, file_path: str) -> Optional[str]:
        """
        检测文件类型
        """
        ext = Path(file_path).suffix.lower()
        if ext in ['.md', '.markdown']:
            return 'markdown'
        elif ext in ['.txt']:
            return 'txt'
        elif ext in ['.pdf']:
            return 'pdf'
        else:
            return None
    
    def _read_file(self, file_path: str, file_type: str) -> str:
        """
        读取文件内容
        """
        try:
            if file_type == 'pdf':
                return self._read_pdf(file_path)
            else:
                # 读取文本文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return ""
    
    def _read_pdf(self, file_path: str) -> str:
        """
        读取 PDF 文件
        """
        try:
            import PyPDF2
            content = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    content += page.extract_text() + "\n"
            return content
        except ImportError:
            print("PyPDF2 未安装，无法读取 PDF 文件")
            return ""
        except Exception as e:
            print(f"读取 PDF 失败: {e}")
            return ""
    
    async def import_directory(self, directory: str, metadata: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        导入目录中的所有笔记
        
        Args:
            directory: 目录路径
            metadata: 元数据
        
        Returns:
            导入结果字典 {文件路径: 是否成功}
        """
        results = {}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                result = await self.import_note(file_path, metadata)
                results[file_path] = result
        
        return results