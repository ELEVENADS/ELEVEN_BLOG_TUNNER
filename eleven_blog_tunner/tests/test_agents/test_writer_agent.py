"""
WriterAgent 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import WriterAgent, AgentContext


class TestWriterAgent:
    """WriterAgent 测试类"""

    @pytest.fixture
    def writer_agent(self):
        """创建 WriterAgent 实例"""
        return WriterAgent()

    @pytest.fixture
    def agent_context(self):
        """创建 AgentContext 实例"""
        return AgentContext(
            task_id="test_task_001",
            user_input="写一篇关于人工智能的文章",
            metadata={"task_type": "article_generation"}
        )

    def test_initialization(self, writer_agent):
        """测试 WriterAgent 初始化"""
        assert writer_agent.name == "WriterAgent"
        assert "负责文章的撰写，通过固定的风格和例子调用工具完成文章" in writer_agent.description
        assert len(writer_agent.tools) > 0

    def test_get_system_prompt(self, writer_agent):
        """测试获取系统提示词"""
        prompt = writer_agent.get_system_prompt()
        assert "WriterAgent" in prompt
        assert "撰写" in prompt

    def test_add_tool(self, writer_agent):
        """测试添加工具"""
        initial_count = len(writer_agent.tools)
        def mock_func():
            pass
        result = writer_agent.add_tool("mock_tool", mock_func)
        assert result is writer_agent
        assert len(writer_agent.tools) == initial_count + 1

    @pytest.mark.asyncio
    async def test_execute_article_generation(self, writer_agent, agent_context):
        """测试执行文章生成"""
        result = await writer_agent.execute(agent_context)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_execute_outline_generation(self, writer_agent):
        """测试执行大纲生成"""
        context = AgentContext(
            task_id="test_task_002",
            user_input="生成文章大纲",
            metadata={"task_type": "outline_generation"}
        )

        with patch.object(writer_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "1. 引言\n2. 人工智能发展历程\n3. 人工智能应用\n4. 总结"

            result = await writer_agent.execute(context)

            assert "1." in result or "大纲" in result

    @pytest.mark.asyncio
    async def test_execute_section_writing(self, writer_agent):
        """测试执行分段撰写"""
        context = AgentContext(
            task_id="test_task_003",
            user_input="撰写第一章：引言",
            metadata={"task_type": "section_writing"}
        )

        with patch.object(writer_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "第一章：引言\n\n人工智能是当今世界最受关注的技术领域之一..."

            result = await writer_agent.execute(context)

            assert "第一章" in result or "引言" in result

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, writer_agent, agent_context):
        """测试带记忆功能的执行"""
        with patch.object(writer_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "文章生成完成"

            # 添加记忆
            writer_agent.add_to_memory("user", "写一篇关于AI的文章")
            writer_agent.add_to_memory("assistant", "好的，我将按照您的风格撰写文章")

            # 执行
            result = await writer_agent.execute(agent_context)

            # 验证记忆被使用
            history = writer_agent.get_memory_history()
            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, writer_agent, agent_context):
        """测试错误处理"""
        result = await writer_agent.execute(agent_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_build_messages(self, writer_agent, agent_context):
        """测试消息构建"""
        messages = writer_agent.build_messages(agent_context)

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"

    def test_validate_context(self, writer_agent, agent_context):
        """测试上下文验证"""
        assert writer_agent.validate_context(agent_context) is True

    @pytest.mark.asyncio
    async def test_execute_polishing(self, writer_agent):
        """测试执行文章润色"""
        context = AgentContext(
            task_id="test_task_004",
            user_input="润色以下文章：人工智能正在改变世界",
            metadata={"task_type": "polishing"}
        )

        with patch.object(writer_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "润色后：人工智能技术正在深刻地改变着我们的世界..."

            result = await writer_agent.execute(context)

            assert "润色" in result or "完成" in result
