"""
LLM 工厂
"""
from eleven_blog_tunner.llm.base import BaseLLM
from eleven_blog_tunner.llm.openai_provider import OpenAIProvider
from eleven_blog_tunner.llm.local_provider import LocalProvider
from eleven_blog_tunner.core.config import get_settings

class LLMFactory:
    """LLM 工厂"""
    
    _providers = {
        "openai": OpenAIProvider,
        "local": LocalProvider,
        # TODO: 添加更多提供商
        # "claude": ClaudeProvider,
    }
    
    @classmethod
    def create(cls, provider: str = None, **kwargs) -> BaseLLM:
        """创建 LLM 实例"""
        settings = get_settings()
        provider = provider or settings.llm_provider
        
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        provider_class = cls._providers[provider]
        
        # 记忆系统配置
        use_memory = kwargs.get("use_memory", True)
        max_history = kwargs.get("max_history", 10)
        
        # 根据提供商传入相应配置
        if provider == "openai":
            # 优先使用 llm_api_key，如果没有则使用 api_key
            api_key = settings.llm_api_key if settings.llm_api_key else settings.api_key
            return provider_class(
                api_key=api_key,
                model=kwargs.get("model", settings.llm_model),
                temperature=kwargs.get("temperature", settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
                base_url=settings.llm_base_url if settings.llm_base_url else None,
                use_memory=use_memory,
                max_history=max_history,
            )
        elif provider == "local":
            return provider_class(
                model=kwargs.get("model", settings.local_llm_model),
                base_url=kwargs.get("base_url", settings.local_llm_base_url),
                temperature=kwargs.get("temperature", settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
                use_memory=use_memory,
                max_history=max_history,
            )
        
        # 其他提供商
        return provider_class(
            use_memory=use_memory,
            max_history=max_history,
            **kwargs
        )

if __name__ == "__main__":
    """测试不同的模型提供商"""
    import asyncio
    import sys
    
    async def test_provider(provider, model=None):
        """测试指定的模型提供商"""
        print(f"\n=== Testing {provider} provider ===")
        
        try:
            # 创建 LLM 实例
            llm = LLMFactory.create(provider=provider, model=model)
            print(f"Created {provider} provider instance")
            
            # 测试普通对话
            print("\n1. Testing normal chat:")
            messages = [
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "你好，你是谁？"}
            ]
            
            response = await llm.chat(messages)
            print(f"Response: {response}")
            
            # 测试流式对话
            print("\n2. Testing stream chat:")
            messages = [
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "请简要介绍一下自己"}
            ]
            
            print("Stream response:")
            async for chunk in llm.stream_chat(messages):
                print(chunk, end="")
            print()
            
        except Exception as e:
            print(f"Error: {e}")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        provider = sys.argv[1]
        model = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(test_provider(provider, model))
    else:
        # 测试所有可用的提供商
        print("Testing all available providers...")
        for provider in LLMFactory._providers.keys():
            asyncio.run(test_provider(provider))
