"""
Assistant Agent 模块

负责辅助文本生成，包括：
- 文本续写和补充
- 基于选中内容的风格提取
- 智能文本生成建议
- 内容改写和润色
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType


class AssistantAgent(BaseAgent):
    """
    Assistant Agent

    负责辅助文本生成和编辑：
    - 根据上下文续写文本
    - 提取选中内容的风格
    - 生成内容建议
    - 改写和润色文本
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="AssistantAgent",
            description="负责辅助文本生成，包括续写、风格提取、改写润色等",
            agent_type=AgentType.ASSISTANT,
            llm_provider=llm_provider,
            use_memory=use_memory
        )
        self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        self.add_tool("continue_writing", self._continue_writing)
        self.add_tool("extract_selection_style", self._extract_selection_style)
        self.add_tool("rewrite_content", self._rewrite_content)
        self.add_tool("polish_text", self._polish_text)
        self.add_tool("generate_suggestions", self._generate_suggestions)
        self.add_tool("expand_content", self._expand_content)
        self.add_tool("summarize_selection", self._summarize_selection)

    async def execute(self, context: AgentContext) -> str:
        """执行辅助任务

        Args:
            context: Agent 上下文

        Returns:
            执行结果
        """
        if not self.validate_context(context):
            return "错误: 无效的上下文"

        task_type = context.metadata.get("task_type", "continue")
        selected_text = context.metadata.get("selected_text", "")
        surrounding_context = context.metadata.get("context", "")

        if task_type == "continue":
            result = await self._handle_continue_writing(
                selected_text, surrounding_context, context.metadata
            )
        elif task_type == "extract_style":
            result = await self._handle_extract_style(selected_text)
        elif task_type == "rewrite":
            result = await self._handle_rewrite(
                selected_text, context.metadata.get("style", "")
            )
        elif task_type == "polish":
            result = await self._handle_polish(selected_text)
        elif task_type == "suggest":
            result = await self._handle_suggestions(
                selected_text, surrounding_context
            )
        elif task_type == "expand":
            result = await self._handle_expand(
                selected_text, context.metadata.get("target_length", 200)
            )
        elif task_type == "summarize":
            result = await self._handle_summarize(selected_text)
        else:
            result = "未知的任务类型"

        return result

    async def _handle_continue_writing(
        self,
        selected_text: str,
        context: str,
        metadata: Dict[str, Any]
    ) -> str:
        """处理续写任务

        Args:
            selected_text: 选中的文本
            context: 上下文
            metadata: 元数据

        Returns:
            续写内容
        """
        try:
            style_hint = metadata.get("style_hint", "")
            length = metadata.get("length", 200)

            result = await self.call_tool(
                "continue_writing",
                selected_text=selected_text,
                context=context,
                style_hint=style_hint,
                length=length
            )

            return result

        except Exception as e:
            return f"续写失败: {str(e)}"

    async def _handle_extract_style(self, selected_text: str) -> str:
        """处理风格提取任务

        Args:
            selected_text: 选中的文本

        Returns:
            风格描述
        """
        try:
            if not selected_text or len(selected_text) < 50:
                return "选中的文本太短，无法提取风格（至少需要50字符）"

            result = await self.call_tool(
                "extract_selection_style",
                text=selected_text
            )

            return result

        except Exception as e:
            return f"风格提取失败: {str(e)}"

    async def _handle_rewrite(self, text: str, style: str) -> str:
        """处理改写任务

        Args:
            text: 原文本
            style: 目标风格

        Returns:
            改写后的文本
        """
        try:
            result = await self.call_tool(
                "rewrite_content",
                text=text,
                style=style
            )

            return result

        except Exception as e:
            return f"改写失败: {str(e)}"

    async def _handle_polish(self, text: str) -> str:
        """处理润色任务

        Args:
            text: 原文本

        Returns:
            润色后的文本
        """
        try:
            result = await self.call_tool("polish_text", text=text)
            return result

        except Exception as e:
            return f"润色失败: {str(e)}"

    async def _handle_suggestions(self, selected_text: str, context: str) -> str:
        """处理生成建议任务

        Args:
            selected_text: 选中的文本
            context: 上下文

        Returns:
            建议内容
        """
        try:
            result = await self.call_tool(
                "generate_suggestions",
                selected_text=selected_text,
                context=context
            )

            return result

        except Exception as e:
            return f"生成建议失败: {str(e)}"

    async def _handle_expand(self, text: str, target_length: int) -> str:
        """处理扩写任务

        Args:
            text: 原文本
            target_length: 目标长度

        Returns:
            扩写后的文本
        """
        try:
            result = await self.call_tool(
                "expand_content",
                text=text,
                target_length=target_length
            )

            return result

        except Exception as e:
            return f"扩写失败: {str(e)}"

    async def _handle_summarize(self, text: str) -> str:
        """处理总结任务

        Args:
            text: 原文本

        Returns:
            总结内容
        """
        try:
            result = await self.call_tool("summarize_selection", text=text)
            return result

        except Exception as e:
            return f"总结失败: {str(e)}"

    # ========== 工具方法 ==========

    def _continue_writing(
        self,
        selected_text: str,
        context: str,
        style_hint: str,
        length: int
    ) -> str:
        """续写文本

        Args:
            selected_text: 选中的文本
            context: 上下文
            style_hint: 风格提示
            length: 生成长度

        Returns:
            续写内容
        """
        return f"根据上文内容，继续撰写约{length}字的内容，保持与原文风格一致。"

    def _extract_selection_style(self, text: str) -> str:
        """提取选中内容的风格

        Args:
            text: 选中的文本

        Returns:
            风格描述
        """
        return f"""从选中文本提取的风格特征：

**语言风格**：专业、简洁
**句式特点**：长短句结合，节奏明快
**词汇偏好**：使用专业术语，表达准确
**情感倾向**：客观、理性
**独特习惯**：
- 喜欢使用"首先...其次...最后"的结构
- 善用举例说明
- 段落组织清晰

**建议应用**：在续写时保持这种结构清晰、逻辑严谨的写作风格。"""

    def _rewrite_content(self, text: str, style: str) -> str:
        """改写内容

        Args:
            text: 原文本
            style: 目标风格

        Returns:
            改写后的文本
        """
        return f"【改写为{style}风格】\n\n{text}\n\n（此处为改写后的内容示例）"

    def _polish_text(self, text: str) -> str:
        """润色文本

        Args:
            text: 原文本

        Returns:
            润色后的文本
        """
        return f"【润色后】\n\n{text}\n\n（此处为润色后的内容，优化了用词和句式）"

    def _generate_suggestions(self, selected_text: str, context: str) -> str:
        """生成写作建议

        Args:
            selected_text: 选中的文本
            context: 上下文

        Returns:
            建议内容
        """
        return """基于当前内容的写作建议：

1. **内容补充建议**
   - 可以添加具体案例来支撑论点
   - 建议补充数据或统计信息增强说服力

2. **结构优化建议**
   - 当前段落较长，建议拆分为2-3个小段落
   - 可以添加小标题提升可读性

3. **表达优化建议**
   - "XXX" 可以改为更具体的描述
   - 建议减少被动语态的使用

4. **衔接建议**
   - 与下文衔接时，可以使用过渡句
   - 建议添加承上启下的段落"""

    def _expand_content(self, text: str, target_length: int) -> str:
        """扩写内容

        Args:
            text: 原文本
            target_length: 目标长度

        Returns:
            扩写后的文本
        """
        return f"【扩写至约{target_length}字】\n\n{text}\n\n（此处为扩写后的详细内容，增加了细节描述、例子和解释）"

    def _summarize_selection(self, text: str) -> str:
        """总结选中的内容

        Args:
            text: 原文本

        Returns:
            总结内容
        """
        return f"【内容总结】\n\n{text[:100]}...\n\n核心要点：\n1. 主要观点...\n2. 关键论据...\n3. 结论建议..."

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 AssistantAgent，是博客写作系统的智能写作助手。

你的职责：
1. 根据上下文智能续写文本
2. 分析选中内容的写作风格
3. 提供内容改写和润色服务
4. 生成写作建议和优化方案
5. 扩写或总结选中的内容

工作原则：
1. 保持与原文风格一致
2. 内容连贯、逻辑清晰
3. 语言流畅、表达准确
4. 尊重原文意图，不偏离主题

任务类型：
- **续写**：根据上下文继续撰写内容
- **风格提取**：分析选中文本的写作风格
- **改写**：按指定风格改写内容
- **润色**：优化文本表达
- **建议**：提供写作建议
- **扩写**：扩展内容细节
- **总结**：提炼核心要点

始终保持专业的辅助态度，帮助用户提升写作质量。"""
