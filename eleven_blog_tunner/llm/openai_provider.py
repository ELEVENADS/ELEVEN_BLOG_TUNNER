"""
OpenAI 提供商
"""
from typing import AsyncIterator, List, Dict, Any
from openai import AsyncOpenAI
from eleven_blog_tunner.llm.base import BaseLLM


class OpenAIProvider(BaseLLM):
    """OpenAI LLM 提供商
    
    使用标准 OpenAI API 格式，支持对话、流式对话和函数调用。
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None, **kwargs):
        super().__init__(model=model, **kwargs)
        self.api_key = api_key
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**client_kwargs)
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备消息，转换为 OpenAI 格式
        
        OpenAI 支持的消息角色：system, user, assistant, tool
        """
        prepared_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "tool":
                # 工具消息需要 tool_call_id
                prepared_msg = {
                    "role": "tool",
                    "content": content,
                    "tool_call_id": msg.get("tool_call_id", "")
                }
            elif role == "assistant" and "tool_calls" in msg:
                # 包含工具调用的 assistant 消息
                prepared_msg = {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": msg["tool_calls"]
                }
            else:
                # 普通消息
                prepared_msg = {
                    "role": role,
                    "content": content
                }
                # 如果有 name 字段（用于 function calling），添加到消息中
                if "name" in msg:
                    prepared_msg["name"] = msg["name"]
            
            prepared_messages.append(prepared_msg)
        
        return prepared_messages
    
    async def _chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数
                - tools: 工具定义列表
                - tool_choice: 工具选择策略 ("auto", "none", 或指定工具)
                
        Returns:
            模型的响应文本，或包含工具调用的响应
        """
        # 准备消息
        prepared_messages = self._prepare_messages(messages)
        
        # 提取参数
        tools = kwargs.get('tools')
        tool_choice = kwargs.get('tool_choice')
        
        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": prepared_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # 添加工具相关参数
        if tools:
            request_params["tools"] = tools
            if tool_choice:
                request_params["tool_choice"] = tool_choice
        
        # 发送请求
        response = await self.client.chat.completions.create(**request_params)
        
        # 处理响应
        message = response.choices[0].message
        
        # 如果有工具调用，返回工具调用信息
        if hasattr(message, 'tool_calls') and message.tool_calls:
            return {
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            }
        
        return message.content or ""
    
    async def _stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """流式对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数
                - tools: 工具定义列表
                - tool_choice: 工具选择策略
                
        Yields:
            模型响应的文本片段
        """
        # 准备消息
        prepared_messages = self._prepare_messages(messages)
        
        # 提取参数
        tools = kwargs.get('tools')
        tool_choice = kwargs.get('tool_choice')
        
        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": prepared_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True
        }
        
        # 添加工具相关参数
        if tools:
            request_params["tools"] = tools
            if tool_choice:
                request_params["tool_choice"] = tool_choice
        
        # 发送流式请求
        stream = await self.client.chat.completions.create(**request_params)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
