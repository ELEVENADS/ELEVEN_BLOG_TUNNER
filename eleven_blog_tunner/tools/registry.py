"""
工具注册中心
"""
import inspect
from typing import Dict, Callable, Any
from functools import wraps


class ToolRegistry:
    """工具注册中心"""
    
    _tools: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, name: str = None, description: str = ""):
        """注册工具装饰器"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            cls._tools[tool_name] = {
                "func": func,
                "description": description,
                "signature": inspect.signature(func),
                "doc": func.__doc__
            }
            return func
        return decorator
    
    @classmethod
    def get_tool(cls, name: str) -> Callable:
        """获取工具"""
        if name not in cls._tools:
            raise KeyError(f"Tool '{name}' not found")
        return cls._tools[name]["func"]
    
    @classmethod
    def list_tools(cls) -> Dict[str, Dict[str, str]]:
        """列出所有工具"""
        return {
            name: {
                "description": info["description"],
                "doc": info["doc"],
                "params": str(info["signature"])
            }
            for name, info in cls._tools.items()
        }
    
    @classmethod
    def has_tool(cls, name: str) -> bool:
        """检查工具是否存在"""
        return name in cls._tools


# 便捷装饰器
tool = ToolRegistry.register
