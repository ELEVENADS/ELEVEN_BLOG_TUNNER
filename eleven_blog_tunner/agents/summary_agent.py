"""
Summary Agent 模块

负责总结类工作，比如总结上下文、总结文章风格等。
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType


class SummaryAgent(BaseAgent):
    """
    Summary Agent

    负责总结类工作：
    - 总结上下文
    - 提取文章风格
    - 压缩对话历史
    - 生成内容摘要
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="SummaryAgent",
            description="负责总结类工作，比如总结上下文、总结文章风格",
            agent_type=AgentType.SUMMARY,
            llm_provider=llm_provider,
            use_memory=use_memory
        )
        self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        self.add_tool("summarize_context", self._summarize_context)
        self.add_tool("extract_style", self._extract_style)
        self.add_tool("compress_history", self._compress_history)
        self.add_tool("generate_outline", self._generate_outline)

    async def execute(self, context: AgentContext) -> str:
        """执行总结任务

        Args:
            context: Agent 上下文

        Returns:
            总结结果
        """
        if not self.validate_context(context):
            return "错误: 无效的上下文"

        user_input = context.user_input

        summary_type = self._analyze_summary_type(user_input)

        if summary_type == "context":
            result = await self._summarize_context_text(user_input)
        elif summary_type == "style":
            result = await self._extract_style_from_text(user_input)
        elif summary_type == "history":
            result = await self._compress_context_history(context)
        elif summary_type == "outline":
            result = await self._generate_content_outline(user_input)
        else:
            result = await self._handle_general_summary(user_input)

        return result

    def _analyze_summary_type(self, user_input: str) -> str:
        """分析总结类型

        Args:
            user_input: 用户输入

        Returns:
            总结类型
        """
        user_input_lower = user_input.lower()

        if any(keyword in user_input_lower for keyword in ["上下文", "context", "分析上下文"]):
            return "context"
        elif any(keyword in user_input_lower for keyword in ["风格", "style", "写作风格", "提取风格"]):
            return "style"
        elif any(keyword in user_input_lower for keyword in ["历史", "history", "压缩"]):
            return "history"
        elif any(keyword in user_input_lower for keyword in ["大纲", "outline", "文章结构"]):
            return "outline"
        else:
            return "general"

    async def _summarize_context_text(self, text: str) -> str:
        """总结上下文文本

        Args:
            text: 待总结文本

        Returns:
            总结结果
        """
        try:
            result = await self.call_tool("summarize_context", text=text)

            return result

        except Exception as e:
            return f"上下文总结失败: {str(e)}"

    async def _extract_style_from_text(self, text: str) -> str:
        """从文本提取风格

        Args:
            text: 待分析文本

        Returns:
            风格描述
        """
        try:
            result = await self.call_tool("extract_style", text=text)

            return result

        except Exception as e:
            return f"风格提取失败: {str(e)}"

    async def _compress_context_history(self, context: AgentContext) -> str:
        """压缩上下文历史

        Args:
            context: Agent 上下文

        Returns:
            压缩后的历史
        """
        try:
            history_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in context.history
            ])

            if not history_text:
                return "没有历史记录需要压缩"

            result = await self.call_tool("compress_history", history=history_text)

            return result

        except Exception as e:
            return f"历史压缩失败: {str(e)}"

    async def _generate_content_outline(self, text: str) -> str:
        """生成内容大纲

        Args:
            text: 内容文本

        Returns:
            文章大纲
        """
        try:
            result = await self.call_tool("generate_outline", text=text)

            return result

        except Exception as e:
            return f"大纲生成失败: {str(e)}"

    async def _handle_general_summary(self, text: str) -> str:
        """处理一般总结

        Args:
            text: 待总结文本

        Returns:
            总结结果
        """
        system_prompt = """你是一个专业的总结助手。请对用户提供的内容进行总结。

        总结要求：
        1. 简洁准确，保留关键信息
        2. 结构清晰，条理分明
        3. 突出重点，忽略次要内容"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请总结以下内容：\n{text}"}
        ]

        return await self.call_llm(messages)

    def _summarize_context(self, text: str) -> str:
        """总结上下文

        Args:
            text: 待总结文本

        Returns:
            总结结果
        """
        return f"上下文总结：\n{text[:200]}..."

    async def analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """使用 LLM 深度分析写作风格

        Args:
            text: 待分析文本

        Returns:
            风格特征字典
        """
        system_prompt = """你是一位专业的写作风格分析专家。请深入分析用户提供的文本，提取其写作风格特征。

请从以下维度进行分析，并以 JSON 格式返回：
{
    "language_style": "语言风格标签，如：幽默/严肃/活泼/沉稳/犀利/温和/文艺/朴实等",
    "tone": "语气特征，如：正式/非正式/学术/口语化/亲切/客观等",
    "vocabulary_level": "词汇水平，如：通俗/专业/学术/文学/口语等",
    "sentence_rhythm": "句式节奏，如：长短句交替/短句为主/长句为主/节奏明快/舒缓等",
    "rhetoric_devices": ["使用的修辞手法，如：比喻/排比/设问/反问/夸张/对偶等"],
    "emotional_tendency": "情感倾向，如：积极/消极/中性/热情/冷静/讽刺等",
    "perspective": "叙述视角，如：第一人称/第三人称/客观/主观/全局/个人等",
    "logic_structure": "逻辑结构偏好，如：总分总/递进/对比/并列/因果等",
    "unique_habits": ["独特的表达习惯或口头禅"],
    "target_audience": "目标读者群体，如：专业人士/大众/学生/技术从业者等",
    "domain_characteristics": "领域特征，如：技术/文学/商业/学术/生活等",
    "writing_quirks": "其他显著特点"
}

注意：
1. 分析要基于文本实际内容，不要臆测
2. 如果文本较短，某些特征可能不明显，标注为"不明显"
3. 返回必须是有效的 JSON 格式"""

        # 截取前3000字符，避免token过多
        text_sample = text[:3000] if len(text) > 3000 else text

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下文本的写作风格：\n\n{text_sample}"}
        ]

        try:
            result = await self.call_llm(messages)
            # 尝试解析 JSON
            import json
            import re

            # 提取 JSON 部分
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                style_data = json.loads(json_match.group())
                return style_data
            else:
                # 如果无法解析，返回原始文本
                return {"raw_analysis": result}
        except Exception as e:
            return {
                "error": f"风格分析失败: {str(e)}",
                "raw_analysis": result if 'result' in locals() else None
            }

    def _extract_style(self, text: str) -> Dict[str, Any]:
        """提取风格（同步版本，用于工具调用）

        Args:
            text: 待分析文本

        Returns:
            风格特征字典
        """
        # 这是一个同步方法，用于工具注册
        # 实际分析应该调用 analyze_writing_style
        return {
            "note": "请使用 analyze_writing_style 方法进行深度分析",
            "writing_style": "简洁",
            "tone": "中性偏正式",
            "vocabulary": "专业",
            "sentence_structure": "复杂句式较多",
            "characteristics": [
                "逻辑性强",
                "注重细节",
                "表达清晰"
            ]
        }

    def _compress_history(self, history: str) -> str:
        """压缩历史

        Args:
            history: 历史记录

        Returns:
            压缩后的历史
        """
        return f"历史压缩总结：\n关键主题：技术博客\n用户意图：文章生成"

    def _generate_outline(self, text: str) -> str:
        """生成大纲

        Args:
            text: 内容文本

        Returns:
            文章大纲
        """
        return """文章大纲：
1. 引言 - 介绍主题背景
2. 主体 - 详细论述核心内容
3. 结论 - 总结要点和建议"""

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 SummaryAgent，是博客写作系统的内容分析中心。

你的职责：
1. 分析并总结上下文内容
2. 提取文本中的写作风格特征
3. 压缩对话历史，减少token消耗
4. 生成文章大纲和结构建议

总结原则：
1. 保持信息的完整性和准确性
2. 突出关键信息和核心观点
3. 去除冗余和重复内容
4. 生成的结构清晰易用

始终保持专业的分析态度，提供高质量的总结服务。"""
