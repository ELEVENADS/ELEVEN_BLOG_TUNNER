import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

def get_project_root() -> Path:
    """获取项目根目录"""
    # 当前文件路径: eleven_blog_tunner/core/config.py
    # 往上退2层到项目根目录
    return Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """统一配置管理"""
    
    # API 配置
    api_base_url: str = "http://localhost:8000"
    
    # LLM 配置
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_base_url: str = ""  # 可选，用于兼容 OpenAI SDK 的第三方服务（如阿里云 DashScope）
    llm_api_key: str = ""   # LLM API Key
    
    # 本地 LLM 配置
    local_llm_base_url: str = "http://localhost:11434/api"
    local_llm_model: str = "llama3"
    
    # RAG 配置
    vector_db_path: str = "./data/vector_db"
    embedding_model: str = "text-embedding-3-small"
    local_embedding_model: str = "dengcao/bge-large-zh-v1.5:latest"
    rerank_model: str = "bbjson/bge-reranker-base"
    local_rerank_model: str = "bbjson/bge-reranker-base"
    use_local_embedding: bool = False
    use_local_rerank: bool = False
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # 数据库
    database_url: str = "postgresql://postgres:123456@localhost:5432/eleven_note"
    
    # 日志
    log_level: str = "INFO"
    
    # Celery 配置
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(
        env_file=get_project_root() / ".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略未定义的环境变量
    )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()