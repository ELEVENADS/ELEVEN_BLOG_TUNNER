"""
Agent 基类模块
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime
from eleven_blog_tunner.core.cache import tool_cache
from eleven_blog_tunner.core.connection_pool import thread_pool


class AgentType(Enum):
    """Agent 类型枚举"""
    BOSS = "boss"
    SYSTEM = "system"
    SUMMARY = "summary"
    WRITER = "writer"
    REVIEW = "review"
    ASSISTANT = "assistant"


class AgentMessage(BaseModel):
    """Agent 消息结构"""
    sender: str
    receiver: str
    content: str
    message_type: str = "text"
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentResponse(BaseModel):
    """Agent 响应结构"""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentContext(BaseModel):
    """Agent 上下文"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_input: str
    history: List[Dict[str, str]] = []
    metadata: Dict[str, Any] = {}
    agent_type: Optional[AgentType] = None
    parent_task_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """Agent 基类

    所有 Agent 的基类，提供通用功能：
    - 上下文管理
    - 工具调用
    - LLM 集成
    - 子 Agent 调用
    - 记忆系统集成
    """

    def __init__(
        self,
        name: str,
        description: str,
        agent_type: AgentType,
        llm_provider: str = "openai",
        use_memory: bool = True,
        max_history: int = 10
    ):
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.use_memory = use_memory
        self.max_history = max_history

        self.tools: Dict[str, Callable] = {}
        self.llm = None
        self.memory = None
        self._initialize()

    def _initialize(self):
        """初始化 Agent"""
        self._init_llm()
        self._init_memory()

    def _init_llm(self):
        """初始化 LLM"""
        try:
            # 延迟导入，避免循环依赖
            from eleven_blog_tunner.llm.factory import LLMFactory
            self.llm = LLMFactory.create(
                provider=self.llm_provider,
                use_memory=self.use_memory,
                max_history=self.max_history
            )
        except Exception as e:
            print(f"LLM 初始化失败: {e}")

    def _init_memory(self):
        """初始化记忆系统"""
        if self.use_memory:
            try:
                # 延迟导入，避免循环依赖
                from eleven_blog_tunner.llm.memory import Memory
                self.memory = Memory(max_history=self.max_history)
            except Exception as e:
                print(f"记忆系统初始化失败: {e}")

    def add_tool(self, name: str, func: Callable) -> "BaseAgent":
        """注册工具

        Args:
            name: 工具名称
            func: 工具函数

        Returns:
            self
        """
        self.tools[name] = func
        return self

    async def call_tool(self, name: str, **kwargs) -> Any:
        """调用工具

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if name not in self.tools:
            raise ValueError(f"工具 {name} 不存在")

        # 生成缓存键
        import hashlib
        import json
        cache_key = {
            "tool_name": name,
            "kwargs": kwargs
        }
        cache_key_str = json.dumps(cache_key, sort_keys=True, default=str)
        cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()

        # 检查缓存
        cached_result = tool_cache.get(cache_key_hash)
        if cached_result is not None:
            return cached_result

        tool_func = self.tools[name]

        # 判断是否为异步函数
        import asyncio
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**kwargs)
        else:
            # 使用线程池执行同步函数，避免阻塞事件循环
            result = await thread_pool.run_in_thread(tool_func, **kwargs)

        # 缓存结果
        tool_cache.set(cache_key_hash, result)

        return result

    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """调用 LLM

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            LLM 响应
        """
        if not self.llm:
            raise RuntimeError("LLM 未初始化")

        response = await self.llm.chat(messages, **kwargs)
        return response

    async def call_agent(
        self,
        agent: "BaseAgent",
        context: AgentContext
    ) -> AgentResponse:
        """调用子 Agent

        Args:
            agent: 目标 Agent
            context: 执行上下文

        Returns:
            Agent 响应
        """
        try:
            result = await agent.execute(context)
            return AgentResponse(
                success=True,
                content=result,
                metadata={"agent": agent.name}
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                content="",
                error=str(e),
                metadata={"agent": agent.name}
            )

    def add_to_memory(self, role: str, content: str):
        """添加记忆

        Args:
            role: 角色
            content: 内容
        """
        if self.memory:
            self.memory.add(role, content)

    def get_memory_history(self) -> List[Dict[str, str]]:
        """获取记忆历史

        Returns:
            记忆历史列表
        """
        if self.memory:
            return self.memory.get_history()
        return []

    def clear_memory(self):
        """清空记忆"""
        if self.memory:
            self.memory.clear()

    @abstractmethod
    async def execute(self, context: AgentContext) -> str:
        """执行 Agent 任务

        Args:
            context: Agent 上下文

        Returns:
            执行结果
        """
        pass

    def get_system_prompt(self) -> str:
        """获取系统提示词

        Returns:
            系统提示词
        """
        return f"You are {self.name}. {self.description}"

    def build_messages(
        self,
        context: AgentContext,
        system_prompt: Optional[str] = None,
        include_memory: bool = True
    ) -> List[Dict[str, str]]:
        """构建消息列表

        Args:
            context: Agent 上下文
            system_prompt: 自定义系统提示
            include_memory: 是否包含记忆

        Returns:
            消息列表
        """
        messages = []

        # 添加系统提示
        prompt = system_prompt or self.get_system_prompt()
        messages.append({"role": "system", "content": prompt})

        # 添加记忆历史
        if include_memory and self.memory:
            memory_history = self.get_memory_history()
            if memory_history:
                messages.extend(memory_history)

        # 添加上下文历史
        if context.history:
            messages.extend(context.history)

        # 添加当前输入
        if context.user_input:
            messages.append({"role": "user", "content": context.user_input})

        return messages

    def validate_context(self, context: AgentContext) -> bool:
        """验证上下文

        Args:
            context: Agent 上下文

        Returns:
            是否有效
        """
        if not context.user_input:
            return False
        return True
