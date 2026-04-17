"""
记忆管理模块
"""
from typing import List, Dict, Optional, Any
from collections import deque


class Memory:
    """对话记忆"""
    
    def __init__(self, max_history: int = 10, max_tokens: int = 4096):
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.history: deque = deque(maxlen=max_history)
    
    def add(self, role: str, content: str, **kwargs):
        """添加对话记录"""
        message = {"role": role, "content": content}
        # 添加额外参数，如 tool_calls, tool_call_id, name 等
        message.update(kwargs)
        self.history.append(message)
        # 自动管理上下文长度
        self._manage_context()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取历史记录"""
        return list(self.history)
    
    def clear(self):
        """清空记忆"""
        self.history.clear()
    
    def get_last_n(self, n: int) -> List[Dict[str, Any]]:
        """获取最近 n 条记录"""
        return list(self.history)[-n:]
    
    def add_message(self, message: Dict[str, Any]):
        """添加完整消息对象"""
        self.history.append(message)
        self._manage_context()
    
    def add_messages(self, messages: List[Dict[str, Any]]):
        """添加多条消息"""
        for message in messages:
            self.add_message(message)
    
    def _manage_context(self):
        """管理上下文长度，确保不超过token限制"""
        # 简单的token估算（实际应用中可能需要更精确的计算）
        total_tokens = 0
        temp_history = []
        
        # 从最新的消息开始，计算token数
        for message in reversed(self.history):
            content = message.get("content", "")
            # 粗略估算：每个字符约0.25个token
            message_tokens = len(content) * 0.25
            
            # 如果加上这条消息会超过限制，则停止
            if total_tokens + message_tokens > self.max_tokens:
                break
            
            temp_history.append(message)
            total_tokens += message_tokens
        
        # 重建历史，保留最近的消息
        if temp_history:
            self.history = deque(reversed(temp_history), maxlen=self.max_history)
    
    def get_context(self, max_tokens: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取上下文，可指定最大token数"""
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        total_tokens = 0
        context = []
        
        for message in reversed(self.history):
            content = message.get("content", "")
            message_tokens = len(content) * 0.25
            
            if total_tokens + message_tokens > max_tokens:
                break
            
            context.append(message)
            total_tokens += message_tokens
        
        return list(reversed(context))
    
    def update_last_message(self, content: str, **kwargs):
        """更新最后一条消息"""
        if self.history:
            last_message = self.history.pop()
            last_message["content"] = content
            last_message.update(kwargs)
            self.history.append(last_message)


class LongTermMemory:
    """长期记忆（基于向量数据库）"""
    
    def __init__(self, vector_db_path: str = "./data/vector_db", embedding_model: str = "text-embedding-3-small", 
                 local_embedding_model: str = "dengcao/bge-large-zh-v1.5:latest", use_local_embedding: bool = False):
        """
        初始化长期记忆
        
        Args:
            vector_db_path: 向量数据库存储路径
            embedding_model: 在线嵌入模型名称
            local_embedding_model: 本地嵌入模型名称
            use_local_embedding: 是否使用本地嵌入模型
        """
        self.vector_db_path = vector_db_path
        self.embedding_model = embedding_model
        self.local_embedding_model = local_embedding_model
        self.use_local_embedding = use_local_embedding
        self.client = None
        self.collection = None
        self._init_chromadb()
    
    def _init_chromadb(self):
        """初始化 ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 初始化 ChromaDB 客户端
            self.client = chromadb.PersistentClient(
                path=self.vector_db_path,
                settings=Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.vector_db_path
                )
            )
            
            # 创建或获取集合
            self.collection = self.client.get_or_create_collection(
                name="long_term_memory",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            print("ChromaDB 未安装，请运行: pip install chromadb")
        except Exception as e:
            print(f"初始化 ChromaDB 失败: {e}")
    
    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        if self.use_local_embedding:
            return await self._get_local_embedding(text)
        else:
            return await self._get_online_embedding(text)
    
    async def _get_local_embedding(self, text: str) -> List[float]:
        """使用本地 Ollama 模型获取嵌入向量"""
        try:
            import ollama
            response = ollama.embeddings(
                model=self.local_embedding_model,
                prompt=text
            )
            return response["embedding"]
        except ImportError:
            print("Ollama 未安装，请运行: pip install ollama")
            return []
        except Exception as e:
            print(f"获取本地嵌入失败: {e}")
            return []
    
    async def _get_online_embedding(self, text: str) -> List[float]:
        """使用在线模型获取嵌入向量"""
        try:
            from openai import AsyncOpenAI
            from eleven_blog_tunner.core.config import get_settings
            
            settings = get_settings()
            client = AsyncOpenAI(
                api_key=settings.llm_api_key or settings.api_key,
                base_url=settings.llm_base_url if settings.llm_base_url else None
            )
            
            response = await client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except ImportError:
            print("OpenAI 未安装，请运行: pip install openai")
            return []
        except Exception as e:
            print(f"获取在线嵌入失败: {e}")
            return []
    
    async def store(self, key: str, content: str, metadata: dict = None):
        """存储长期记忆"""
        if not self.collection:
            print("向量数据库未初始化")
            return
        
        try:
            # 获取嵌入向量
            embedding = await self._get_embedding(content)
            if not embedding:
                print("获取嵌入向量失败")
                return
            
            # 存储到向量数据库
            self.collection.add(
                ids=[key],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None
            )
        except Exception as e:
            print(f"存储记忆失败: {e}")
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """检索相关记忆"""
        if not self.collection:
            print("向量数据库未初始化")
            return []
        
        try:
            # 获取查询嵌入向量
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                print("获取查询嵌入向量失败")
                return []
            
            # 检索相关文档
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # 返回检索到的文档
            return results.get("documents", [[]])[0]
        except Exception as e:
            print(f"检索记忆失败: {e}")
            return []
    
    async def delete(self, key: str):
        """删除记忆"""
        if not self.collection:
            print("向量数据库未初始化")
            return
        
        try:
            self.collection.delete(ids=[key])
        except Exception as e:
            print(f"删除记忆失败: {e}")
    
    def get_stats(self):
        """获取向量数据库统计信息"""
        if not self.collection:
            print("向量数据库未初始化")
            return {}
        
        try:
            return {
                "count": self.collection.count(),
                "name": self.collection.name
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, Memory] = {}
    
    def get_session(self, session_id: str, **kwargs) -> Memory:
        """获取或创建会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = Memory(**kwargs)
        return self.sessions[session_id]
    
    def remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        return list(self.sessions.keys())
