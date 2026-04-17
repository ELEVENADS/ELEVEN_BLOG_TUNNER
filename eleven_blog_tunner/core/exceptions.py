"""
自定义异常类
"""
from typing import Optional, Dict, Any

class ElevenBlogException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error": {
                "message": self.message,
                "error_code": self.error_code,
                "details": self.details
            }
        }


class AgentException(ElevenBlogException):
    """Agent 相关异常"""
    pass


class AgentNotFoundError(AgentException):
    """Agent 未找到"""
    def __init__(self, agent_name: str):
        super().__init__(
            message=f"Agent '{agent_name}' not found",
            error_code=404,
            details={"agent_name": agent_name}
        )


class AgentExecutionError(AgentException):
    """Agent 执行失败"""
    def __init__(self, agent_name: str, error: str):
        super().__init__(
            message=f"Agent '{agent_name}' execution failed: {error}",
            error_code=500,
            details={"agent_name": agent_name, "error": error}
        )


class LLMException(ElevenBlogException):
    """LLM 调用异常"""
    pass


class LLMConnectionError(LLMException):
    """LLM 连接失败"""
    def __init__(self, provider: str, error: str):
        super().__init__(
            message=f"LLM connection failed ({provider}): {error}",
            error_code=503,
            details={"provider": provider, "error": error}
        )


class LLMResponseError(LLMException):
    """LLM 响应错误"""
    def __init__(self, provider: str, error: str):
        super().__init__(
            message=f"LLM response error ({provider}): {error}",
            error_code=500,
            details={"provider": provider, "error": error}
        )


class LLMTimeoutError(LLMException):
    """LLM 超时"""
    def __init__(self, provider: str, timeout: float):
        super().__init__(
            message=f"LLM timeout ({provider}): {timeout}s",
            error_code=408,
            details={"provider": provider, "timeout": timeout}
        )


class RAGException(ElevenBlogException):
    """RAG 处理异常"""
    pass


class DocumentProcessingError(RAGException):
    """文档处理失败"""
    def __init__(self, error: str):
        super().__init__(
            message=f"Document processing failed: {error}",
            error_code=400,
            details={"error": error}
        )


class VectorDBError(RAGException):
    """向量数据库错误"""
    def __init__(self, error: str):
        super().__init__(
            message=f"Vector database error: {error}",
            error_code=500,
            details={"error": error}
        )


class EmbeddingError(RAGException):
    """向量化失败"""
    def __init__(self, model: str, error: str):
        super().__init__(
            message=f"Embedding failed ({model}): {error}",
            error_code=500,
            details={"model": model, "error": error}
        )


class ToolException(ElevenBlogException):
    """工具调用异常"""
    pass


class ToolNotFoundError(ToolException):
    """工具未找到"""
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"Tool '{tool_name}' not found",
            error_code=404,
            details={"tool_name": tool_name}
        )


class ToolExecutionError(ToolException):
    """工具执行失败"""
    def __init__(self, tool_name: str, error: str):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {error}",
            error_code=500,
            details={"tool_name": tool_name, "error": error}
        )


class ConfigException(ElevenBlogException):
    """配置异常"""
    pass


class ConfigNotFoundError(ConfigException):
    """配置未找到"""
    def __init__(self, config_key: str):
        super().__init__(
            message=f"Config '{config_key}' not found",
            error_code=404,
            details={"config_key": config_key}
        )


class ConfigValidationError(ConfigException):
    """配置验证失败"""
    def __init__(self, config_key: str, error: str):
        super().__init__(
            message=f"Config validation failed for '{config_key}': {error}",
            error_code=400,
            details={"config_key": config_key, "error": error}
        )

