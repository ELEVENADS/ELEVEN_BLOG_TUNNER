"""
Writer Agent 模块

负责文章的撰写，通过固定的风格和例子调用工具完成文章。
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType


class WriterAgent(BaseAgent):
    """
    Writer Agent

    负责文章的撰写：
    - 根据风格配置撰写文章
    - 调用工具获取素材
    - 生成结构化文章
    - 润色和优化内容
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="WriterAgent",
            description="负责文章的撰写，通过固定的风格和例子调用工具完成文章",
            agent_type=AgentType.WRITER,
            llm_provider=llm_provider,
            use_memory=use_memory
        )
        self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        self.add_tool("generate_outline", self._generate_outline)
        self.add_tool("write_section", self._write_section)
        self.add_tool("polish_content", self._polish_content)
        self.add_tool("search_reference", self._search_reference)

    async def execute(self, context: AgentContext) -> str:
        """执行写作任务

        Args:
            context: Agent 上下文

        Returns:
            撰写结果
        """
        if not self.validate_context(context):
            return "错误: 无效的上下文"

        user_input = context.user_input

        style_config = context.metadata.get("style_config", {})
        context_analysis = context.metadata.get("context_analysis", "")

        result = await self._write_article(
            topic=user_input,
            style_config=style_config,
            context_analysis=context_analysis
        )

        return result

    async def _write_article(
        self,
        topic: str,
        style_config: Dict[str, Any],
        context_analysis: str
    ) -> str:
        """撰写文章

        Args:
            topic: 文章主题
            style_config: 风格配置
            context_analysis: 上下文分析

        Returns:
            完成的文章
        """
        try:
            outline = await self._generate_article_outline(topic, style_config)

            sections = []
            for section in outline:
                section_content = await self._write_section_content(
                    section=section,
                    topic=topic,
                    style_config=style_config
                )
                sections.append(section_content)

            article = "\n\n".join(sections)

            polished_article = await self._polish_article(
                article=article,
                style_config=style_config
            )

            return polished_article

        except Exception as e:
            return f"文章撰写失败: {str(e)}"

    async def _generate_article_outline(
        self,
        topic: str,
        style_config: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """生成文章大纲

        Args:
            topic: 文章主题
            style_config: 风格配置

        Returns:
            文章大纲
        """
        try:
            outline = await self.call_tool(
                "generate_outline",
                topic=topic,
                style=style_config
            )

            return outline

        except Exception:
            return [
                {"title": "引言", "description": "介绍主题背景"},
                {"title": "主要内容", "description": "详细论述"},
                {"title": "总结", "description": "总结要点"}
            ]

    async def _write_section_content(
        self,
        section: Dict[str, str],
        topic: str,
        style_config: Dict[str, Any]
    ) -> str:
        """撰写章节内容

        Args:
            section: 章节信息
            topic: 文章主题
            style_config: 风格配置

        Returns:
            章节内容
        """
        try:
            content = await self.call_tool(
                "write_section",
                section=section,
                topic=topic,
                style=style_config
            )

            return content

        except Exception:
            return f"## {section.get('title', '无标题')}\n\n{section.get('description', '')}"

    async def _polish_article(
        self,
        article: str,
        style_config: Dict[str, Any]
    ) -> str:
        """润色文章

        Args:
            article: 原始文章
            style_config: 风格配置

        Returns:
            润色后的文章
        """
        try:
            polished = await self.call_tool(
                "polish_content",
                article=article,
                style=style_config
            )

            return polished

        except Exception:
            return article

    async def _search_reference(self, query: str) -> List[str]:
        """搜索参考资料

        Args:
            query: 查询内容

        Returns:
            参考资料列表
        """
        try:
            references = await self.call_tool("search_reference", query=query)

            return references

        except Exception:
            return []

    def _generate_outline(
        self,
        topic: str,
        style: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """生成大纲

        Args:
            topic: 主题
            style: 风格配置

        Returns:
            大纲列表
        """
        writing_style = style.get("writing_style", "简洁")

        if "简洁" in writing_style:
            return [
                {"title": "引言", "description": "简洁介绍主题", "word_count": "200字"},
                {"title": "核心观点", "description": "重点论述", "word_count": "500字"},
                {"title": "总结", "description": "简洁总结", "word_count": "150字"}
            ]
        else:
            return [
                {"title": "引言", "description": "详细介绍背景", "word_count": "300字"},
                {"title": "论点一", "description": "第一个论点", "word_count": "400字"},
                {"title": "论点二", "description": "第二个论点", "word_count": "400字"},
                {"title": "结论", "description": "总结与建议", "word_count": "250字"}
            ]

    def _write_section(
        self,
        section: Dict[str, str],
        topic: str,
        style: Dict[str, Any]
    ) -> str:
        """写章节

        Args:
            section: 章节信息
            topic: 主题
            style: 风格配置

        Returns:
            章节内容
        """
        title = section.get("title", "无标题")
        description = section.get("description", "")

        return f"## {title}\n\n{description}\n\n根据\"{topic}\"的要求，本章节详细描述了相关内容。"

    def _polish_content(self, article: str, style: Dict[str, Any]) -> str:
        """润色内容

        Args:
            article: 文章内容
            style: 风格配置

        Returns:
            润色后的内容
        """
        writing_style = style.get("writing_style", "简洁专业")

        if "简洁" in writing_style:
            return article
        else:
            return article

    def _search_reference(self, query: str) -> List[str]:
        """搜索参考

        Args:
            query: 查询

        Returns:
            参考列表
        """
        return [
            f"参考文章1: 关于{query}的研究",
            f"参考文章2: {query}的最佳实践"
        ]

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 WriterAgent，是博客写作系统的文章撰写专家。

你的职责：
1. 根据风格配置撰写高质量文章
2. 生成清晰的结构化内容
3. 调用工具获取素材和参考资料
4. 润色和优化文章内容

写作原则：
1. 严格遵循指定的风格配置
2. 内容准确、结构清晰
3. 语言流畅、表达清晰
4. 注重可读性和专业性

文章结构：
1. 引言 - 吸引读者，介绍主题
2. 主体 - 详细论述，逻辑清晰
3. 结论 - 总结要点，提出建议

始终保持专业的写作态度，创造高质量的博客内容。"""
