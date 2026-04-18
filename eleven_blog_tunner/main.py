"""
应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import sys
import os

from eleven_blog_tunner.api import router as api_router
from eleven_blog_tunner.core.config import get_settings

# 创建静态目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)


LOGO = """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                               ║
    ║     _______   ___       _______   ___      ___ _______   ________             ║
    ║    |\  ___ \ |\  \     |\  ___ \ |\  \    /  /|\  ___ \ |\   ___  \           ║
    ║     \ \   __/|\ \  \    \ \   __/|\ \  \  /  / | \   __/|\ \  \ \  \          ║
    ║      \ \  \_|/_\ \  \    \ \  \_|/_\ \  \/  / / \ \  \_|/_\ \  \ \  \         ║
    ║       \ \  \_|\ \ \  \____\ \  \_|\ \ \    / /   \ \  \_|\ \ \  \ \  \        ║
    ║        \ \_______\ \_______\ \_______\ \__/ /     \ \_______\ \__\ \__\       ║
    ║         \|_______|\|_______|\|_______|\|__|/       \|_______|\|__| \|__|      ║
    ║                                                                               ║      
    ║                     A R T I C L E   G E N E R A T O R                         ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
"""


def get_emoji(text: str, fallback: str = "") -> str:
    """根据系统环境返回合适的 emoji 或替代文本"""
    if sys.platform.startswith('win'):
        return fallback
    return text


def mask_sensitive_info(value: str, show_last: int = 4) -> str:
    """掩码敏感信息，只显示尾部几位"""
    if not value:
        return "<未设置>"
    if len(value) <= show_last:
        return value
    return "*" * (len(value) - show_last) + value[-show_last:]


def format_config_value(key: str, value: str) -> str:
    """格式化配置值"""
    sensitive_keys = ["llm_api_key", "database_url"]
    if any(sensitive in key.lower() for sensitive in sensitive_keys):
        if "database_url" in key.lower():
            # 特殊处理数据库 URL
            if "://" in value:
                parts = value.split("://")
                if len(parts) == 2:
                    protocol = parts[0]
                    rest = parts[1]
                    if ":" in rest and "@" in rest:
                        creds, host_part = rest.split("@", 1)
                        if ":" in creds:
                            user, password = creds.split(":", 1)
                            masked_password = mask_sensitive_info(password)
                            return f"{protocol}://{user}:{masked_password}@{host_part}"
        return mask_sensitive_info(value)
    return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(LOGO)
    print("\n" + "=" * 80)
    print(f"{get_emoji('🚀', '>>>')} 系统启动中...")

    settings = get_settings()
    
    # 创建数据库表
    from eleven_blog_tunner.common.models import create_tables
    print(f"{get_emoji('🗃️', '  ')} 创建数据库表...")
    create_tables()
    print(f"{get_emoji('✅', '  ')} 数据库表创建完成")
    
    # 显示所有配置项
    print(f"\n{get_emoji('📋', '  ')} 系统配置:")
    print("-" * 60)
    
    config_items = {
        "API Base URL": settings.api_base_url,
        "LLM Provider": settings.llm_provider,
        "LLM Model": settings.llm_model,
        "LLM Temperature": settings.llm_temperature,
        "LLM Max Tokens": settings.llm_max_tokens,
        "LLM Base URL": settings.llm_base_url,
        "LLM API Key": format_config_value("llm_api_key", settings.llm_api_key),
        "Local LLM Base URL": settings.local_llm_base_url,
        "Local LLM Model": settings.local_llm_model,
        "Vector DB Path": settings.vector_db_path,
        "Embedding Model": settings.embedding_model,
        "Local Embedding Model": settings.local_embedding_model,
        "Rerank Model": settings.rerank_model,
        "Local Rerank Model": settings.local_rerank_model,
        "Use Local Embedding": settings.use_local_embedding,
        "Use Local Rerank": settings.use_local_rerank,
        "Chunk Size": settings.chunk_size,
        "Chunk Overlap": settings.chunk_overlap,
        "Database URL": format_config_value("database_url", settings.database_url),
        "Log Level": settings.log_level,
    }
    
    for key, value in config_items.items():
        formatted_value = format_config_value(key, str(value))
        print(f"   {key:<30} {formatted_value}")
    
    print("-" * 60)
    
    print("\n" + "=" * 80)
    print(f"\n{get_emoji('✅', ' ')} 系统已成功启动！")
    print(f"{get_emoji('📖', '  ')} API 文档: http://localhost:8000/docs")
    print(f"{get_emoji('❤️', '  ')} 健康检查: http://localhost:8000/health")
    print("\n" + "-" * 80 + "\n")

    yield

    print("\n" + "-" * 80)
    print(f"{get_emoji('👋', '  ')} 系统正在关闭...")
    print(f"{get_emoji('✅', ' ')} 系统已关闭")


app = FastAPI(
    title="ELEVEN Blog Turner API",
    description="AI 博客生成助手",
    version="0.1.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(api_router)

# 配置静态文件服务
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """根路径"""
    # 检查是否存在 index.html 文件，如果存在则返回前端页面
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "ELEVEN Blog Turner",
        "version": "0.1.0",
        "status": "running"
    }

# 处理前端路由，所有未匹配的路径都返回 index.html
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """服务 SPA 应用"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "error": "Not found"
    }

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