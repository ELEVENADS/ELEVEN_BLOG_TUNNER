"""
MCP 工具集
负责存放 mcp 工具集
"""
from typing import List, Dict, Any


class MCPTools:
    """MCP 工具管理"""
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
    
    def register_mcp_tool(self, name: str, tool: Any):
        """注册 MCP 工具"""
        self._tools[name] = tool
    
    def get_mcp_tool(self, name: str) -> Any:
        """获取 MCP 工具"""
        return self._tools.get(name)
    
    def list_mcp_tools(self) -> List[str]:
        """列出所有 MCP 工具"""
        return list(self._tools.keys())
