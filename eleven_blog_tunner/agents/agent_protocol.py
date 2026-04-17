"""
Agent 通信协议模块

定义 Agent 之间的通信标准和调用链机制。
"""
from typing import Dict, List, Optional, Any, Callable, Awaitable
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid
import asyncio


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentMessage(BaseModel):
    """Agent 消息结构

    用于 Agent 之间传递的消息格式。
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    receiver: str
    content: str
    message_type: MessageType = MessageType.REQUEST
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    reply_to: Optional[str] = None


class TaskContext(BaseModel):
    """任务上下文

    描述一个完整任务的执行上下文。
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[Dict[str, Any]] = []


class AgentCallChain:
    """Agent 调用链

    管理 Agent 之间的调用关系和执行流程。
    """

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.call_history: List[AgentMessage] = []
        self.task_contexts: Dict[str, TaskContext] = {}

    def register_agent(self, name: str, agent: Any):
        """注册 Agent

        Args:
            name: Agent 名称
            agent: Agent 实例
        """
        self.agents[name] = agent

    def get_agent(self, name: str) -> Optional[Any]:
        """获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例
        """
        return self.agents.get(name)

    def create_task(self, parent_task_id: Optional[str] = None) -> TaskContext:
        """创建任务上下文

        Args:
            parent_task_id: 父任务 ID

        Returns:
            任务上下文
        """
        task = TaskContext(parent_task_id=parent_task_id)
        self.task_contexts[task.task_id] = task
        return task

    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            **kwargs: 其他更新字段
        """
        if task_id in self.task_contexts:
            task = self.task_contexts[task_id]
            task.status = status
            task.updated_at = datetime.now()
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

    def add_step(self, task_id: str, step: Dict[str, Any]):
        """添加执行步骤

        Args:
            task_id: 任务 ID
            step: 步骤信息
        """
        if task_id in self.task_contexts:
            self.task_contexts[task_id].steps.append(step)

    async def send_message(
        self,
        sender: str,
        receiver: str,
        content: str,
        message_type: MessageType = MessageType.REQUEST,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """发送消息

        Args:
            sender: 发送者
            receiver: 接收者
            content: 消息内容
            message_type: 消息类型
            metadata: 元数据

        Returns:
            发送的消息
        """
        message = AgentMessage(
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.call_history.append(message)
        return message

    async def route_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """路由消息

        Args:
            message: 消息

        Returns:
            响应消息
        """
        receiver = self.get_agent(message.receiver)
        if not receiver:
            return await self.send_message(
                sender=message.receiver,
                receiver=message.sender,
                content=f"Agent {message.receiver} 未找到",
                message_type=MessageType.ERROR,
                metadata={"original_message_id": message.message_id}
            )

        try:
            response_content = await receiver.execute(message.content)
            return await self.send_message(
                sender=message.receiver,
                receiver=message.sender,
                content=response_content,
                message_type=MessageType.RESPONSE,
                metadata={"original_message_id": message.message_id}
            )
        except Exception as e:
            return await self.send_message(
                sender=message.receiver,
                receiver=message.sender,
                content=f"执行失败: {str(e)}",
                message_type=MessageType.ERROR,
                metadata={"original_message_id": message.message_id}
            )


class AgentProtocol:
    """Agent 通信协议

    定义 Agent 之间的标准通信接口和流程。
    """

    def __init__(self):
        self.call_chain = AgentCallChain()
        self._init_builtin_agents()

    def _init_builtin_agents(self):
        """初始化内置 Agent"""
        # 延迟导入以避免循环导入
        try:
            from eleven_blog_tunner.agents.boss_agent import BossAgent
            from eleven_blog_tunner.agents.system_agent import SystemAgent
            from eleven_blog_tunner.agents.summary_agent import SummaryAgent
            from eleven_blog_tunner.agents.writer_agent import WriterAgent
            from eleven_blog_tunner.agents.review_agent import ReviewAgent

            self.register_agent("BossAgent", BossAgent())
            self.register_agent("SystemAgent", SystemAgent())
            self.register_agent("SummaryAgent", SummaryAgent())
            self.register_agent("WriterAgent", WriterAgent())
            self.register_agent("ReviewAgent", ReviewAgent())
        except ImportError:
            # 导入失败时跳过初始化
            pass

    def register_agent(self, name: str, agent: Any):
        """注册 Agent

        Args:
            name: Agent 名称
            agent: Agent 实例
        """
        self.call_chain.register_agent(name, agent)

    def get_agent(self, name: str) -> Optional[Any]:
        """获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例
        """
        return self.call_chain.get_agent(name)

    async def execute_task(
        self,
        task: str,
        initial_input: str,
        agent_sequence: Optional[List[str]] = None
    ) -> str:
        """执行任务

        Args:
            task: 任务描述
            initial_input: 初始输入
            agent_sequence: Agent 执行序列，默认使用标准流程

        Returns:
            任务结果
        """
        if agent_sequence is None:
            agent_sequence = [
                "BossAgent",
                "SystemAgent",
                "SummaryAgent",
                "WriterAgent",
                "ReviewAgent"
            ]

        task_context = self.call_chain.create_task()
        self.call_chain.update_task_status(task_context.task_id, TaskStatus.RUNNING)

        current_input = initial_input

        for agent_name in agent_sequence:
            agent = self.get_agent(agent_name)
            if not agent:
                self.call_chain.update_task_status(
                    task_context.task_id,
                    TaskStatus.FAILED,
                    error=f"Agent {agent_name} 未找到"
                )
                raise ValueError(f"Agent {agent_name} 未找到")

            self.call_chain.add_step(task_context.task_id, {
                "agent": agent_name,
                "input": current_input,
                "timestamp": datetime.now().isoformat()
            })

            try:
                current_input = await agent.execute(current_input)
            except Exception as e:
                self.call_chain.update_task_status(
                    task_context.task_id,
                    TaskStatus.FAILED,
                    error=str(e)
                )
                raise

        self.call_chain.update_task_status(
            task_context.task_id,
            TaskStatus.COMPLETED,
            result=current_input
        )

        return current_input

    async def call_agent(
        self,
        caller: str,
        callee: str,
        input_data: str
    ) -> Dict[str, Any]:
        """Agent 间直接调用

        Args:
            caller: 调用者
            callee: 被调用者
            input_data: 输入数据

        Returns:
            调用结果
        """
        agent = self.get_agent(callee)
        if not agent:
            return {
                "success": False,
                "error": f"Agent {callee} 未找到"
            }

        try:
            result = await agent.execute(input_data)
            return {
                "success": True,
                "result": result,
                "callee": callee
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "callee": callee
            }

    def get_task_context(self, task_id: str) -> Optional[TaskContext]:
        """获取任务上下文

        Args:
            task_id: 任务 ID

        Returns:
            任务上下文
        """
        return self.call_chain.task_contexts.get(task_id)

    def get_call_history(self) -> List[AgentMessage]:
        """获取调用历史

        Returns:
            调用历史列表
        """
        return self.call_chain.call_history


# 全局协议实例
_global_protocol: Optional[AgentProtocol] = None


def get_protocol() -> AgentProtocol:
    """获取全局协议实例

    Returns:
        AgentProtocol 实例
    """
    global _global_protocol
    if _global_protocol is None:
        _global_protocol = AgentProtocol()
    return _global_protocol
