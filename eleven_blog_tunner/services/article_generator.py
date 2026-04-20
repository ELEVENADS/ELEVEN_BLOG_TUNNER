"""
文章生成服务

支持两种生成模式：
1. 笔记整合模式（默认）- 基于笔记内容检索和整合生成文章
2. 风格+主题模式 - 基于风格配置和主题生成文章
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json

from eleven_blog_tunner.rag.note_retriever import NoteRetriever, RetrievalStrategy
from eleven_blog_tunner.rag.style_manager import StyleManager
from eleven_blog_tunner.agents.writer_agent import WriterAgent
from eleven_blog_tunner.agents.base_agent import AgentContext
from eleven_blog_tunner.utils.logger import logger_instance as logger


class GenerationMode(Enum):
    """文章生成模式"""
    NOTE_INTEGRATION = "note_integration"    # 笔记整合模式（默认）
    STYLE_TOPIC = "style_topic"                # 风格+主题模式


@dataclass
class ArticleGenerationRequest:
    """文章生成请求"""
    topic: str
    mode: GenerationMode = GenerationMode.NOTE_INTEGRATION
    style_name: Optional[str] = None
    note_ids: Optional[List[str]] = None          # 指定笔记ID列表
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    top_k: int = 10                               # 检索片段数量
    outline: Optional[List[Dict[str, str]]] = None
    target_length: int = 1000
    user_id: Optional[str] = None


@dataclass
class ArticleGenerationResult:
    """文章生成结果"""
    content: str
    mode: GenerationMode
    used_notes: List[Dict[str, Any]]
    style_applied: Optional[str]
    outline: List[Dict[str, str]]
    metadata: Dict[str, Any]


class ArticleGenerator:
    """文章生成器
    
    核心服务，支持两种生成模式：
    1. 笔记整合模式：检索相关笔记内容，整合后生成文章
    2. 风格+主题模式：基于已学习的风格配置生成文章
    """
    
    def __init__(self):
        self.note_retriever = NoteRetriever()
        self.style_manager = StyleManager()
        self.writer_agent = WriterAgent()
    
    async def generate(self, request: ArticleGenerationRequest) -> ArticleGenerationResult:
        """
        生成文章
        
        Args:
            request: 生成请求
            
        Returns:
            生成结果
        """
        logger.info(f"[ArticleGenerator] 开始生成文章: mode={request.mode.value}, topic={request.topic}")
        
        if request.mode == GenerationMode.NOTE_INTEGRATION:
            return await self._generate_by_note_integration(request)
        else:
            return await self._generate_by_style_topic(request)
    
    async def _generate_by_note_integration(
        self,
        request: ArticleGenerationRequest
    ) -> ArticleGenerationResult:
        """
        笔记整合模式生成文章
        
        流程：
        1. 检索相关笔记内容
        2. 整合笔记内容
        3. 应用风格（如果指定）
        4. 生成文章
        """
        logger.info("[ArticleGenerator] 使用笔记整合模式")
        
        # 1. 检索笔记内容
        if request.note_ids:
            # 使用用户指定的笔记
            retrieval_result = await self.note_retriever.retrieve_by_notes(
                note_ids=request.note_ids,
                topic=request.topic
            )
        else:
            # 自动检索相关笔记
            retrieval_result = await self.note_retriever.retrieve_by_topic(
                topic=request.topic,
                top_k=request.top_k,
                strategy=request.retrieval_strategy,
                user_id=request.user_id
            )
        
        logger.info(f"[ArticleGenerator] 检索到 {len(retrieval_result.chunks)} 个片段，来自 {retrieval_result.total_notes} 篇笔记")
        
        # 2. 格式化笔记内容为参考文本
        reference_content = self.note_retriever.format_for_prompt(retrieval_result)
        
        # 3. 获取风格配置（如果指定）
        style_config = {}
        if request.style_name:
            try:
                style_data = await self.style_manager.load_style(request.style_name)
                style_config = style_data.get("features", {})
                logger.info(f"[ArticleGenerator] 应用风格: {request.style_name}")
            except FileNotFoundError:
                logger.warning(f"[ArticleGenerator] 风格不存在: {request.style_name}")
        
        # 4. 构建生成提示
        generation_prompt = self._build_integration_prompt(
            topic=request.topic,
            reference_content=reference_content,
            style_config=style_config,
            target_length=request.target_length
        )
        
        # 5. 生成大纲（如果未提供）
        outline = request.outline
        if not outline:
            outline = await self._generate_outline(
                topic=request.topic,
                reference_content=reference_content,
                style_config=style_config
            )
        
        # 6. 生成文章
        context = AgentContext(
            user_input=generation_prompt,
            metadata={
                "mode": "note_integration",
                "topic": request.topic,
                "style_name": request.style_name,
                "outline": outline,
                "reference_notes": [c.note_title for c in retrieval_result.chunks]
            }
        )
        
        content = await self._generate_content_with_outline(
            outline=outline,
            prompt=generation_prompt,
            style_config=style_config
        )
        
        # 7. 整理使用的笔记信息
        used_notes = []
        seen_notes = set()
        for chunk in retrieval_result.chunks:
            if chunk.note_id not in seen_notes:
                seen_notes.add(chunk.note_id)
                used_notes.append({
                    "id": chunk.note_id,
                    "title": chunk.note_title,
                    "relevance_score": chunk.score
                })
        
        return ArticleGenerationResult(
            content=content,
            mode=GenerationMode.NOTE_INTEGRATION,
            used_notes=used_notes,
            style_applied=request.style_name,
            outline=outline,
            metadata={
                "total_chunks": len(retrieval_result.chunks),
                "retrieval_strategy": retrieval_result.strategy.value,
                "target_length": request.target_length
            }
        )
    
    async def _generate_by_style_topic(
        self,
        request: ArticleGenerationRequest
    ) -> ArticleGenerationResult:
        """
        风格+主题模式生成文章
        
        流程：
        1. 加载风格配置
        2. 生成大纲
        3. 根据风格撰写文章
        """
        logger.info("[ArticleGenerator] 使用风格+主题模式")
        
        # 1. 加载风格
        style_config = {}
        if request.style_name:
            try:
                style_data = await self.style_manager.load_style(request.style_name)
                style_config = style_data.get("features", {})
            except FileNotFoundError:
                logger.warning(f"风格不存在: {request.style_name}")
        
        # 2. 生成大纲
        outline = request.outline
        if not outline:
            outline = await self._generate_outline(
                topic=request.topic,
                reference_content="",
                style_config=style_config
            )
        
        # 3. 构建提示
        prompt = f"""请根据以下主题和风格要求撰写文章。

主题：{request.topic}

风格要求：
{json.dumps(style_config, ensure_ascii=False, indent=2)}

要求：
- 文章长度约 {request.target_length} 字
- 严格遵循指定的写作风格
- 内容结构清晰，逻辑连贯
"""
        
        # 4. 生成文章
        content = await self._generate_content_with_outline(
            outline=outline,
            prompt=prompt,
            style_config=style_config
        )
        
        return ArticleGenerationResult(
            content=content,
            mode=GenerationMode.STYLE_TOPIC,
            used_notes=[],
            style_applied=request.style_name,
            outline=outline,
            metadata={
                "target_length": request.target_length
            }
        )
    
    def _build_integration_prompt(
        self,
        topic: str,
        reference_content: str,
        style_config: Dict[str, Any],
        target_length: int
    ) -> str:
        """构建笔记整合模式的生成提示"""
        
        style_instruction = ""
        if style_config:
            style_instruction = f"""

## 写作风格要求
{json.dumps(style_config, ensure_ascii=False, indent=2)}

请确保生成的文章符合上述风格特征。
"""
        
        prompt = f"""请根据以下参考笔记内容，撰写一篇关于"{topic}"的文章。

{reference_content}

---

## 写作要求

1. **主题**：{topic}
2. **内容来源**：基于上述参考笔记内容进行整合和扩展
3. **文章长度**：约 {target_length} 字
4. **写作原则**：
   - 充分吸收参考笔记的核心观点和关键信息
   - 重新组织结构，形成连贯的文章
   - 保持逻辑清晰，层次分明
   - 可以适当补充和扩展，但要基于参考内容
{style_instruction}

请直接输出完整的文章内容。
"""
        return prompt
    
    async def _generate_outline(
        self,
        topic: str,
        reference_content: str,
        style_config: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """生成文章大纲"""
        
        prompt = f"""请为文章生成大纲。

主题：{topic}

"""
        if reference_content:
            prompt += f"""参考内容：
{reference_content[:2000]}

"""
        
        prompt += """请生成文章大纲，格式为JSON数组：
[
  {"title": "章节标题", "description": "章节内容简介", "word_count": "预计字数"},
  ...
]

要求：
- 包含引言、主体内容、总结
- 每个章节有明确的标题和简介
- 结构清晰，逻辑连贯
"""
        
        try:
            # 使用LLM生成大纲
            messages = [
                {"role": "system", "content": "你是一位专业的文章大纲规划师。"},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.writer_agent.call_llm(messages, temperature=0.7)
            
            # 解析JSON大纲
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                outline = json.loads(json_match.group())
                if isinstance(outline, list):
                    return outline
        except Exception as e:
            logger.error(f"生成大纲失败: {e}")
        
        # 默认大纲
        return [
            {"title": "引言", "description": "介绍主题背景", "word_count": "200字"},
            {"title": "主要内容", "description": "详细论述", "word_count": "600字"},
            {"title": "总结", "description": "总结要点", "word_count": "200字"}
        ]
    
    async def _generate_content_with_outline(
        self,
        outline: List[Dict[str, str]],
        prompt: str,
        style_config: Dict[str, Any]
    ) -> str:
        """根据大纲生成完整文章内容"""
        
        sections = []
        
        # 生成引言
        intro_prompt = f"{prompt}\n\n请先撰写引言部分。"
        intro = await self._generate_section(intro_prompt, style_config)
        sections.append(intro)
        
        # 生成各章节
        for i, section in enumerate(outline):
            section_prompt = f"""{prompt}

正在撰写第 {i+1} 部分：{section['title']}
内容简介：{section.get('description', '')}
预计字数：{section.get('word_count', '适量')}

请撰写这一部分内容："""
            
            section_content = await self._generate_section(section_prompt, style_config)
            sections.append(f"\n## {section['title']}\n\n{section_content}")
        
        # 生成总结
        conclusion_prompt = f"{prompt}\n\n最后，请撰写总结部分。"
        conclusion = await self._generate_section(conclusion_prompt, style_config)
        sections.append(f"\n## 总结\n\n{conclusion}")
        
        return "\n\n".join(sections)
    
    async def _generate_section(self, prompt: str, style_config: Dict[str, Any]) -> str:
        """生成单个章节内容"""
        try:
            messages = [
                {"role": "system", "content": "你是一位专业的文章撰写专家。"},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.writer_agent.call_llm(
                messages,
                temperature=style_config.get("temperature", 0.7)
            )
            
            return response.strip()
        except Exception as e:
            logger.error(f"生成章节失败: {e}")
            return "[内容生成失败]"
