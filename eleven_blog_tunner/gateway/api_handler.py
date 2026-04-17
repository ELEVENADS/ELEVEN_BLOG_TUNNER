"""
API 处理器

负责：
- 接收和处理 API 请求
- 与 Agent 层交互
- 统一的 API 响应格式
- 请求验证和错误处理
"""
from typing import Dict, Any, Optional
import logging
from fastapi import HTTPException, status

from eleven_blog_tunner.gateway.task_manager import TaskManager
from eleven_blog_tunner.agents import get_protocol

logger = logging.getLogger(__name__)


class APIHandler:
    """API 处理器"""
    
    def __init__(self):
        self.task_manager = TaskManager()
        self.protocol = get_protocol()
    
    async def start(self):
        """启动 API 处理器"""
        await self.task_manager.start()
        logger.info("API 处理器已启动")
    
    async def stop(self):
        """停止 API 处理器"""
        await self.task_manager.stop()
        logger.info("API 处理器已停止")
    
    async def create_task(
        self,
        task_type: str,
        input_data: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            input_data: 输入数据
            user_id: 用户ID
            
        Returns:
            任务创建结果
        """
        try:
            # 验证参数
            if not task_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务类型不能为空"
                )
            
            if not input_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="输入数据不能为空"
                )
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户ID不能为空"
                )
            
            # 验证任务类型
            valid_task_types = [
                "article_generation",
                "style_analysis",
                "article_review",
                "system_status"
            ]
            
            if task_type not in valid_task_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的任务类型，支持的类型: {valid_task_types}"
                )
            
            # 创建任务
            task_id = await self.task_manager.create_task(
                task_type=task_type,
                input_data=input_data,
                user_id=user_id
            )
            
            logger.info(f"API 创建任务: {task_id}, 类型: {task_type}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "任务创建成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建任务失败: {str(e)}"
            )
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态
        """
        try:
            if not task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务ID不能为空"
                )
            
            status_info = await self.task_manager.get_task_status(task_id)
            
            if not status_info.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=status_info.get("error", "任务不存在")
                )
            
            return {
                "success": True,
                "data": status_info
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取任务状态失败: {str(e)}"
            )
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        try:
            if not task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务ID不能为空"
                )
            
            # 先检查任务状态
            status_info = await self.task_manager.get_task_status(task_id)
            
            if not status_info.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=status_info.get("error", "任务不存在")
                )
            
            if status_info.get("status") != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"任务尚未完成，当前状态: {status_info.get('status')}"
                )
            
            # 获取任务结果
            result = await self.task_manager.get_task_result(task_id)
            
            return {
                "success": True,
                "data": result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取任务结果失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取任务结果失败: {str(e)}"
            )
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消结果
        """
        try:
            if not task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务ID不能为空"
                )
            
            success = await self.task_manager.cancel_task(task_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务取消失败，可能任务不存在或已完成"
                )
            
            return {
                "success": True,
                "message": "任务取消成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"取消任务失败: {str(e)}"
            )
    
    async def list_tasks(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        列出任务
        
        Args:
            user_id: 用户ID，不指定则列出所有任务
            
        Returns:
            任务列表
        """
        try:
            tasks = await self.task_manager.list_tasks(user_id)
            
            return {
                "success": True,
                "data": tasks,
                "total": len(tasks)
            }
            
        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"列出任务失败: {str(e)}"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态
        """
        try:
            # 检查任务管理器状态
            is_running = hasattr(self.task_manager, 'running') and self.task_manager.running
            
            # 检查协议状态
            protocol_available = self.protocol is not None
            
            return {
                "success": True,
                "status": "healthy",
                "components": {
                    "task_manager": "running" if is_running else "stopped",
                    "agent_protocol": "available" if protocol_available else "unavailable"
                }
            }
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e)
            }
