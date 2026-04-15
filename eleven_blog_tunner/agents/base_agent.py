from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AgentContext(BaseModel):
    """Agent 上下文"""
    task_id: str
    user_input: str
    history: List[Dict[str, str]] = []
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: List[Any] = []
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> str:
        """执行 Agent 任务"""
        pass
    
    def add_tool(self, tool: Any) -> "BaseAgent":
        """添加工具"""
        self.tools.append(tool)
        return self
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return f"You are {self.name}. {self.description}"
