"""
LLM 基类
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
from eleven_blog_tunner.llm.memory import Memory
from eleven_blog_tunner.core.cache import llm_cache

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
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096, use_memory: bool = True, max_history: int = 10):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_memory = use_memory
        self.max_history = max_history
        
        # 初始化记忆系统
        if self.use_memory:
            self.memory = Memory(max_history=max_history, max_tokens=max_tokens)
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备消息，子类可以重写此方法进行格式转换
        
        Args:
            messages: 标准格式的消息列表
            
        Returns:
            转换后的消息列表，适合当前提供商的格式
        """
        # 默认不做转换，直接返回
        return messages
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数，如 tools, tool_choice 等
            
        Returns:
            模型的响应文本
        """
        # 生成缓存键
        cache_key = {
            "model": self.model,
            "messages": messages,
            "kwargs": kwargs
        }
        
        # 检查缓存
        import hashlib
        import json
        cache_key_str = json.dumps(cache_key, sort_keys=True, default=str)
        cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
        
        cached_response = llm_cache.get(cache_key_hash)
        if cached_response:
            return cached_response
        
        # 如果使用记忆系统，合并历史消息
        if self.use_memory:
            # 提取系统消息（通常是第一条）
            system_messages = [msg for msg in messages if msg.get("role") == "system"]
            # 提取新的用户消息
            new_messages = [msg for msg in messages if msg.get("role") != "system"]
            
            # 获取历史记忆（不包含系统消息）
            history = [msg for msg in self.memory.get_history() if msg.get("role") != "system"]
            
            # 构建完整消息列表：系统消息 + 历史消息 + 新消息
            full_messages = system_messages + history + new_messages
        else:
            full_messages = messages
        
        # 调用具体实现
        response = await self._chat(full_messages, **kwargs)
        
        # 缓存响应
        llm_cache.set(cache_key_hash, response)
        
        # 更新记忆
        if self.use_memory:
            # 添加新消息到记忆
            for msg in new_messages:
                self.memory.add_message(msg)
            # 添加模型响应到记忆
            self.memory.add("assistant", response)
        
        return response
    
    async def stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """流式对话
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数，如 tools, tool_choice 等
            
        Yields:
            模型响应的文本片段
        """
        # 如果使用记忆系统，合并历史消息
        if self.use_memory:
            # 提取系统消息
            system_messages = [msg for msg in messages if msg.get("role") == "system"]
            # 提取新的用户消息
            new_messages = [msg for msg in messages if msg.get("role") != "system"]
            
            # 获取历史记忆
            history = [msg for msg in self.memory.get_history() if msg.get("role") != "system"]
            
            # 构建完整消息列表
            full_messages = system_messages + history + new_messages
        else:
            full_messages = messages
        
        # 收集流式响应
        response_chunks = []
        async for chunk in self._stream_chat(full_messages, **kwargs):
            response_chunks.append(chunk)
            yield chunk
        
        # 合并响应并更新记忆
        if self.use_memory:
            full_response = "".join(response_chunks)
            # 添加新消息到记忆
            for msg in new_messages:
                self.memory.add_message(msg)
            # 添加模型响应到记忆
            self.memory.add("assistant", full_response)
    
    @abstractmethod
    async def _chat(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """实际对话实现
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数
            
        Returns:
            模型的响应文本
        """
        pass
    
    @abstractmethod
    async def _stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """实际流式对话实现
        
        Args:
            messages: 标准格式的消息列表
            **kwargs: 额外的参数
            
        Yields:
            模型响应的文本片段
        """
        pass
    
    def get_memory(self) -> Optional[Memory]:
        """获取记忆系统实例
        
        Returns:
            Memory 实例或 None
        """
        return getattr(self, "memory", None)
    
    def clear_memory(self):
        """清空记忆"""
        if self.use_memory and hasattr(self, "memory"):
            self.memory.clear()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Returns:
            对话历史消息列表
        """
        if self.use_memory and hasattr(self, "memory"):
            return self.memory.get_history()
        return []
    
    def add_to_memory(self, message: Dict[str, Any]):
        """手动添加消息到记忆
        
        Args:
            message: 消息对象
        """
        if self.use_memory and hasattr(self, "memory"):
            self.memory.add_message(message)
