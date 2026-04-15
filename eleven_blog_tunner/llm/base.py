"""
LLM 基类
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any


class BaseLLM(ABC):
    """LLM 基类"""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话"""
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """流式对话"""
        pass
