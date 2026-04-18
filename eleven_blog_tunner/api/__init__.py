"""
API 模块
"""
from fastapi import APIRouter
from .routes import api_router as routes_router

router = APIRouter(prefix="/api/v1")

router.include_router(routes_router)
