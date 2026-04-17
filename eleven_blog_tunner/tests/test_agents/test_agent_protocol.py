"""
Agent Protocol 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import AgentProtocol, AgentCallChain, TaskContext, MessageType, TaskStatus, get_protocol


class TestAgentProtocol:
    """AgentProtocol 测试类"""

    @pytest.fixture
    def agent_protocol(self):
        """创建 AgentProtocol 实例"""
        return AgentProtocol()

    @pytest.fixture
    def task_context(self):
        """创建 TaskContext 实例"""
        return TaskContext(
            task_id="test_task_001",
            task_type="article_generation",
            input_data="写一篇关于人工智能的文章"
        )

    def test_initialization(self, agent_protocol):
        """测试 AgentProtocol 初始化"""
        assert agent_protocol is not None
        assert hasattr(agent_protocol, 'agents')
        assert hasattr(agent_protocol, 'call_chains')

    def test_register_agent(self, agent_protocol):
        """测试注册 Agent"""
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"

        result = agent_protocol.register_agent(mock_agent)

        assert result is agent_protocol
        assert "TestAgent" in agent_protocol.agents

    def test_get_agent(self, agent_protocol):
        """测试获取 Agent"""
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        agent_protocol.register_agent(mock_agent)

        retrieved_agent = agent_protocol.get_agent("TestAgent")
        assert retrieved_agent is mock_agent

        not_found_agent = agent_protocol.get_agent("NonExistentAgent")
        assert not_found_agent is None

    @pytest.mark.asyncio
    async def test_call_agent_success(self, agent_protocol):
        """测试成功调用 Agent"""
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        mock_agent.execute = AsyncMock(return_value="Task completed")

        agent_protocol.register_agent(mock_agent)

        result = await agent_protocol.call_agent(
            caller="Gateway",
            callee="TestAgent",
            input_data="Test input"
        )

        assert result["success"] is True
        assert result["result"] == "Task completed"
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_agent_not_found(self, agent_protocol):
        """测试调用不存在的 Agent"""
        result = await agent_protocol.call_agent(
            caller="Gateway",
            callee="NonExistentAgent",
            input_data="Test input"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_call_agent_error(self, agent_protocol):
        """测试 Agent 执行错误"""
        mock_agent = MagicMock()
        mock_agent.name = "ErrorAgent"
        mock_agent.execute = AsyncMock(side_effect=Exception("Execution failed"))

        agent_protocol.register_agent(mock_agent)

        result = await agent_protocol.call_agent(
            caller="Gateway",
            callee="ErrorAgent",
            input_data="Test input"
        )

        assert result["success"] is False
        assert "Execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_task(self, agent_protocol):
        """测试执行任务"""
        mock_boss_agent = MagicMock()
        mock_boss_agent.name = "BossAgent"
        mock_boss_agent.execute = AsyncMock(return_value="Task completed by BossAgent")

        agent_protocol.register_agent(mock_boss_agent)

        result = await agent_protocol.execute_task(
            task="article_generation",
            initial_input="写一篇关于人工智能的文章",
            agent_sequence=["BossAgent"]
        )

        assert result["success"] is True
        assert "BossAgent" in result["result"]

    @pytest.mark.asyncio
    async def test_execute_task_with_multiple_agents(self, agent_protocol):
        """测试多 Agent 协作执行任务"""
        mock_boss_agent = MagicMock()
        mock_boss_agent.name = "BossAgent"
        mock_boss_agent.execute = AsyncMock(return_value="BossAgent completed")

        mock_writer_agent = MagicMock()
        mock_writer_agent.name = "WriterAgent"
        mock_writer_agent.execute = AsyncMock(return_value="WriterAgent completed")

        agent_protocol.register_agent(mock_boss_agent)
        agent_protocol.register_agent(mock_writer_agent)

        result = await agent_protocol.execute_task(
            task="article_generation",
            initial_input="写一篇关于人工智能的文章",
            agent_sequence=["BossAgent", "WriterAgent"]
        )

        assert result["success"] is True
        mock_boss_agent.execute.assert_called_once()
        mock_writer_agent.execute.assert_called_once()


class TestAgentCallChain:
    """AgentCallChain 测试类"""

    @pytest.fixture
    def agent_call_chain(self):
        """创建 AgentCallChain 实例"""
        return AgentCallChain()

    def test_initialization(self, agent_call_chain):
        """测试 AgentCallChain 初始化"""
        assert agent_call_chain is not None
        assert agent_call_chain.call_chains == {}

    def test_start_call(self, agent_call_chain):
        """测试开始调用"""
        result = agent_call_chain.start_call(
            task_id="test_task_001",
            caller="Gateway",
            callee="BossAgent"
        )

        assert result is True
        assert "test_task_001" in agent_call_chain.call_chains
        assert "BossAgent" in agent_call_chain.call_chains["test_task_001"]

    def test_start_call_chain_limit(self, agent_call_chain):
        """测试调用链深度限制"""
        task_id = "test_task_001"

        # 添加多个调用直到超过限制
        for i in range(11):
            agent_call_chain.start_call(task_id, f"Agent{i}", f"Agent{i+1}")

        # 再次调用应该失败
        result = agent_call_chain.start_call(task_id, "Agent10", "Agent11")
        assert result is False

    def test_end_call(self, agent_call_chain):
        """测试结束调用"""
        task_id = "test_task_001"
        agent_call_chain.start_call(task_id, "Gateway", "BossAgent")
        agent_call_chain.start_call(task_id, "BossAgent", "WriterAgent")

        result = agent_call_chain.end_call(task_id)

        assert result is True
        assert "WriterAgent" not in agent_call_chain.call_chains.get(task_id, [])

    def test_get_call_chain(self, agent_call_chain):
        """测试获取调用链"""
        task_id = "test_task_001"
        agent_call_chain.start_call(task_id, "Gateway", "BossAgent")
        agent_call_chain.start_call(task_id, "BossAgent", "WriterAgent")

        chain = agent_call_chain.get_call_chain(task_id)

        assert len(chain) == 2
        assert "Gateway" in chain
        assert "BossAgent" in chain
        assert "WriterAgent" in chain

    def test_check_circular_call(self, agent_call_chain):
        """测试循环调用检测"""
        task_id = "test_task_001"
        agent_call_chain.start_call(task_id, "Gateway", "BossAgent")
        agent_call_chain.start_call(task_id, "BossAgent", "WriterAgent")

        # 检测循环调用
        result = agent_call_chain.check_circular_call(task_id, "Gateway")
        assert result is True  # Gateway 已经在链中

        result = agent_call_chain.check_circular_call(task_id, "NewAgent")
        assert result is False  # NewAgent 不在链中

    def test_clear_chain(self, agent_call_chain):
        """测试清除调用链"""
        task_id = "test_task_001"
        agent_call_chain.start_call(task_id, "Gateway", "BossAgent")
        agent_call_chain.start_call(task_id, "BossAgent", "WriterAgent")

        result = agent_call_chain.clear_chain(task_id)

        assert result is True
        assert task_id not in agent_call_chain.call_chains


class TestTaskContext:
    """TaskContext 测试类"""

    def test_initialization(self):
        """测试 TaskContext 初始化"""
        context = TaskContext(
            task_id="test_task_001",
            task_type="article_generation",
            input_data="写一篇关于人工智能的文章"
        )

        assert context.task_id == "test_task_001"
        assert context.task_type == "article_generation"
        assert context.input_data == "写一篇关于人工智能的文章"
        assert context.status == TaskStatus.PENDING
        assert context.metadata == {}

    def test_update_status(self):
        """测试更新状态"""
        context = TaskContext(
            task_id="test_task_001",
            task_type="article_generation",
            input_data="Test"
        )

        context.update_status(TaskStatus.RUNNING)
        assert context.status == TaskStatus.RUNNING

        context.update_status(TaskStatus.COMPLETED)
        assert context.status == TaskStatus.COMPLETED

    def test_set_result(self):
        """测试设置结果"""
        context = TaskContext(
            task_id="test_task_001",
            task_type="article_generation",
            input_data="Test"
        )

        context.set_result("Task completed")
        assert context.result == "Task completed"
        assert context.status == TaskStatus.COMPLETED

    def test_set_error(self):
        """测试设置错误"""
        context = TaskContext(
            task_id="test_task_001",
            task_type="article_generation",
            input_data="Test"
        )

        context.set_error("Task failed")
        assert context.error == "Task failed"
        assert context.status == TaskStatus.FAILED


class TestGetProtocol:
    """get_protocol 测试类"""

    def test_get_protocol_singleton(self):
        """测试 get_protocol 单例模式"""
        protocol1 = get_protocol()
        protocol2 = get_protocol()

        assert protocol1 is protocol2
