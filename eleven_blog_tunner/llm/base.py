"""
LLM 基类
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any

class BaseLLM(ABC):
    """LLM 基类
    
    所有 LLM 提供商的基类，定义统一的消息格式标准。
    
    标准消息格式：
    - role: 消息角色 ("system", "user", "assistant", "tool")
    - content: 消息内容
    - name: 工具名称 (仅用于 tool 角色)
    - tool_calls: 工具调用列表 (仅用于 assistant 角色)
    - tool_call_id: 工具调用ID (仅用于 tool 角色)
    
    示例：
    [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
        {"role": "assistant", "content": "", "tool_calls": [...]},
        {"role": "tool", "content": "工具结果", "tool_call_id": "call_xxx", "name": "tool_name"}
    ]
    """
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备消息，子类可以重写此方法进行格式转换
        
        Args:
            messages: 标准格式的消息列表
            
        Returns:
            转换后的消息列表，适合当前提供商的格式
        """
        # 默认不做转换，直接返回
        return messages
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数，如 tools, tool_choice 等
            
        Returns:
            模型的响应文本
        """
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """流式对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数，如 tools, tool_choice 等
            
        Yields:
            模型响应的文本片段
        """
        pass
