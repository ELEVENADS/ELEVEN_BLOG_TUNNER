"""
记忆管理模块
"""
from typing import List, Dict, Optional
from collections import deque


class Memory:
    """对话记忆"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
    
    def add(self, role: str, content: str):
        """添加对话记录"""
        self.history.append({"role": role, "content": content})
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取历史记录"""
        return list(self.history)
    
    def clear(self):
        """清空记忆"""
        self.history.clear()
    
    def get_last_n(self, n: int) -> List[Dict[str, str]]:
        """获取最近 n 条记录"""
        return list(self.history)[-n:]


class LongTermMemory:
    """长期记忆（基于向量数据库）"""
    
    def __init__(self):
        # TODO: 集成向量数据库
        pass
    
    async def store(self, key: str, content: str):
        """存储长期记忆"""
        pass
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """检索相关记忆"""
        return []
