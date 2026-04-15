"""
OpenAI 提供商
"""
from typing import AsyncIterator, List, Dict, Any
from eleven_blog_tunner.llm.base import BaseLLM


class OpenAIProvider(BaseLLM):
    """OpenAI LLM 提供商"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        super().__init__(model=model, **kwargs)
        self.api_key = api_key
        # TODO: 初始化 OpenAI 客户端
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话"""
        # TODO: 实现 OpenAI 调用
        return ""
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """流式对话"""
        # TODO: 实现 OpenAI 流式调用
        yield ""
