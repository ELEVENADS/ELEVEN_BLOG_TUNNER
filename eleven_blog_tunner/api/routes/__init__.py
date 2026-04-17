"""
API 路由
"""
from fastapi import APIRouter
from .config import router as config_router
from .agent import router as agent_router
from .knowledge import router as knowledge_router

api_router = APIRouter()
api_router.include_router(config_router)
api_router.include_router(agent_router)
api_router.include_router(knowledge_router)
