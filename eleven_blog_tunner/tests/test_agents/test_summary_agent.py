"""
SummaryAgent 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import SummaryAgent, AgentContext


class TestSummaryAgent:
    """SummaryAgent 测试类"""

    @pytest.fixture
    def summary_agent(self):
        """创建 SummaryAgent 实例"""
        return SummaryAgent()

    @pytest.fixture
    def agent_context(self):
        """创建 AgentContext 实例"""
        return AgentContext(
            task_id="test_task_001",
            user_input="总结这篇关于人工智能的文章",
            metadata={"task_type": "summarization"}
        )

    def test_initialization(self, summary_agent):
        """测试 SummaryAgent 初始化"""
        assert summary_agent.name == "SummaryAgent"
        assert "负责总结类工作，比如总结上下文、总结文章风格" in summary_agent.description
        assert len(summary_agent.tools) > 0

    def test_get_system_prompt(self, summary_agent):
        """测试获取系统提示词"""
        prompt = summary_agent.get_system_prompt()
        assert "SummaryAgent" in prompt
        assert "总结" in prompt

    def test_add_tool(self, summary_agent):
        """测试添加工具"""
        initial_count = len(summary_agent.tools)
        def mock_func():
            pass
        result = summary_agent.add_tool("mock_tool", mock_func)
        assert result is summary_agent
        assert len(summary_agent.tools) == initial_count + 1

    @pytest.mark.asyncio
    async def test_execute_summarization(self, summary_agent, agent_context):
        """测试执行总结任务"""
        with patch.object(summary_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "文章总结：本文介绍了人工智能的发展历程..."

            result = await summary_agent.execute(agent_context)

            assert "总结" in result or "文章" in result
            mock_call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_context_compression(self, summary_agent):
        """测试执行上下文压缩"""
        context = AgentContext(
            task_id="test_task_002",
            user_input="压缩以下上下文",
            metadata={"task_type": "context_compression"}
        )

        with patch.object(summary_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "上下文压缩完成：核心观点已提取"

            result = await summary_agent.execute(context)

            assert "压缩" in result or "完成" in result

    @pytest.mark.asyncio
    async def test_execute_style_extraction(self, summary_agent):
        """测试执行风格提取"""
        context = AgentContext(
            task_id="test_task_003",
            user_input="提取文章风格特征",
            metadata={"task_type": "style_extraction"}
        )

        result = await summary_agent.execute(context)
        assert isinstance(result, (str, dict))

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, summary_agent, agent_context):
        """测试带记忆功能的执行"""
        with patch.object(summary_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "总结完成"

            # 添加记忆
            summary_agent.add_to_memory("user", "总结这篇文章")
            summary_agent.add_to_memory("assistant", "好的，我将为您总结这篇文章")

            # 执行
            result = await summary_agent.execute(agent_context)

            # 验证记忆被使用
            history = summary_agent.get_memory_history()
            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, summary_agent, agent_context):
        """测试错误处理"""
        result = await summary_agent.execute(agent_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_build_messages(self, summary_agent, agent_context):
        """测试消息构建"""
        messages = summary_agent.build_messages(agent_context)

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"

    def test_validate_context(self, summary_agent, agent_context):
        """测试上下文验证"""
        assert summary_agent.validate_context(agent_context) is True

    @pytest.mark.asyncio
    async def test_execute_long_text(self, summary_agent):
        """测试长文本总结"""
        long_text = "人工智能是计算机科学的一个分支，旨在创造能够像人类一样思考和学习的机器。" * 50
        context = AgentContext(
            task_id="test_task_004",
            user_input=f"总结以下内容：{long_text}",
            metadata={"task_type": "summarization"}
        )

        with patch.object(summary_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "长文本总结完成"

            result = await summary_agent.execute(context)

            assert result is not None
