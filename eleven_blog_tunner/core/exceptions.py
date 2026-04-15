"""
自定义异常类
"""


class ElevenBlogException(Exception):
    """基础异常类"""
    pass


class AgentException(ElevenBlogException):
    """Agent 相关异常"""
    pass


class LLMException(ElevenBlogException):
    """LLM 调用异常"""
    pass


class RAGException(ElevenBlogException):
    """RAG 处理异常"""
    pass


class ToolException(ElevenBlogException):
    """工具调用异常"""
    pass
