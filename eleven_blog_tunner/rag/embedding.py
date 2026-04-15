"""
Embedding 服务
"""
from typing import List


class EmbeddingService:
    """Embedding 服务"""
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        # TODO: 初始化实际的 embedding 模型
    
    async def embed(self, text: str) -> List[float]:
        """单文本向量化"""
        # TODO: 实现实际的 embedding 逻辑
        return []
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        # TODO: 实现批量 embedding 逻辑
        return [await self.embed(text) for text in texts]
