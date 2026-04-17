"""
性能测试模块

验证系统性能优化效果
"""
import pytest
import asyncio
import time
from eleven_blog_tunner.agents.boss_agent import BossAgent
from eleven_blog_tunner.agents.base_agent import AgentContext
from eleven_blog_tunner.core.cache import llm_cache, tool_cache


@pytest.fixture
async def boss_agent():
    """创建BossAgent实例"""
    agent = BossAgent(llm_provider="openai", use_memory=True)
    yield agent
    # 清理缓存
    llm_cache.clear()
    tool_cache.clear()


async def test_async_concurrency_performance(boss_agent):
    """测试异步并发性能"""
    # 创建多个上下文
    contexts = []
    for i in range(3):
        context = AgentContext(
            user_input=f"生成一篇关于Python编程的文章 {i+1}",
            metadata={}
        )
        contexts.append(context)
    
    # 测量串行执行时间
    start_time = time.time()
    for context in contexts:
        await boss_agent.execute(context)
    serial_time = time.time() - start_time
    print(f"串行执行时间: {serial_time:.2f}秒")
    
    # 测量并行执行时间
    start_time = time.time()
    await asyncio.gather(*[boss_agent.execute(context) for context in contexts])
    parallel_time = time.time() - start_time
    print(f"并行执行时间: {parallel_time:.2f}秒")
    
    # 验证并行执行比串行快
    assert parallel_time < serial_time
    print(f"性能提升: {((serial_time - parallel_time) / serial_time) * 100:.2f}%")


async def test_llm_cache_performance(boss_agent):
    """测试LLM缓存性能"""
    context = AgentContext(
        user_input="生成一篇关于人工智能的文章",
        metadata={}
    )
    
    # 第一次调用（无缓存）
    start_time = time.time()
    await boss_agent.execute(context)
    first_time = time.time() - start_time
    print(f"第一次调用时间: {first_time:.2f}秒")
    
    # 第二次调用（有缓存）
    start_time = time.time()
    await boss_agent.execute(context)
    second_time = time.time() - start_time
    print(f"第二次调用时间: {second_time:.2f}秒")
    
    # 验证缓存生效
    assert second_time < first_time
    print(f"缓存性能提升: {((first_time - second_time) / first_time) * 100:.2f}%")


async def test_tool_cache_performance():
    """测试工具缓存性能"""
    from eleven_blog_tunner.agents.base_agent import BaseAgent, AgentType
    
    # 创建一个测试Agent
    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__(
                name="TestAgent",
                description="Test agent",
                agent_type=AgentType.SYSTEM,
                use_memory=False
            )
        
        async def execute(self, context):
            # 调用测试工具
            result = await self.call_tool("test_tool", value=42)
            return result
    
    agent = TestAgent()
    
    # 添加一个耗时的测试工具
    def test_tool(value):
        # 模拟耗时操作
        time.sleep(0.5)
        return f"Result: {value}"
    
    agent.add_tool("test_tool", test_tool)
    
    context = AgentContext(
        user_input="test",
        metadata={}
    )
    
    # 第一次调用（无缓存）
    start_time = time.time()
    await agent.execute(context)
    first_time = time.time() - start_time
    print(f"第一次工具调用时间: {first_time:.2f}秒")
    
    # 第二次调用（有缓存）
    start_time = time.time()
    await agent.execute(context)
    second_time = time.time() - start_time
    print(f"第二次工具调用时间: {second_time:.2f}秒")
    
    # 验证缓存生效
    assert second_time < first_time
    print(f"工具缓存性能提升: {((first_time - second_time) / first_time) * 100:.2f}%")


async def test_overall_performance(boss_agent):
    """测试整体性能"""
    context = AgentContext(
        user_input="生成一篇关于机器学习的文章，要求包含监督学习和无监督学习的区别",
        metadata={}
    )
    
    start_time = time.time()
    result = await boss_agent.execute(context)
    total_time = time.time() - start_time
    
    print(f"整体执行时间: {total_time:.2f}秒")
    print(f"生成文章长度: {len(result)}字符")
    
    # 验证执行时间在合理范围内
    assert total_time < 60  # 60秒内完成


if __name__ == "__main__":
    # 运行性能测试
    asyncio.run(test_async_concurrency_performance(BossAgent()))
    asyncio.run(test_llm_cache_performance(BossAgent()))
    asyncio.run(test_tool_cache_performance())
    asyncio.run(test_overall_performance(BossAgent()))
