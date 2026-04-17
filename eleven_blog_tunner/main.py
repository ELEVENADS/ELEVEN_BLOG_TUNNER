"""
应用入口
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from eleven_blog_tunner.api import router as api_router
from eleven_blog_tunner.core.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    settings = get_settings()
    print("[START] 启动 ELEVEN Blog Tuner")
    print(f"   API: {settings.api_base_url}")
    print(f"   LLM: {settings.llm_provider}/{settings.llm_model}")
    
    yield
    # 关闭时执行
    print("[STOP] 关闭应用")

app = FastAPI(
    title="ELEVEN Blog Tuner API",
    description="AI 博客生成助手",
    version="0.1.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(api_router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "ELEVEN Blog Tuner",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

import sys
from pathlib import Path

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "eleven_blog_tunner.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
