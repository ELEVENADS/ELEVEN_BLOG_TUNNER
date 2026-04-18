"""
API 路由
"""
from fastapi import APIRouter
from .config import router as config_router
from .agent import router as agent_router
from .knowledge import router as knowledge_router
from .styles import router as styles_router
from .articles import router as articles_router
from .gateway import router as gateway_router
from .auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(config_router)
api_router.include_router(agent_router)
api_router.include_router(knowledge_router)
api_router.include_router(styles_router)
api_router.include_router(articles_router)
api_router.include_router(gateway_router)