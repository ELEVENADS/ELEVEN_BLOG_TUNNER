"""
Embedding 服务
"""
from typing import List
import httpx
from eleven_blog_tunner.core.config import get_settings


class EmbeddingService:
    """Embedding 服务"""

    def __init__(self, model_name: str = "text-embedding-3-small", use_local: bool = None):
        self.settings = get_settings()
        self.model_name = model_name

        if use_local is None:
            self.use_local = self.settings.use_local_embedding
        else:
            self.use_local = use_local

        if self.use_local:
            self.model_name = self.settings.local_embedding_model
            self.base_url = self.settings.local_llm_base_url
        else:
            self.api_key = self.settings.api_key
    
    async def embed(self, text: str) -> List[float]:
        """单文本向量化"""
        if self.use_local:
            return await self._embed_local(text)
        else:
            return await self._embed_openai(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        if self.use_local:
            # 本地模型批量处理
            embeddings = []
            for text in texts:
                embedding = await self._embed_local(text)
                embeddings.append(embedding)
            return embeddings
        else:
            # OpenAI 批量处理
            return await self._embed_openai_batch(texts)
    
    async def _embed_openai(self, text: str) -> List[float]:
        """使用 OpenAI 进行向量化"""
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "input": text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
    
    async def _embed_openai_batch(self, texts: List[str]) -> List[List[float]]:
        """使用 OpenAI 批量向量化"""
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "input": texts
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return [item["embedding"] for item in response.json()["data"]]
    
    async def _embed_local(self, text: str) -> List[float]:
        """使用本地 Ollama 进行向量化"""
        url = f"{self.base_url}/embeddings"
        data = {
            "model": self.model_name,
            "prompt": text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()["embedding"]
