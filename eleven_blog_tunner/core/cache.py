"""
缓存模块

提供通用的缓存功能，用于存储LLM响应、工具调用结果等
"""
import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class Cache:
    """缓存类
    
    提供内存缓存功能，支持TTL（Time To Live）
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """初始化缓存
        
        Args:
            max_size: 缓存最大容量
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_key(self, data: Any) -> str:
        """生成缓存键
        
        Args:
            data: 要缓存的数据
            
        Returns:
            缓存键
        """
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        # 检查是否过期
        if datetime.now() > item['expires_at']:
            del self.cache[key]
            return None
        
        return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认值
        """
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # 删除最旧的缓存
            oldest_key = min(self.cache.items(), key=lambda x: x[1]['created_at'])[0]
            del self.cache[oldest_key]
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl)
        }
    
    def delete(self, key: str) -> None:
        """删除缓存
        
        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def get_size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        return len(self.cache)


# 全局缓存实例
llm_cache = Cache(max_size=1000, default_ttl=3600)
tool_cache = Cache(max_size=500, default_ttl=1800)
