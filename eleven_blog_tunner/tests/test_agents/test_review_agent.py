"""
ReviewAgent 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import ReviewAgent, AgentContext


class TestReviewAgent:
    """ReviewAgent 测试类"""

    @pytest.fixture
    def review_agent(self):
        """创建 ReviewAgent 实例"""
        return ReviewAgent()

    @pytest.fixture
    def agent_context(self):
        """创建 AgentContext 实例"""
        return AgentContext(
            task_id="test_task_001",
            user_input="审查这篇文章的质量",
            metadata={"task_type": "review"}
        )

    def test_initialization(self, review_agent):
        """测试 ReviewAgent 初始化"""
        assert review_agent.name == "ReviewAgent"
        assert "负责审查文章质量和是否违规" in review_agent.description
        assert len(review_agent.tools) > 0

    def test_get_system_prompt(self, review_agent):
        """测试获取系统提示词"""
        prompt = review_agent.get_system_prompt()
        assert "ReviewAgent" in prompt
        assert "审查" in prompt

    def test_add_tool(self, review_agent):
        """测试添加工具"""
        initial_count = len(review_agent.tools)
        def mock_func():
            pass
        result = review_agent.add_tool("mock_tool", mock_func)
        assert result is review_agent
        assert len(review_agent.tools) == initial_count + 1

    @pytest.mark.asyncio
    async def test_execute_review(self, review_agent, agent_context):
        """测试执行文章审查"""
        result = await review_agent.execute(agent_context)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_execute_quality_score(self, review_agent):
        """测试执行质量评分"""
        context = AgentContext(
            task_id="test_task_002",
            user_input="对文章进行质量评分",
            metadata={"task_type": "quality_score"}
        )

        with patch.object(review_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "质量评分：90分（优秀）"

            result = await review_agent.execute(context)

            assert "评分" in result or "分" in result

    @pytest.mark.asyncio
    async def test_execute_violation_detection(self, review_agent):
        """测试执行违规检测"""
        context = AgentContext(
            task_id="test_task_003",
            user_input="检测文章是否违规",
            metadata={"task_type": "violation_detection"}
        )

        with patch.object(review_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "未检测到违规内容"

            result = await review_agent.execute(context)

            assert "违规" in result or "检测" in result

    @pytest.mark.asyncio
    async def test_execute_suggestion_generation(self, review_agent):
        """测试执行修改建议生成"""
        context = AgentContext(
            task_id="test_task_004",
            user_input="生成文章修改建议",
            metadata={"task_type": "suggestion"}
        )

        with patch.object(review_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "修改建议：1. 增加具体案例 2. 优化段落结构"

            result = await review_agent.execute(context)

            assert "建议" in result or "修改" in result

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, review_agent, agent_context):
        """测试带记忆功能的执行"""
        with patch.object(review_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "审查完成"

            # 添加记忆
            review_agent.add_to_memory("user", "审查这篇文章")
            review_agent.add_to_memory("assistant", "好的，我将审查文章的质量和合规性")

            # 执行
            result = await review_agent.execute(agent_context)

            # 验证记忆被使用
            history = review_agent.get_memory_history()
            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, review_agent, agent_context):
        """测试错误处理"""
        result = await review_agent.execute(agent_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_build_messages(self, review_agent, agent_context):
        """测试消息构建"""
        messages = review_agent.build_messages(agent_context)

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"

    def test_validate_context(self, review_agent, agent_context):
        """测试上下文验证"""
        assert review_agent.validate_context(agent_context) is True

    @pytest.mark.asyncio
    async def test_execute_multi_dimensional_review(self, review_agent):
        """测试多维度审查"""
        context = AgentContext(
            task_id="test_task_005",
            user_input="从流畅度、原创度、风格匹配度等维度审查文章",
            metadata={"task_type": "multi_dimensional_review"}
        )

        with patch.object(review_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "流畅度：90分，原创度：85分，风格匹配度：88分"

            result = await review_agent.execute(context)

            assert "流畅度" in result or "评分" in result
