"""
启动脚本 - 从项目根目录运行
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入模块了
from eleven_blog_tunner.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "eleven_blog_tunner.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
