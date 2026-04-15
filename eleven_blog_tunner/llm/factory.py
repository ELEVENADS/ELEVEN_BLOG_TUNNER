"""
LLM 工厂
"""
from eleven_blog_tunner.llm.base import BaseLLM
from eleven_blog_tunner.llm.openai_provider import OpenAIProvider
from eleven_blog_tunner.core.config import get_settings


class LLMFactory:
    """LLM 工厂"""
    
    _providers = {
        "openai": OpenAIProvider,
        # TODO: 添加更多提供商
        # "claude": ClaudeProvider,
        # "local": LocalProvider,
    }
    
    @classmethod
    def create(cls, provider: str = None, **kwargs) -> BaseLLM:
        """创建 LLM 实例"""
        settings = get_settings()
        provider = provider or settings.llm_provider
        
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        provider_class = cls._providers[provider]
        
        # 根据提供商传入相应配置
        if provider == "openai":
            return provider_class(
                api_key=settings.api_key,
                model=kwargs.get("model", settings.llm_model),
                temperature=kwargs.get("temperature", settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
            )
        
        return provider_class(**kwargs)
