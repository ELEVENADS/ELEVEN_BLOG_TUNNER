"""
System Agent 模块

负责系统内任务状态查询和各种参数返回，比如返回风格数据等。
"""
from typing import Dict, List, Optional, Any
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext, AgentType


class SystemAgent(BaseAgent):
    """
    System Agent

    负责系统内任务状态查询和各种参数返回：
    - 风格数据查询
    - 系统配置获取
    - 任务状态查询
    - 记忆检索
    """

    def __init__(self, llm_provider: str = "openai", use_memory: bool = True):
        super().__init__(
            name="SystemAgent",
            description="负责系统内任务状态查询和各种参数返回",
            agent_type=AgentType.SYSTEM,
            llm_provider=llm_provider,
            use_memory=use_memory
        )
        self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        self.add_tool("get_style_config", self._get_style_config)
        self.add_tool("get_system_config", self._get_system_config)
        self.add_tool("query_memory", self._query_memory)
        self.add_tool("get_task_status", self._get_task_status)

    async def execute(self, context: AgentContext) -> str:
        """执行系统查询

        Args:
            context: Agent 上下文

        Returns:
            查询结果
        """
        if not self.validate_context(context):
            return "错误: 无效的上下文"

        user_input = context.user_input

        query_type = self._analyze_query_type(user_input)

        if query_type == "style":
            result = await self._query_style(user_input)
        elif query_type == "config":
            result = await self._query_config(user_input)
        elif query_type == "memory":
            result = await self._query_memory_data(user_input)
        elif query_type == "status":
            result = await self._query_status(context)
        else:
            result = await self._handle_general_query(user_input)

        return result

    def _analyze_query_type(self, user_input: str) -> str:
        """分析查询类型

        Args:
            user_input: 用户输入

        Returns:
            查询类型
        """
        user_input_lower = user_input.lower()

        if any(keyword in user_input_lower for keyword in ["风格", "style", "写作风格"]):
            return "style"
        elif any(keyword in user_input_lower for keyword in ["配置", "config", "系统配置"]):
            return "config"
        elif any(keyword in user_input_lower for keyword in ["记忆", "memory", "历史"]):
            return "memory"
        elif any(keyword in user_input_lower for keyword in ["状态", "status", "任务"]):
            return "status"
        else:
            return "general"

    async def _query_style(self, query: str) -> str:
        """查询风格数据

        Args:
            query: 查询内容

        Returns:
            风格配置
        """
        try:
            style_config = await self.call_tool("get_style_config", query=query)

            system_prompt = """你是一个风格分析助手。根据提供的风格配置，
            用自然语言描述风格特点。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"风格配置：\n{style_config}"}
            ]

            return await self.call_llm(messages)

        except Exception as e:
            return f"风格查询失败: {str(e)}"

    async def _query_config(self, query: str) -> str:
        """查询系统配置

        Args:
            query: 查询内容

        Returns:
            系统配置
        """
        try:
            config = await self.call_tool("get_system_config", query=query)

            system_prompt = """你是一个系统配置助手。根据提供的系统配置信息，
            用自然语言描述当前系统状态。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"系统配置：\n{config}"}
            ]

            return await self.call_llm(messages)

        except Exception as e:
            return f"配置查询失败: {str(e)}"

    async def _query_memory_data(self, query: str) -> str:
        """查询记忆数据

        Args:
            query: 查询内容

        Returns:
            记忆数据
        """
        try:
            memory_data = await self.call_tool("query_memory", query=query)

            if not memory_data:
                return "未找到相关记忆数据"

            return memory_data

        except Exception as e:
            return f"记忆查询失败: {str(e)}"

    async def _query_status(self, context: AgentContext) -> str:
        """查询状态

        Args:
            context: Agent 上下文

        Returns:
            状态信息
        """
        try:
            status = await self.call_tool(
                "get_task_status",
                task_id=context.task_id
            )

            return status

        except Exception as e:
            return f"状态查询失败: {str(e)}"

    async def _handle_general_query(self, query: str) -> str:
        """处理一般查询

        Args:
            query: 查询内容

        Returns:
            查询结果
        """
        system_prompt = """你是一个系统查询助手。用户会提出各种关于系统配置、
        风格设置、写作参数等问题。请根据你的知识回答用户问题。

        如果涉及：
        1. 风格配置 → 提供默认风格描述
        2. 系统参数 → 提供合理的默认值
        3. 使用方法 → 提供清晰的指导"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        return await self.call_llm(messages)

    def _get_style_config(self, query: str) -> Dict[str, Any]:
        """获取风格配置

        Args:
            query: 查询内容

        Returns:
            风格配置字典
        """
        default_style = {
            "writing_style": "简洁专业",
            "tone": "中性",
            "paragraph_length": "中等",
            "use_analogies": True,
            "code_examples": False,
            "summary_style": "要点式"
        }

        return default_style

    def _get_system_config(self, query: str) -> Dict[str, Any]:
        """获取系统配置

        Args:
            query: 查询内容

        Returns:
            系统配置字典
        """
        try:
            from eleven_blog_tunner.core.config import get_settings
            settings = get_settings()

            return {
                "llm_provider": settings.llm_provider,
                "llm_model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap
            }
        except Exception:
            return {
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 4096,
                "embedding_model": "text-embedding-3-small",
                "chunk_size": 1000,
                "chunk_overlap": 200
            }

    def _query_memory(self, query: str) -> str:
        """查询记忆

        Args:
            query: 查询内容

        Returns:
            相关记忆
        """
        if not self.memory:
            return "记忆系统未初始化"

        history = self.get_memory_history()

        if not history:
            return "没有找到相关记忆"

        return "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in history[-5:]
        ])

    def _get_task_status(self, task_id: str) -> str:
        """获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态
        """
        return f"任务 {task_id} 状态查询"

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return """你是 SystemAgent，是博客写作系统的配置和状态查询中心。

你的职责：
1. 提供风格配置查询服务
2. 返回系统配置信息
3. 查询任务执行状态
4. 检索记忆数据

始终保持专业、准确的服务态度。"""
