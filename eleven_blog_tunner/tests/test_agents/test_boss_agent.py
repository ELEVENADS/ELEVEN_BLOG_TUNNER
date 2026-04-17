"""
BossAgent 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import BossAgent, AgentContext


class TestBossAgent:
    """BossAgent 测试类"""

    @pytest.fixture
    def boss_agent(self):
        """创建 BossAgent 实例"""
        return BossAgent()

    @pytest.fixture
    def agent_context(self):
        """创建 AgentContext 实例"""
        return AgentContext(
            task_id="test_task_001",
            user_input="写一篇关于人工智能的文章",
            metadata={"task_type": "article_generation"}
        )

    def test_initialization(self, boss_agent):
        """测试 BossAgent 初始化"""
        assert boss_agent.name == "BossAgent"
        assert boss_agent.description == "统筹系统任务调度和信息返回"
        assert boss_agent.tools == []

    def test_get_system_prompt(self, boss_agent):
        """测试获取系统提示词"""
        prompt = boss_agent.get_system_prompt()
        assert "BossAgent" in prompt
        assert "统筹系统任务调度" in prompt

    def test_add_tool(self, boss_agent):
        """测试添加工具"""
        mock_tool = MagicMock()
        result = boss_agent.add_tool(mock_tool)
        assert result is boss_agent
        assert len(boss_agent.tools) == 1

    @pytest.mark.asyncio
    async def test_execute_article_generation(self, boss_agent, agent_context):
        """测试执行文章生成任务"""
        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "文章生成完成：关于人工智能的文章"

            result = await boss_agent.execute(agent_context)

            assert "文章" in result
            mock_call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_style_query(self, boss_agent):
        """测试执行风格查询任务"""
        context = AgentContext(
            task_id="test_task_002",
            user_input="查询当前风格配置",
            metadata={"task_type": "style_query"}
        )

        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "当前风格配置：简洁专业"

            result = await boss_agent.execute(context)

            assert "风格" in result or "配置" in result
            mock_call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, boss_agent, agent_context):
        """测试带记忆功能的执行"""
        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "文章生成完成"

            # 添加记忆
            boss_agent.add_to_memory("user", "我需要一篇技术文章")
            boss_agent.add_to_memory("assistant", "好的，我将为您生成一篇技术文章")

            # 执行
            result = await boss_agent.execute(agent_context)

            # 验证记忆被使用
            history = boss_agent.get_memory_history()
            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_execute_with_sub_agent(self, boss_agent, agent_context):
        """测试带子Agent调用的执行"""
        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "任务调度完成"

            with patch.object(boss_agent, 'call_agent', new_callable=AsyncMock) as mock_call_agent:
                mock_call_agent.return_value = {
                    "success": True,
                    "result": "SystemAgent查询完成"
                }

                result = await boss_agent.execute(agent_context)

                assert result is not None

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, boss_agent, agent_context):
        """测试错误处理"""
        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.side_effect = Exception("LLM 调用失败")

            result = await boss_agent.execute(agent_context)

            assert "错误" in result or "失败" in result

    @pytest.mark.asyncio
    async def test_build_messages(self, boss_agent, agent_context):
        """测试消息构建"""
        messages = boss_agent.build_messages(agent_context)

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert any(msg["role"] == "user" for msg in messages)

    def test_validate_context(self, boss_agent, agent_context):
        """测试上下文验证"""
        assert boss_agent.validate_context(agent_context) is True

    @pytest.mark.asyncio
    async def test_execute_empty_input(self, boss_agent):
        """测试空输入处理"""
        context = AgentContext(
            task_id="test_task_003",
            user_input="",
            metadata={}
        )

        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "请提供有效的输入"

            result = await boss_agent.execute(context)

            assert result is not None
