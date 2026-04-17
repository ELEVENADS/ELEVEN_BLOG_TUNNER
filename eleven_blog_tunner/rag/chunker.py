"""
文档分块模块
"""
from typing import List, Tuple, Dict, Any
import re


class Chunker:
    """文档分块器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split(self, doc: str, strategy: str = "semantic", metadata: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        将文档分块
        
        Args:
            doc: 文档内容
            strategy: 分块策略 ("semantic" | "recursive" | "fixed")
            metadata: 文档元数据
        
        Returns:
            分块内容和对应的元数据
        """
        if strategy == "semantic":
            return self._semantic_split(doc, metadata)
        elif strategy == "recursive":
            return self._recursive_split(doc, metadata)
        else:
            return self._fixed_split(doc, metadata)
    
    def _fixed_split(self, doc: str, metadata: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        固定长度分块
        """
        chunks_with_metadata = []
        start = 0
        chunk_index = 0
        
        while start < len(doc):
            end = start + self.chunk_size
            chunk = doc[start:end]
            
            # 生成块元数据
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = chunk_index
            chunk_metadata['start_pos'] = start
            chunk_metadata['end_pos'] = end
            chunk_metadata['chunk_length'] = len(chunk)
            
            chunks_with_metadata.append((chunk, chunk_metadata))
            start = end - self.chunk_overlap
            chunk_index += 1
        
        return chunks_with_metadata
    
    def _semantic_split(self, doc: str, metadata: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        语义分块
        - 基于段落、句子等语义边界
        """
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', doc)
        chunks_with_metadata = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                current_start += len(paragraph) + 2  # 加2是因为分割符是\n\s*\n
                continue
            
            # 检查添加当前段落是否超过块大小
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                # 如果当前块不为空，添加到结果
                if current_chunk:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata['chunk_index'] = chunk_index
                    chunk_metadata['start_pos'] = current_start
                    chunk_metadata['end_pos'] = current_start + len(current_chunk)
                    chunk_metadata['chunk_length'] = len(current_chunk.strip())
                    chunk_metadata['paragraph_index'] = i - 1
                    chunks_with_metadata.append((current_chunk.strip(), chunk_metadata))
                    chunk_index += 1
                
                # 处理当前段落
                if len(paragraph) > self.chunk_size:
                    # 段落过长，进一步分割
                    sentence_chunks = self._split_by_sentences(paragraph, current_start, metadata, chunk_index)
                    chunks_with_metadata.extend(sentence_chunks)
                    chunk_index += len(sentence_chunks)
                else:
                    current_chunk = paragraph + "\n\n"
                
                current_start += len(paragraph) + 2
        
        # 添加最后一个块
        if current_chunk:
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = chunk_index
            chunk_metadata['start_pos'] = current_start
            chunk_metadata['end_pos'] = current_start + len(current_chunk)
            chunk_metadata['chunk_length'] = len(current_chunk.strip())
            chunk_metadata['paragraph_index'] = len(paragraphs) - 1
            chunks_with_metadata.append((current_chunk.strip(), chunk_metadata))
        
        return chunks_with_metadata
    
    def _split_by_sentences(self, text: str, start_pos: int = 0, metadata: Dict[str, Any] = None, chunk_index: int = 0) -> List[Tuple[str, Dict[str, Any]]]:
        """
        按句子分割文本
        """
        # 按句子分割
        sentences = re.split(r'[。！？.!?]\s*', text)
        chunks_with_metadata = []
        current_chunk = ""
        current_start = start_pos
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                current_start += len(sentence) + 1  # 加1是因为分割符
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata['chunk_index'] = chunk_index + len(chunks_with_metadata)
                    chunk_metadata['start_pos'] = current_start
                    chunk_metadata['end_pos'] = current_start + len(current_chunk)
                    chunk_metadata['chunk_length'] = len(current_chunk)
                    chunk_metadata['sentence_index'] = i - 1
                    chunks_with_metadata.append((current_chunk, chunk_metadata))
                current_chunk = sentence + "。"
                current_start += len(sentence) + 1
        
        if current_chunk:
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = chunk_index + len(chunks_with_metadata)
            chunk_metadata['start_pos'] = current_start
            chunk_metadata['end_pos'] = current_start + len(current_chunk)
            chunk_metadata['chunk_length'] = len(current_chunk)
            chunk_metadata['sentence_index'] = len(sentences) - 1
            chunks_with_metadata.append((current_chunk, chunk_metadata))
        
        return chunks_with_metadata
    
    def _recursive_split(self, doc: str, metadata: Dict[str, Any] = None, start_pos: int = 0, chunk_index: int = 0) -> List[Tuple[str, Dict[str, Any]]]:
        """
        递归分块
        - 尝试在多个层次上找到最佳分块点
        """
        if len(doc) <= self.chunk_size:
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = chunk_index
            chunk_metadata['start_pos'] = start_pos
            chunk_metadata['end_pos'] = start_pos + len(doc)
            chunk_metadata['chunk_length'] = len(doc)
            return [(doc, chunk_metadata)]
        
        # 尝试在段落边界分割
        paragraphs = re.split(r'\n\s*\n', doc)
        if len(paragraphs) > 1:
            mid = len(paragraphs) // 2
            left = "\n\n".join(paragraphs[:mid])
            right = "\n\n".join(paragraphs[mid:])
            
            left_chunks = self._recursive_split(left, metadata, start_pos, chunk_index)
            right_start = start_pos + len(left) + 2  # 加2是因为分割符
            right_chunks = self._recursive_split(right, metadata, right_start, chunk_index + len(left_chunks))
            return left_chunks + right_chunks
        
        # 尝试在句子边界分割
        sentences = re.split(r'[。！？.!?]\s*', doc)
        if len(sentences) > 1:
            mid = len(sentences) // 2
            left = "。".join(sentences[:mid]) + "。"
            right = "。".join(sentences[mid:])
            if right and not right.endswith(('。', '！', '？', '.', '!', '?')):
                right += "。"
            
            left_chunks = self._recursive_split(left, metadata, start_pos, chunk_index)
            right_start = start_pos + len(left)
            right_chunks = self._recursive_split(right, metadata, right_start, chunk_index + len(left_chunks))
            return left_chunks + right_chunks
        
        # 最后使用固定长度分割
        return self._fixed_split(doc, metadata)
