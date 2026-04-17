"""
Agent 集成测试
端到端流程测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from eleven_blog_tunner.agents import (
    BossAgent, SystemAgent, SummaryAgent, WriterAgent, ReviewAgent,
    AgentContext, get_protocol, AgentProtocol
)
from eleven_blog_tunner.gateway import TaskManager, APIHandler, StatusMonitor, Integration


class TestAgentIntegration:
    """Agent 集成测试类"""

    @pytest.fixture
    def agent_protocol(self):
        """创建 AgentProtocol 实例"""
        protocol = get_protocol()
        # 确保所有 Agent 都已注册
        return protocol

    @pytest.fixture
    def task_manager(self):
        """创建 TaskManager 实例"""
        return TaskManager()

    @pytest.fixture
    def api_handler(self, task_manager):
        """创建 APIHandler 实例"""
        handler = APIHandler()
        # 模拟任务管理器
        handler.task_manager = task_manager
        return handler

    @pytest.fixture
    def integration(self):
        """创建 Integration 实例"""
        return Integration()

    @pytest.mark.asyncio
    async def test_complete_article_generation_flow(self, agent_protocol):
        """测试完整的文章生成流程"""
        # 模拟所有 Agent 的 execute 方法
        with patch.object(BossAgent, 'execute', new_callable=AsyncMock) as mock_boss_execute:
            mock_boss_execute.return_value = "BossAgent 已协调完成文章生成"

            with patch.object(SystemAgent, 'execute', new_callable=AsyncMock) as mock_system_execute:
                mock_system_execute.return_value = "风格配置: 简洁专业"

                with patch.object(SummaryAgent, 'execute', new_callable=AsyncMock) as mock_summary_execute:
                    mock_summary_execute.return_value = "文章大纲: 1. 引言 2. 发展历程 3. 应用 4. 总结"

                    with patch.object(WriterAgent, 'execute', new_callable=AsyncMock) as mock_writer_execute:
                        mock_writer_execute.return_value = "# 人工智能的发展\n\n人工智能技术正在快速发展..."

                        with patch.object(ReviewAgent, 'execute', new_callable=AsyncMock) as mock_review_execute:
                            mock_review_execute.return_value = "质量评分: 90分，质量优秀"

                            # 执行完整的文章生成流程
                            result = await agent_protocol.execute_task(
                                task="article_generation",
                                initial_input="写一篇关于人工智能的文章",
                                agent_sequence=[
                                    "BossAgent",
                                    "SystemAgent",
                                    "SummaryAgent",
                                    "WriterAgent",
                                    "ReviewAgent"
                                ]
                            )

                            # 验证结果
                            assert result["success"] is True
                            assert "文章" in result["result"] or "完成" in result["result"]

                            # 验证所有 Agent 都被调用
                            mock_boss_execute.assert_called_once()
                            mock_system_execute.assert_called_once()
                            mock_summary_execute.assert_called_once()
                            mock_writer_execute.assert_called_once()
                            mock_review_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_gateway_task_flow(self, task_manager):
        """测试 Gateway 层的任务流程"""
        # 模拟任务执行
        with patch.object(TaskManager, '_process_task', new_callable=AsyncMock) as mock_process_task:
            # 创建任务
            task_id = await task_manager.create_task(
                task_type="article_generation",
                input_data="写一篇关于人工智能的文章",
                user_id="user123"
            )

            # 验证任务创建
            assert task_id is not None
            assert task_id in task_manager.tasks

            # 验证任务状态
            task = task_manager.tasks[task_id]
            assert task.status.value == "pending"
            assert task.task_type == "article_generation"
            assert task.user_id == "user123"

    @pytest.mark.asyncio
    async def test_api_handler_integration(self, api_handler, task_manager):
        """测试 APIHandler 集成"""
        # 模拟任务创建
        with patch.object(TaskManager, 'create_task', new_callable=AsyncMock) as mock_create_task:
            mock_create_task.return_value = "test_task_001"

            # 测试创建任务
            response = await api_handler.create_task(
                task_type="article_generation",
                input_data="写一篇关于人工智能的文章",
                user_id="user123"
            )

            assert response["success"] is True
            assert response["task_id"] == "test_task_001"
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_integration_with_agents(self, integration):
        """测试 Integration 与 Agent 的集成"""
        # 模拟 BossAgent 调用
        with patch.object(integration, 'call_boss_agent', new_callable=AsyncMock) as mock_call_boss:
            mock_call_boss.return_value = {
                "success": True,
                "result": "BossAgent 执行完成"
            }

            # 模拟 SystemAgent 调用
            with patch.object(integration, 'call_system_agent', new_callable=AsyncMock) as mock_call_system:
                mock_call_system.return_value = {
                    "success": True,
                    "result": "系统配置: LLM=OpenAI"
                }

                # 测试执行任务链
                result = await integration.execute_task_chain(
                    task_type="article_generation",
                    input_data="写一篇关于人工智能的文章",
                    task_id="test_task_001"
                )

                assert result["success"] is True
                mock_call_boss.assert_called_once()
                mock_call_system.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, agent_protocol):
        """测试集成错误处理"""
        # 模拟 BossAgent 执行失败
        with patch.object(BossAgent, 'execute', new_callable=AsyncMock) as mock_boss_execute:
            mock_boss_execute.side_effect = Exception("BossAgent 执行失败")

            # 执行任务
            result = await agent_protocol.execute_task(
                task="article_generation",
                initial_input="写一篇关于人工智能的文章",
                agent_sequence=["BossAgent"]
            )

            # 验证错误处理
            assert result["success"] is False
            assert "失败" in result["error"]

    @pytest.mark.asyncio
    async def test_memory_integration(self):
        """测试记忆系统集成"""
        # 创建 BossAgent
        boss_agent = BossAgent()

        # 添加记忆
        boss_agent.add_to_memory("user", "我需要一篇技术文章")
        boss_agent.add_to_memory("assistant", "好的，我将为您生成一篇技术文章")

        # 创建上下文
        context = AgentContext(
            task_id="test_task_001",
            user_input="关于人工智能的",
            metadata={"task_type": "article_generation"}
        )

        # 模拟 LLM 调用
        with patch.object(boss_agent, 'call_llm', new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = "文章生成完成"

            # 执行
            result = await boss_agent.execute(context)

            # 验证记忆被使用
            history = boss_agent.get_memory_history()
            assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_agent_chain_integration(self, agent_protocol):
        """测试 Agent 链式调用"""
        # 模拟 Agent 调用
        with patch.object(agent_protocol, 'call_agent', new_callable=AsyncMock) as mock_call_agent:
            # 模拟不同 Agent 的返回
            mock_call_agent.side_effect = [
                {"success": True, "result": "BossAgent 开始处理"},
                {"success": True, "result": "SystemAgent 获取配置"},
                {"success": True, "result": "WriterAgent 撰写文章"},
                {"success": True, "result": "ReviewAgent 审查完成"}
            ]

            # 执行任务
            result = await agent_protocol.execute_task(
                task="article_generation",
                initial_input="写一篇关于人工智能的文章",
                agent_sequence=[
                    "BossAgent",
                    "SystemAgent",
                    "WriterAgent",
                    "ReviewAgent"
                ]
            )

            # 验证链式调用
            assert result["success"] is True
            assert mock_call_agent.call_count == 4

    @pytest.mark.asyncio
    async def test_status_monitor_integration(self, task_manager):
        """测试状态监控集成"""
        from eleven_blog_tunner.gateway.status_monitor import StatusMonitor

        # 创建状态监控
        status_monitor = StatusMonitor(task_manager)

        # 启动监控
        await status_monitor.start()

        try:
            # 获取系统状态
            system_status = await status_monitor.get_system_status()
            assert system_status is not None
            assert "system" in system_status
            assert "resources" in system_status
            assert "tasks" in system_status

            # 获取任务统计
            task_stats = await status_monitor.get_task_stats()
            assert task_stats is not None

            # 获取资源使用
            resource_usage = await status_monitor.get_resource_usage()
            assert resource_usage is not None
        finally:
            # 停止监控
            await status_monitor.stop()

    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, task_manager, api_handler):
        """测试完整工作流集成"""
        # 启动任务管理器
        await task_manager.start()

        try:
            # 1. 创建任务
            task_id = await task_manager.create_task(
                task_type="article_generation",
                input_data="写一篇关于人工智能的文章",
                user_id="user123"
            )

            # 2. 获取任务状态
            status = await task_manager.get_task_status(task_id)
            assert status["status"] == "pending"

            # 3. 模拟任务完成
            task = task_manager.tasks[task_id]
            task.set_result("文章生成完成")

            # 4. 获取任务结果
            result = await task_manager.get_task_result(task_id)
            assert result == "文章生成完成"

            # 5. 测试 API 接口
            api_response = await api_handler.get_task_status(task_id)
            assert api_response["success"] is True
            assert api_response["data"]["status"] == "completed"

        finally:
            # 停止任务管理器
            await task_manager.stop()

    @pytest.mark.asyncio
    async def test_health_check_integration(self, integration):
        """测试健康检查集成"""
        # 测试 Integration 健康检查
        health = await integration.health_check()
        assert health is not None
        assert "status" in health

        # 测试 APIHandler 健康检查
        api_handler = APIHandler()
        health_check = await api_handler.health_check()
        assert health_check["success"] is True
        assert health_check["status"] in ["healthy", "unhealthy"]
