"""
SystemAgent 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import SystemAgent, AgentContext


class TestSystemAgent:
    """SystemAgent 测试类"""

    @pytest.fixture
    def system_agent(self):
        """创建 SystemAgent 实例"""
        return SystemAgent()

    @pytest.fixture
    def agent_context(self):
        """创建 AgentContext 实例"""
        return AgentContext(
            task_id="test_task_001",
            user_input="获取系统配置",
            metadata={"query_type": "system_config"}
        )

    def test_initialization(self, system_agent):
        """测试 SystemAgent 初始化"""
        assert system_agent.name == "SystemAgent"
        assert "系统内任务状态查询和各种参数返回" in system_agent.description
        assert len(system_agent.tools) > 0

    def test_get_system_prompt(self, system_agent):
        """测试获取系统提示词"""
        prompt = system_agent.get_system_prompt()
        assert "SystemAgent" in prompt

    def test_add_tool(self, system_agent):
        """测试添加工具"""
        initial_count = len(system_agent.tools)
        def mock_func():
            pass
        result = system_agent.add_tool("mock_tool", mock_func)
        assert result is system_agent
        assert len(system_agent.tools) == initial_count + 1

    @pytest.mark.asyncio
    async def test_execute_system_config_query(self, system_agent, agent_context):
        """测试执行系统配置查询"""
        with patch.object(system_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "LLM配置: OpenAI, 模型: GPT-4"

            result = await system_agent.execute(agent_context)

            assert "LLM" in result or "配置" in result
            mock_call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_style_config_query(self, system_agent):
        """测试执行风格配置查询"""
        context = AgentContext(
            task_id="test_task_002",
            user_input="获取风格配置",
            metadata={"query_type": "style_config"}
        )

        with patch.object(system_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "风格配置: 简洁专业"

            result = await system_agent.execute(context)

            assert "风格" in result or "配置" in result

    @pytest.mark.asyncio
    async def test_execute_task_status_query(self, system_agent):
        """测试执行任务状态查询"""
        context = AgentContext(
            task_id="test_task_003",
            user_input="查询任务状态",
            metadata={"query_type": "task_status"}
        )

        with patch.object(system_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "任务状态: 进行中"

            result = await system_agent.execute(context)

            assert "任务" in result or "状态" in result

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, system_agent, agent_context):
        """测试带记忆功能的执行"""
        with patch.object(system_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "系统配置查询完成"

            # 添加记忆
            system_agent.add_to_memory("user", "查询系统配置")
            system_agent.add_to_memory("assistant", "系统配置: LLM配置已完成")

            # 执行
            result = await system_agent.execute(agent_context)

            # 验证记忆被使用
            history = system_agent.get_memory_history()
            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, system_agent, agent_context):
        """测试错误处理"""
        with patch.object(system_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.side_effect = Exception("LLM 调用失败")

            result = await system_agent.execute(agent_context)

            assert "错误" in result or "失败" in result

    @pytest.mark.asyncio
    async def test_build_messages(self, system_agent, agent_context):
        """测试消息构建"""
        messages = system_agent.build_messages(agent_context)

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"

    def test_validate_context(self, system_agent, agent_context):
        """测试上下文验证"""
        assert system_agent.validate_context(agent_context) is True

    @pytest.mark.asyncio
    async def test_execute_unknown_query_type(self, system_agent):
        """测试未知查询类型"""
        context = AgentContext(
            task_id="test_task_004",
            user_input="未知查询",
            metadata={"query_type": "unknown"}
        )

        with patch.object(system_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "无法识别查询类型"

            result = await system_agent.execute(context)

            assert result is not None
