import os
from dotenv import load_dotenv

def load_env_from_root(levels_up: int = 1):
    """
    通用加载 .env 工具函数
    :param levels_up: 从当前文件 往上退几层 到达项目根目录
    """
    # 1. 获取当前调用这个函数的文件的绝对路径
    current_file_path = os.path.abspath(__file__)

    # 2. 从当前路径开始，往上跳 levels_up 次，到达根目录
    root_dir = current_file_path
    for _ in range(levels_up):
        root_dir = os.path.dirname(root_dir)

    # 3. 加载根目录的 .env 文件
    env_path = os.path.join(root_dir, ".env")
    load_dotenv(env_path)

    # 可选：返回根目录，方便其他地方使用
    return root_dir
