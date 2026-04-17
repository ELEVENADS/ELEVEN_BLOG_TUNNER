"""
短期记忆功能测试
"""
import asyncio
from eleven_blog_tunner.llm.factory import LLMFactory
from eleven_blog_tunner.llm.memory import Memory, SessionManager


async def test_memory_basic():
    """测试Memory类的基本功能"""
    print("=== 测试Memory类基本功能 ===")
    
    # 创建Memory实例
    memory = Memory(max_history=5, max_tokens=1000)
    
    # 添加对话记录
    memory.add("user", "你好，你是谁？")
    memory.add("assistant", "我是一个助手，有什么可以帮助你的吗？")
    memory.add("user", "我想了解一下人工智能")
    
    # 获取历史记录
    history = memory.get_history()
    print(f"历史记录长度: {len(history)}")
    for i, msg in enumerate(history):
        print(f"{i+1}. {msg['role']}: {msg['content']}")
    
    # 测试上下文管理
    context = memory.get_context(max_tokens=500)
    print(f"\n上下文长度: {len(context)}")
    
    # 测试清空记忆
    memory.clear()
    print(f"\n清空后历史记录长度: {len(memory.get_history())}")
    
    print("=== Memory类基本功能测试完成 ===\n")


async def test_session_manager():
    """测试SessionManager"""
    print("=== 测试SessionManager ===")
    
    # 创建会话管理器
    manager = SessionManager()
    
    # 创建两个会话
    session1 = manager.get_session("session1")
    session2 = manager.get_session("session2")
    
    # 向会话1添加消息
    session1.add("user", "会话1: 你好")
    session1.add("assistant", "会话1: 你好！")
    
    # 向会话2添加消息
    session2.add("user", "会话2: 你好")
    session2.add("assistant", "会话2: 你好！")
    
    # 查看会话列表
    sessions = manager.list_sessions()
    print(f"会话列表: {sessions}")
    
    # 查看每个会话的历史
    print("\n会话1历史:")
    for msg in session1.get_history():
        print(f"{msg['role']}: {msg['content']}")
    
    print("\n会话2历史:")
    for msg in session2.get_history():
        print(f"{msg['role']}: {msg['content']}")
    
    # 移除会话
    manager.remove_session("session1")
    print(f"\n移除会话1后，会话列表: {manager.list_sessions()}")
    
    print("=== SessionManager测试完成 ===\n")


async def test_llm_memory_integration():
    """测试LLM与记忆系统的集成"""
    print("=== 测试LLM与记忆系统集成 ===")
    
    try:
        # 创建LLM实例（使用本地Ollama模型）
        llm = LLMFactory.create(
            provider="local",
            model="llama3",
            use_memory=True,
            max_history=5
        )
        
        print("创建LLM实例成功")
        
        # 测试对话历史管理
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好，你是谁？"}
        ]
        
        response1 = await llm.chat(messages)
        print(f"第一次响应: {response1}")
        
        # 第二次对话，应该能够记住之前的对话
        messages2 = [
            {"role": "user", "content": "我刚才问了你什么？"}
        ]
        
        response2 = await llm.chat(messages2)
        print(f"第二次响应: {response2}")
        
        # 查看对话历史
        history = llm.get_history()
        print("\n对话历史:")
        for i, msg in enumerate(history):
            print(f"{i+1}. {msg['role']}: {msg['content']}")
        
        # 测试清空记忆
        llm.clear_memory()
        print(f"\n清空记忆后，历史记录长度: {len(llm.get_history())}")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：如果Ollama服务未运行，此测试会失败，这是正常的")
    
    print("=== LLM与记忆系统集成测试完成 ===\n")


async def test_memory_usage_example():
    """短期记忆功能使用示例"""
    print("=== 短期记忆功能使用示例 ===")
    
    # 示例1: 基本使用
    print("示例1: 基本使用")
    memory = Memory(max_history=3)
    memory.add("user", "你好")
    memory.add("assistant", "你好！")
    memory.add("user", "今天天气怎么样？")
    print(f"历史记录: {memory.get_history()}")
    
    # 示例2: 会话管理
    print("\n示例2: 会话管理")
    manager = SessionManager()
    session = manager.get_session("user123")
    session.add("user", "我想订一张明天的机票")
    session.add("assistant", "好的，请问您要去哪里？")
    print(f"会话历史: {session.get_history()}")
    
    # 示例3: 与LLM集成
    print("\n示例3: 与LLM集成")
    print("使用方法:")
    print("""
    # 创建带记忆功能的LLM实例
    llm = LLMFactory.create(
        provider="openai",
        model="gpt-4",
        use_memory=True,
        max_history=10
    )
    
    # 第一次对话
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好，我叫张三"}
    ]
    response = await llm.chat(messages)
    
    # 第二次对话，模型会记住你的名字
    messages2 = [
        {"role": "user", "content": "你知道我叫什么名字吗？"}
    ]
    response2 = await llm.chat(messages2)
    """)
    
    print("=== 短期记忆功能使用示例完成 ===")


if __name__ == "__main__":
    """运行所有测试"""
    asyncio.run(test_memory_basic())
    asyncio.run(test_session_manager())
    asyncio.run(test_llm_memory_integration())
    asyncio.run(test_memory_usage_example())
    print("\n所有测试完成！")
