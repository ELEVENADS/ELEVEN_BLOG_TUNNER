import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def project_path():
    return project_root

@pytest.fixture(scope="session")
def sample_user_data():
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password_123"
    }

@pytest.fixture(scope="session")
def sample_note_data():
    return {
        "title": "测试笔记",
        "content": "这是一篇测试笔记的内容",
        "source_type": "markdown"
    }

@pytest.fixture(scope="session")
def sample_style_data():
    return {
        "name": "测试风格",
        "description": "用于测试的风格"
    }

@pytest.fixture(scope="session")
def sample_article_data():
    return {
        "title": "测试文章标题",
        "source_topic": "测试主题"
    }
