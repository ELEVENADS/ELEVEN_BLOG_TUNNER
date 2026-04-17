"""
Agent 全流程演示脚本

展示从用户输入到文章生成的完整流程
"""
import asyncio
from eleven_blog_tunner.agents.boss_agent import BossAgent
from eleven_blog_tunner.agents.base_agent import AgentContext


async def agent_full_flow_demo():
    """Agent 全流程演示"""
    print("=== ELEVEN Blog Tuner Agent 全流程演示 ===")
    print("=" * 60)
    
    # 创建 Boss Agent
    boss_agent = BossAgent(llm_provider="openai", use_memory=True)
    
    # 用户输入
    user_input = "生成一篇关于人工智能在医疗领域应用的文章，要求内容专业、结构清晰"
    print(f"用户输入: {user_input}")
    print("-" * 60)
    
    # 创建上下文
    context = AgentContext(
        user_input=user_input,
        metadata={}
    )
    
    print("1. Boss Agent 开始处理任务...")
    print("2. 分析任务类型...")
    print("3. 并行调用 System Agent 和 Summary Agent...")
    print("4. 调用 Writer Agent 撰写文章...")
    print("5. 调用 Review Agent 审查文章...")
    print("-" * 60)
    
    # 执行流程
    try:
        result = await boss_agent.execute(context)
        print("=== 生成结果 ===")
        print(result)
        print("=" * 60)
        print("演示完成！")
    except Exception as e:
        print(f"演示过程中出现错误: {str(e)}")


async def agent_types_demo():
    """展示不同类型的Agent功能"""
    print("\n=== 不同类型 Agent 功能演示 ===")
    print("=" * 60)
    
    boss_agent = BossAgent(llm_provider="openai", use_memory=True)
    
    # 测试风格查询
    style_context = AgentContext(
        user_input="查询当前的写作风格配置",
        metadata={}
    )
    
    print("测试 System Agent - 风格查询:")
    style_result = await boss_agent.execute(style_context)
    print(f"结果: {style_result}")
    print("-" * 60)
    
    # 测试文章审查
    review_context = AgentContext(
        user_input="审查以下文章：人工智能正在改变我们的生活，它可以帮助我们完成各种任务，提高工作效率。",
        metadata={}
    )
    
    print("测试 Review Agent - 文章审查:")
    review_result = await boss_agent.execute(review_context)
    print(f"结果: {review_result}")
    print("-" * 60)


if __name__ == "__main__":
    # 运行全流程演示
    asyncio.run(agent_full_flow_demo())
    
    # 运行不同类型Agent演示
    asyncio.run(agent_types_demo())
