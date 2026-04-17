"""
集成模块

负责：
- 与 BossAgent 深度绑定
- 与 SystemAgent 深度绑定
- Agent 间的协调和通信
- 系统配置和状态管理
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from eleven_blog_tunner.agents import get_protocol
from eleven_blog_tunner.agents.base_agent import AgentContext
from eleven_blog_tunner.core.config import get_settings

logger = logging.getLogger(__name__)


class Integration:
    """集成模块"""
    
    def __init__(self):
        self.protocol = get_protocol()
        self.settings = get_settings()
        self.boss_agent = None
        self.system_agent = None
        self._init_agents()
    
    def _init_agents(self):
        """初始化 Agent"""
        try:
            # 获取 BossAgent
            self.boss_agent = self.protocol.get_agent("BossAgent")
            if not self.boss_agent:
                logger.warning("BossAgent 未找到，将在运行时动态获取")
            
            # 获取 SystemAgent
            self.system_agent = self.protocol.get_agent("SystemAgent")
            if not self.system_agent:
                logger.warning("SystemAgent 未找到，将在运行时动态获取")
            
        except Exception as e:
            logger.error(f"初始化 Agent 失败: {e}")
    
    async def call_boss_agent(
        self,
        task: str,
        input_data: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        调用 BossAgent
        
        Args:
            task: 任务类型
            input_data: 输入数据
            task_id: 任务ID
            
        Returns:
            调用结果
        """
        try:
            # 确保 BossAgent 存在
            if not self.boss_agent:
                self.boss_agent = self.protocol.get_agent("BossAgent")
                if not self.boss_agent:
                    return {
                        "success": False,
                        "error": "BossAgent 不可用"
                    }
            
            # 创建上下文
            context = AgentContext(
                task_id=task_id,
                user_input=input_data,
                metadata={"task_type": task}
            )
            
            # 调用 BossAgent
            result = await self.boss_agent.execute(context)
            
            return {
                "success": True,
                "result": result,
                "agent": "BossAgent"
            }
            
        except Exception as e:
            logger.error(f"调用 BossAgent 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "BossAgent"
            }
    
    async def call_system_agent(
        self,
        query: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        调用 SystemAgent
        
        Args:
            query: 查询内容
            task_id: 任务ID
            
        Returns:
            调用结果
        """
        try:
            # 确保 SystemAgent 存在
            if not self.system_agent:
                self.system_agent = self.protocol.get_agent("SystemAgent")
                if not self.system_agent:
                    return {
                        "success": False,
                        "error": "SystemAgent 不可用"
                    }
            
            # 创建上下文
            context = AgentContext(
                task_id=task_id,
                user_input=query,
                metadata={"query_type": "system"}
            )
            
            # 调用 SystemAgent
            result = await self.system_agent.execute(context)
            
            return {
                "success": True,
                "result": result,
                "agent": "SystemAgent"
            }
            
        except Exception as e:
            logger.error(f"调用 SystemAgent 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "SystemAgent"
            }
    
    async def get_system_config(self) -> Dict[str, Any]:
        """
        获取系统配置
        
        Returns:
            系统配置
        """
        try:
            # 先尝试从 SystemAgent 获取
            system_result = await self.call_system_agent(
                "获取系统配置",
                f"system_config_{datetime.now().timestamp()}"
            )
            
            if system_result.get("success"):
                return system_result.get("result", {})
            
            # 如果 SystemAgent 不可用，从配置文件获取
            config = {
                "llm": {
                    "provider": self.settings.llm_provider,
                    "model": self.settings.llm_model,
                    "temperature": self.settings.llm_temperature,
                    "max_tokens": self.settings.llm_max_tokens
                },
                "rag": {
                    "vector_db_path": self.settings.vector_db_path,
                    "embedding_model": self.settings.embedding_model,
                    "chunk_size": self.settings.chunk_size,
                    "chunk_overlap": self.settings.chunk_overlap
                },
                "api": {
                    "base_url": self.settings.api_base_url
                }
            }
            
            return config
            
        except Exception as e:
            logger.error(f"获取系统配置失败: {e}")
            return {}
    
    async def get_style_config(self) -> Dict[str, Any]:
        """
        获取风格配置
        
        Returns:
            风格配置
        """
        try:
            # 从 SystemAgent 获取风格配置
            system_result = await self.call_system_agent(
                "获取风格配置",
                f"style_config_{datetime.now().timestamp()}"
            )
            
            if system_result.get("success"):
                return system_result.get("result", {})
            
            # 默认风格配置
            return {
                "writing_style": "简洁专业",
                "tone": "中性",
                "paragraph_length": "中等",
                "use_analogies": True,
                "code_examples": False,
                "summary_style": "要点式"
            }
            
        except Exception as e:
            logger.error(f"获取风格配置失败: {e}")
            return {}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态
        """
        try:
            # 从 SystemAgent 获取系统状态
            system_result = await self.call_system_agent(
                "获取系统状态",
                f"system_status_{datetime.now().timestamp()}"
            )
            
            if system_result.get("success"):
                return system_result.get("result", {})
            
            # 构建基本系统状态
            status = {
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    "BossAgent": "available" if self.boss_agent else "unavailable",
                    "SystemAgent": "available" if self.system_agent else "unavailable"
                },
                "config": await self.get_system_config()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {}
    
    async def execute_task_chain(
        self,
        task_type: str,
        input_data: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        执行任务链
        
        Args:
            task_type: 任务类型
            input_data: 输入数据
            task_id: 任务ID
            
        Returns:
            执行结果
        """
        try:
            logger.info(f"开始执行任务链: {task_type}, 任务ID: {task_id}")
            
            # 1. 获取系统配置
            system_config = await self.get_system_config()
            logger.debug(f"系统配置: {system_config}")
            
            # 2. 获取风格配置（如果需要）
            style_config = {}
            if task_type in ["article_generation", "style_analysis"]:
                style_config = await self.get_style_config()
                logger.debug(f"风格配置: {style_config}")
            
            # 3. 调用 BossAgent 执行任务
            boss_result = await self.call_boss_agent(
                task_type,
                input_data,
                task_id
            )
            
            if not boss_result.get("success"):
                logger.error(f"BossAgent 执行失败: {boss_result.get('error')}")
                return {
                    "success": False,
                    "error": boss_result.get("error", "任务执行失败")
                }
            
            # 4. 构建完整结果
            result = {
                "success": True,
                "result": boss_result.get("result"),
                "metadata": {
                    "task_type": task_type,
                    "system_config": system_config,
                    "style_config": style_config,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"任务链执行完成: {task_id}")
            return result
            
        except Exception as e:
            logger.error(f"执行任务链失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态
        """
        try:
            # 检查 Agent 可用性
            boss_available = self.boss_agent is not None
            system_available = self.system_agent is not None
            
            # 检查配置
            config_available = self.settings is not None
            
            # 检查协议
            protocol_available = self.protocol is not None
            
            # 综合健康状态
            overall_health = "healthy" if all([
                boss_available,
                system_available,
                config_available,
                protocol_available
            ]) else "unhealthy"
            
            return {
                "status": overall_health,
                "components": {
                    "BossAgent": "available" if boss_available else "unavailable",
                    "SystemAgent": "available" if system_available else "unavailable",
                    "config": "available" if config_available else "unavailable",
                    "protocol": "available" if protocol_available else "unavailable"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
