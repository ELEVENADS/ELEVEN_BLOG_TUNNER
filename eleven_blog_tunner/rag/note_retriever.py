"""
笔记检索服务

提供基于主题检索相关笔记内容的功能，支持多种检索策略
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from eleven_blog_tunner.rag.pipeline import RAGPipeline
from eleven_blog_tunner.rag.searcher import SearchResult
from eleven_blog_tunner.common.models import Note, get_db_session
from eleven_blog_tunner.utils.logger import logger_instance as logger


class RetrievalStrategy(Enum):
    """检索策略"""
    VECTOR = "vector"           # 向量相似度检索
    KEYWORD = "keyword"         # 关键词匹配
    HYBRID = "hybrid"           # 混合检索
    SELECTED = "selected"       # 用户指定笔记


@dataclass
class NoteChunk:
    """笔记片段"""
    content: str
    note_id: str
    note_title: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class RetrievalResult:
    """检索结果"""
    chunks: List[NoteChunk]
    total_notes: int
    strategy: RetrievalStrategy
    query: str


class NoteRetriever:
    """笔记检索器
    
    负责根据主题检索相关笔记内容，支持：
    1. 向量相似度检索（语义匹配）
    2. 关键词匹配
    3. 混合检索
    4. 用户指定笔记检索
    """
    
    def __init__(self):
        self.rag_pipeline = RAGPipeline()
    
    async def retrieve_by_topic(
        self,
        topic: str,
        top_k: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        user_id: Optional[str] = None
    ) -> RetrievalResult:
        """
        根据主题检索相关笔记内容
        
        Args:
            topic: 文章主题/关键词
            top_k: 返回的片段数量
            strategy: 检索策略
            user_id: 用户ID（用于过滤用户笔记）
            
        Returns:
            检索结果
        """
        logger.info(f"[NoteRetriever] 开始检索笔记: topic={topic}, strategy={strategy.value}")
        
        if strategy == RetrievalStrategy.VECTOR:
            return await self._vector_retrieval(topic, top_k, user_id)
        elif strategy == RetrievalStrategy.KEYWORD:
            return await self._keyword_retrieval(topic, top_k, user_id)
        elif strategy == RetrievalStrategy.HYBRID:
            return await self._hybrid_retrieval(topic, top_k, user_id)
        else:
            raise ValueError(f"不支持的检索策略: {strategy}")
    
    async def retrieve_by_notes(
        self,
        note_ids: List[str],
        topic: Optional[str] = None
    ) -> RetrievalResult:
        """
        根据指定笔记ID检索内容
        
        Args:
            note_ids: 笔记ID列表
            topic: 可选的主题（用于内容筛选）
            
        Returns:
            检索结果
        """
        logger.info(f"[NoteRetriever] 检索指定笔记: note_ids={note_ids}")
        
        chunks = []
        db = get_db_session()
        
        try:
            for note_id in note_ids:
                note = db.query(Note).filter(Note.id == note_id).first()
                if note and note.content:
                    # 如果提供了主题，进行相关性筛选
                    if topic:
                        # 简单分段，取相关段落
                        relevant_chunks = self._extract_relevant_chunks(
                            note.content, 
                            topic,
                            max_chunks=3
                        )
                        for chunk in relevant_chunks:
                            chunks.append(NoteChunk(
                                content=chunk,
                                note_id=str(note.id),
                                note_title=note.title,
                                score=1.0,  # 用户指定笔记默认高相关度
                                metadata={
                                    "source": "user_selected",
                                    "note_id": str(note.id),
                                    "note_title": note.title
                                }
                            ))
                    else:
                        # 使用整个笔记内容
                        chunks.append(NoteChunk(
                            content=note.content[:5000],  # 限制长度
                            note_id=str(note.id),
                            note_title=note.title,
                            score=1.0,
                            metadata={
                                "source": "user_selected",
                                "note_id": str(note.id),
                                "note_title": note.title
                            }
                        ))
        finally:
            db.close()
        
        return RetrievalResult(
            chunks=chunks,
            total_notes=len(note_ids),
            strategy=RetrievalStrategy.SELECTED,
            query=topic or "用户指定笔记"
        )
    
    async def _vector_retrieval(
        self,
        topic: str,
        top_k: int,
        user_id: Optional[str]
    ) -> RetrievalResult:
        """向量检索"""
        results = await self.rag_pipeline.search(topic, top_k=top_k)
        
        chunks = []
        unique_notes = set()
        
        for result in results:
            metadata = result.metadata or {}
            note_id = metadata.get("note_id", "unknown")
            note_title = metadata.get("note_title", "未命名笔记")
            
            unique_notes.add(note_id)
            
            chunks.append(NoteChunk(
                content=result.content,
                note_id=note_id,
                note_title=note_title,
                score=result.score,
                metadata=metadata
            ))
        
        return RetrievalResult(
            chunks=chunks,
            total_notes=len(unique_notes),
            strategy=RetrievalStrategy.VECTOR,
            query=topic
        )
    
    async def _keyword_retrieval(
        self,
        topic: str,
        top_k: int,
        user_id: Optional[str]
    ) -> RetrievalResult:
        """关键词检索"""
        db = get_db_session()
        chunks = []
        
        try:
            # 提取关键词（简单实现，可以使用更复杂的NLP）
            keywords = [kw.strip() for kw in topic.split() if len(kw.strip()) > 1]
            
            # 查询数据库
            query = db.query(Note).filter(Note.deleted_at.is_(None))
            if user_id:
                query = query.filter(Note.user_id == user_id)
            
            notes = query.all()
            
            for note in notes:
                if not note.content:
                    continue
                
                # 计算关键词匹配度
                match_count = sum(1 for kw in keywords if kw.lower() in note.content.lower())
                
                if match_count > 0:
                    # 提取包含关键词的片段
                    relevant_chunks = self._extract_relevant_chunks(
                        note.content,
                        topic,
                        max_chunks=2
                    )
                    
                    for chunk in relevant_chunks:
                        chunks.append(NoteChunk(
                            content=chunk,
                            note_id=str(note.id),
                            note_title=note.title,
                            score=match_count / len(keywords),
                            metadata={
                                "source": "keyword_match",
                                "note_id": str(note.id),
                                "note_title": note.title,
                                "match_count": match_count
                            }
                        ))
            
            # 按相关度排序并限制数量
            chunks.sort(key=lambda x: x.score, reverse=True)
            chunks = chunks[:top_k]
            
        finally:
            db.close()
        
        unique_notes = set(c.note_id for c in chunks)
        
        return RetrievalResult(
            chunks=chunks,
            total_notes=len(unique_notes),
            strategy=RetrievalStrategy.KEYWORD,
            query=topic
        )
    
    async def _hybrid_retrieval(
        self,
        topic: str,
        top_k: int,
        user_id: Optional[str]
    ) -> RetrievalResult:
        """混合检索（向量+关键词）"""
        # 并行执行两种检索
        import asyncio
        vector_result, keyword_result = await asyncio.gather(
            self._vector_retrieval(topic, top_k=top_k//2, user_id=user_id),
            self._keyword_retrieval(topic, top_k=top_k//2, user_id=user_id)
        )
        
        # 合并结果并去重
        all_chunks = {}
        
        # 添加向量检索结果（权重较高）
        for chunk in vector_result.chunks:
            key = f"{chunk.note_id}_{hash(chunk.content[:100])}"
            if key not in all_chunks:
                all_chunks[key] = NoteChunk(
                    content=chunk.content,
                    note_id=chunk.note_id,
                    note_title=chunk.note_title,
                    score=chunk.score * 1.2,  # 向量检索加权
                    metadata={**chunk.metadata, "source": "hybrid_vector"}
                )
        
        # 添加关键词检索结果
        for chunk in keyword_result.chunks:
            key = f"{chunk.note_id}_{hash(chunk.content[:100])}"
            if key in all_chunks:
                # 如果已存在，提升分数
                existing = all_chunks[key]
                all_chunks[key] = NoteChunk(
                    content=existing.content,
                    note_id=existing.note_id,
                    note_title=existing.note_title,
                    score=max(existing.score, chunk.score * 1.0),
                    metadata={**existing.metadata, "keyword_matched": True}
                )
            else:
                all_chunks[key] = NoteChunk(
                    content=chunk.content,
                    note_id=chunk.note_id,
                    note_title=chunk.note_title,
                    score=chunk.score * 1.0,
                    metadata={**chunk.metadata, "source": "hybrid_keyword"}
                )
        
        # 排序并限制数量
        chunks = sorted(all_chunks.values(), key=lambda x: x.score, reverse=True)[:top_k]
        unique_notes = set(c.note_id for c in chunks)
        
        return RetrievalResult(
            chunks=chunks,
            total_notes=len(unique_notes),
            strategy=RetrievalStrategy.HYBRID,
            query=topic
        )
    
    def _extract_relevant_chunks(
        self,
        content: str,
        topic: str,
        max_chunks: int = 3,
        chunk_size: int = 500
    ) -> List[str]:
        """
        从笔记内容中提取与主题相关的片段
        
        Args:
            content: 笔记内容
            topic: 主题
            max_chunks: 最大片段数
            chunk_size: 片段大小
            
        Returns:
            相关片段列表
        """
        # 简单分段
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 计算每段与主题的相关度（简单关键词匹配）
        topic_keywords = set(topic.lower().split())
        scored_paragraphs = []
        
        for para in paragraphs:
            para_lower = para.lower()
            score = sum(1 for kw in topic_keywords if kw in para_lower)
            if score > 0:
                scored_paragraphs.append((para, score))
        
        # 按相关度排序
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        
        # 返回最相关的片段
        return [p[0][:chunk_size] for p in scored_paragraphs[:max_chunks]]
    
    def format_for_prompt(self, retrieval_result: RetrievalResult) -> str:
        """
        将检索结果格式化为Prompt可用的文本
        
        Args:
            retrieval_result: 检索结果
            
        Returns:
            格式化后的参考内容
        """
        if not retrieval_result.chunks:
            return ""
        
        sections = []
        sections.append(f"# 参考笔记内容（共{retrieval_result.total_notes}篇笔记）\n")
        
        for i, chunk in enumerate(retrieval_result.chunks, 1):
            sections.append(f"## 参考片段 {i}（来自《{chunk.note_title}》）\n")
            sections.append(chunk.content)
            sections.append("\n")
        
        return "\n".join(sections)
