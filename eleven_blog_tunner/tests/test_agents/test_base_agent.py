import pytest
from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentContext

class MockAgent(BaseAgent):
    """测试用 Agent 实现"""

    async def execute(self, context: AgentContext) -> str:
        return f"Processed: {context.user_input}"


class TestAgentContext:
    def test_agent_context_creation(self):
        context = AgentContext(
            task_id="task123",
            user_input="test input"
        )
        assert context.task_id == "task123"
        assert context.user_input == "test input"
        assert context.history == []
        assert context.metadata == {}

    def test_agent_context_with_metadata(self):
        context = AgentContext(
            task_id="task123",
            user_input="test",
            metadata={"key": "value"}
        )
        assert context.metadata["key"] == "value"

    def test_agent_context_with_history(self):
        context = AgentContext(
            task_id="task123",
            user_input="test",
            history=[{"role": "user", "content": "hello"}]
        )
        assert len(context.history) == 1


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_agent_execute_returns_string(self):
        agent = MockAgent(name="test_agent", description="A test agent")
        context = AgentContext(task_id="t1", user_input="test task")
        result = await agent.execute(context)
        assert isinstance(result, str)
        assert "Processed" in result

    def test_agent_name_assignment(self):
        agent = MockAgent(name="my_agent", description="desc")
        assert agent.name == "my_agent"
        assert agent.description == "desc"

    def test_agent_get_system_prompt(self):
        agent = MockAgent(name="test", description="A test agent")
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert "test" in prompt

    def test_agent_add_tool(self):
        agent = MockAgent(name="test", description="desc")
        assert len(agent.tools) == 0
        agent.add_tool("mock_tool")
        assert len(agent.tools) == 1
        assert agent.tools[0] == "mock_tool"
