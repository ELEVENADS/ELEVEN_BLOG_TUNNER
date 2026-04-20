"""连接池管理模块

提供连接池功能，优化资源使用
"""
import asyncio
from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class ConnectionPool:
    """连接池类
    
    管理连接对象，支持异步操作
    """
    
    def __init__(self, max_connections: int = 10, timeout: int = 30):
        """初始化连接池
        
        Args:
            max_connections: 最大连接数
            timeout: 连接超时时间（秒）
        """
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool: List[Any] = []
        self.in_use = set()
        self.semaphore = asyncio.Semaphore(max_connections)
        self.lock = asyncio.Lock()
    
    async def get(self) -> Any:
        """获取连接
        
        Returns:
            连接对象
        """
        async with self.semaphore:
            async with self.lock:
                # 从池中获取可用连接
                while self.pool:
                    conn = self.pool.pop()
                    if self._is_valid(conn):
                        self.in_use.add(conn)
                        return conn
                
                # 创建新连接
                conn = await self._create_connection()
                self.in_use.add(conn)
                return conn
    
    async def put(self, conn: Any) -> None:
        """归还连接
        
        Args:
            conn: 连接对象
        """
        async with self.lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
                if self._is_valid(conn) and len(self.pool) < self.max_connections:
                    self.pool.append(conn)
                else:
                    await self._close_connection(conn)
    
    async def close(self) -> None:
        """关闭所有连接"""
        async with self.lock:
            # 关闭池中连接
            for conn in self.pool:
                await self._close_connection(conn)
            self.pool.clear()
            
            # 关闭使用中的连接
            for conn in list(self.in_use):
                await self._close_connection(conn)
            self.in_use.clear()
    
    async def _create_connection(self) -> Any:
        """创建新连接
        
        Returns:
            连接对象
        """
        # 子类实现
        raise NotImplementedError
    
    async def _close_connection(self, conn: Any) -> None:
        """关闭连接
        
        Args:
            conn: 连接对象
        """
        # 子类实现
        raise NotImplementedError
    
    def _is_valid(self, conn: Any) -> bool:
        """检查连接是否有效
        
        Args:
            conn: 连接对象
            
        Returns:
            是否有效
        """
        # 子类实现
        return True


class ThreadPoolManager:
    """线程池管理器
    
    用于执行同步任务的线程池
    """
    
    def __init__(self, max_workers: int = 5):
        """初始化线程池
        
        Args:
            max_workers: 最大工作线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_in_thread(self, func, *args, **kwargs):
        """在线程池中执行同步函数

        Args:
            func: 同步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        loop = asyncio.get_event_loop()
        # 使用 partial 将关键字参数绑定到函数上
        # run_in_executor 只接受位置参数
        if kwargs:
            func_with_kwargs = partial(func, **kwargs)
            return await loop.run_in_executor(self.executor, func_with_kwargs, *args)
        return await loop.run_in_executor(self.executor, func, *args)
    
    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)


# 全局线程池管理器
thread_pool = ThreadPoolManager(max_workers=10)
