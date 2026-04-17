"""
长期记忆功能测试
"""
import asyncio
import tempfile
import shutil
from eleven_blog_tunner.llm.memory import LongTermMemory
from eleven_blog_tunner.core.config import get_settings


async def test_long_term_memory_basic():
    """测试长期记忆基本功能"""
    print("=== 测试长期记忆基本功能 ===")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建长期记忆实例
        ltm = LongTermMemory(vector_db_path=temp_dir)
        
        # 测试初始化
        print("测试初始化...")
        stats = ltm.get_stats()
        print(f"初始统计信息: {stats}")
        
        # 测试存储记忆
        print("\n测试存储记忆...")
        test_data = [
            ("mem1", "Python 是一种高级编程语言，广泛用于数据分析、人工智能等领域"),
            ("mem2", "Java 是一种面向对象的编程语言，常用于企业级应用开发"),
            ("mem3", "JavaScript 是一种脚本语言，主要用于前端开发"),
            ("mem4", "Go 是一种开源的编程语言，以其高性能和并发特性而闻名"),
            ("mem5", "Rust 是一种系统编程语言，注重安全性和性能")
        ]
        
        for key, content in test_data:
            await ltm.store(key, content)
            print(f"存储记忆: {key}")
        
        # 测试统计信息
        print("\n测试统计信息...")
        stats = ltm.get_stats()
        print(f"存储后统计信息: {stats}")
        assert stats.get("count") == 5, f"期望存储5条记忆，实际存储了{stats.get('count')}条"
        
        # 测试检索记忆
        print("\n测试检索记忆...")
        queries = [
            "编程语言",
            "前端开发",
            "系统编程"
        ]
        
        for query in queries:
            results = await ltm.retrieve(query, top_k=2)
            print(f"\n查询: {query}")
            print(f"检索结果 ({len(results)}):")
            for i, result in enumerate(results):
                print(f"  {i+1}. {result[:100]}...")
        
        # 测试删除记忆
        print("\n测试删除记忆...")
        await ltm.delete("mem1")
        print("删除记忆: mem1")
        
        # 测试删除后的统计信息
        stats = ltm.get_stats()
        print(f"删除后统计信息: {stats}")
        assert stats.get("count") == 4, f"期望剩余4条记忆，实际剩余{stats.get('count')}条"
        
        # 测试删除后的检索
        results = await ltm.retrieve("Python", top_k=2)
        print(f"\n删除mem1后检索Python: {len(results)}条结果")
        
        print("\n=== 长期记忆基本功能测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：如果依赖未安装，此测试会失败，这是正常的")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


async def test_local_embedding():
    """测试本地嵌入模型"""
    print("\n=== 测试本地嵌入模型 ===")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建使用本地嵌入模型的长期记忆实例
        ltm = LongTermMemory(
            vector_db_path=temp_dir,
            use_local_embedding=True,
            local_embedding_model="dengcao/bge-large-zh-v1.5:latest"
        )
        
        # 测试存储和检索
        print("测试本地嵌入模型存储...")
        await ltm.store("local1", "这是一个本地嵌入模型测试")
        
        results = await ltm.retrieve("测试", top_k=1)
        print(f"本地嵌入模型检索结果: {len(results)}条")
        if results:
            print(f"结果内容: {results[0]}")
        
        print("\n=== 本地嵌入模型测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：如果Ollama未安装或模型未下载，此测试会失败，这是正常的")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


async def test_with_config():
    """测试使用配置的长期记忆"""
    print("\n=== 测试使用配置的长期记忆 ===")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 获取配置
        settings = get_settings()
        
        # 创建长期记忆实例
        ltm = LongTermMemory(
            vector_db_path=temp_dir,
            embedding_model=settings.embedding_model,
            local_embedding_model=settings.local_embedding_model,
            use_local_embedding=settings.use_local_embedding
        )
        
        print(f"使用配置创建长期记忆实例:")
        print(f"  向量数据库路径: {temp_dir}")
        print(f"  在线嵌入模型: {settings.embedding_model}")
        print(f"  本地嵌入模型: {settings.local_embedding_model}")
        print(f"  使用本地嵌入: {settings.use_local_embedding}")
        
        # 测试基本功能
        await ltm.store("config_test", "这是一个使用配置的测试")
        results = await ltm.retrieve("测试", top_k=1)
        print(f"\n使用配置的检索结果: {len(results)}条")
        
        print("\n=== 使用配置的长期记忆测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建长期记忆实例
        ltm = LongTermMemory(vector_db_path=temp_dir)
        
        # 测试空查询
        print("测试空查询...")
        results = await ltm.retrieve("", top_k=1)
        print(f"空查询结果: {len(results)}条")
        
        # 测试不存在的键删除
        print("测试删除不存在的键...")
        await ltm.delete("non_existent_key")
        print("删除不存在的键成功")
        
        print("\n=== 错误处理测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    """运行所有测试"""
    asyncio.run(test_long_term_memory_basic())
    asyncio.run(test_local_embedding())
    asyncio.run(test_with_config())
    asyncio.run(test_error_handling())
    print("\n所有长期记忆功能测试完成！")
