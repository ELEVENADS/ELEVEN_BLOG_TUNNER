"""
API 端到端测试

测试文章生成和风格学习 API 的完整流程
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from eleven_blog_tunner.main import app


client = TestClient(app)


class TestAPIEndToEnd:
    """API 端到端测试"""

    @pytest.mark.skip(reason="需要网络连接，暂时跳过")
    @pytest.mark.asyncio
    async def test_style_learning_flow(self):
        """测试风格学习完整流程"""
        # 1. 从文本学习风格
        style_data = {
            "text": "这是一个测试文本，用于学习写作风格。\n\n我喜欢简洁明了的表达方式，避免冗长的句子。\n\n写作时要注意逻辑清晰，层次分明。",
            "style_name": "test_style_1",
            "metadata": {"source": "test"}
        }

        response = client.post("/api/v1/styles/learn", json=style_data)
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "test_style_1"
        assert "features" in result
        assert "vector" in result

        # 2. 获取风格列表
        response = client.get("/api/v1/styles/list")
        assert response.status_code == 200
        styles = response.json()
        assert "success" in styles
        assert "test_style_1" in styles["styles"]

        # 3. 获取风格详情
        response = client.get("/api/v1/styles/test_style_1")
        assert response.status_code == 200
        style_detail = response.json()
        assert style_detail["name"] == "test_style_1"

        # 4. 预览风格特征
        test_content = "这是一个测试内容，用于预览风格特征。"
        files = {
            "file": ("test.txt", test_content.encode("utf-8"), "text/plain")
        }
        data = {
            "style_name": "test_style_1"
        }

        response = client.post("/api/v1/styles/preview", files=files, data=data)
        assert response.status_code == 200
        preview_result = response.json()
        assert "success" in preview_result
        assert "features" in preview_result
        assert "similarity" in preview_result

    @pytest.mark.skip(reason="需要网络连接，暂时跳过")
    @pytest.mark.asyncio
    async def test_article_generation_flow(self):
        """测试文章生成完整流程"""
        # 1. 生成文章
        article_data = {
            "topic": "人工智能在教育中的应用",
            "style_name": "test_style_1",
            "target_length": 500
        }

        response = client.post("/api/v1/articles/generate", json=article_data)
        assert response.status_code == 200
        generation_result = response.json()
        assert "task_id" in generation_result
        assert generation_result["status"] == "generating"

        task_id = generation_result["task_id"]

        # 2. 等待文章生成完成（模拟异步处理）
        await asyncio.sleep(2)

        # 3. 获取文章详情
        response = client.get(f"/api/v1/articles/{task_id}")
        assert response.status_code == 200
        article = response.json()
        assert article["id"] == task_id
        assert article["topic"] == "人工智能在教育中的应用"
        assert article["style_name"] == "test_style_1"
        assert len(article["content"]) > 0

        # 4. 生成大纲
        outline_data = {
            "topic": "人工智能在教育中的应用",
            "style_name": "test_style_1"
        }

        response = client.post(f"/api/v1/articles/{task_id}/outline", json=outline_data)
        assert response.status_code == 200
        outline_result = response.json()
        assert "outline" in outline_result
        assert len(outline_result["outline"]) > 0

        # 5. 润色文章
        response = client.post(f"/api/v1/articles/{task_id}/polish")
        assert response.status_code == 200
        polish_result = response.json()
        assert len(polish_result["content"]) > 0

        # 6. 提交审核
        response = client.post(f"/api/v1/articles/{task_id}/review")
        assert response.status_code == 200
        review_result = response.json()
        assert review_result["success"]

        # 7. 审核通过
        response = client.post(f"/api/v1/articles/{task_id}/approve")
        assert response.status_code == 200
        approve_result = response.json()
        assert approve_result["success"]

    @pytest.mark.skip(reason="需要网络连接，暂时跳过")
    @pytest.mark.asyncio
    async def test_article_management_flow(self):
        """测试文章管理完整流程"""
        # 1. 生成文章
        article_data = {
            "topic": "测试文章管理",
            "target_length": 300
        }

        response = client.post("/api/v1/articles/generate", json=article_data)
        assert response.status_code == 200
        generation_result = response.json()
        task_id = generation_result["task_id"]

        await asyncio.sleep(2)

        # 2. 获取文章列表
        response = client.get("/api/v1/articles")
        assert response.status_code == 200
        articles_list = response.json()
        assert "articles" in articles_list
        assert len(articles_list["articles"]) > 0

        # 3. 更新文章
        updated_content = "这是更新后的文章内容。"
        response = client.put(f"/api/v1/articles/{task_id}", json={"content": updated_content})
        assert response.status_code == 200
        updated_article = response.json()
        assert updated_article["content"] == updated_content

        # 4. 删除文章
        response = client.delete(f"/api/v1/articles/{task_id}")
        assert response.status_code == 200
        delete_result = response.json()
        assert delete_result["success"]

        # 5. 验证文章已删除
        response = client.get(f"/api/v1/articles/{task_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        # 1. 测试不存在的风格
        response = client.get("/api/v1/styles/nonexistent_style")
        assert response.status_code == 404

        # 2. 测试不存在的文章
        response = client.get("/api/v1/articles/nonexistent_article")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])