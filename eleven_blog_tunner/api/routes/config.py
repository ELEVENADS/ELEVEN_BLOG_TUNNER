"""
配置相关 API
"""
from fastapi import APIRouter
from eleven_blog_tunner.core.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/")
async def get_config():
    """获取配置信息"""
    settings = get_settings()
    return {
        "api_base_url": settings.api_base_url,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }
