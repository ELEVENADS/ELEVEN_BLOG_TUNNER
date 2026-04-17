"""
任务管理器

负责：
- 24小时运行
- 自动处理任务链
- 任务状态管理
- 任务调度和执行
"""
from typing import Dict, Any, Optional, List
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from collections import deque
import logging

from eleven_blog_tunner.agents import get_protocol
from eleven_blog_tunner.agents.base_agent import AgentContext

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """任务类"""
    
    def __init__(self, task_id: str, task_type: str, input_data: str, user_id: str):
        self.task_id = task_id
        self.task_type = task_type
        self.input_data = input_data
        self.user_id = user_id
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result = None
        self.error = None
        self.progress = 0
        self.steps = []
    
    def update_status(self, status: TaskStatus):
        """更新任务状态"""
        self.status = status
        self.updated_at = datetime.now()
    
    def set_result(self, result: Any):
        """设置任务结果"""
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.updated_at = datetime.now()
    
    def set_error(self, error: str):
        """设置任务错误"""
        self.error = error
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now()
    
    def update_progress(self, progress: int):
        """更新任务进度"""
        self.progress = min(max(progress, 0), 100)
        self.updated_at = datetime.now()
    
    def add_step(self, step: str):
        """添加任务步骤"""
        self.steps.append({
            "step": step,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "input_data": self.input_data,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "steps": self.steps
        }


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue = deque()
        self.running = False
        self.worker_task = None
        self.protocol = get_protocol()
    
    async def start(self):
        """启动任务管理器"""
        if not self.running:
            self.running = True
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("任务管理器已启动")
    
    async def stop(self):
        """停止任务管理器"""
        if self.running:
            self.running = False
            if self.worker_task:
                await self.worker_task
            logger.info("任务管理器已停止")
    
    async def create_task(
        self,
        task_type: str,
        input_data: str,
        user_id: str
    ) -> str:
        """
        创建任务
        
        Args:
            task_type: 任务类型
            input_data: 输入数据
            user_id: 用户ID
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, task_type, input_data, user_id)
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        # 如果任务管理器未启动，自动启动
        if not self.running:
            await self.start()
        
        logger.info(f"创建任务: {task_id}, 类型: {task_type}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态
        """
        if task_id not in self.tasks:
            return {
                "success": False,
                "error": f"任务 {task_id} 不存在",
                "status": "not_found"
            }
        
        task = self.tasks[task_id]
        return {
            "success": True,
            "status": task.status.value,
            "progress": task.progress,
            "updated_at": task.updated_at.isoformat(),
            "steps": task.steps
        }
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        if task.status != TaskStatus.COMPLETED:
            return None
        
        return task.result
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.update_status(TaskStatus.CANCELLED)
        logger.info(f"任务已取消: {task_id}")
        return True
    
    async def list_tasks(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            user_id: 用户ID，不指定则列出所有任务
            
        Returns:
            任务列表
        """
        tasks = []
        for task in self.tasks.values():
            if user_id is None or task.user_id == user_id:
                tasks.append(task.to_dict())
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return tasks
    
    async def _worker(self):
        """工作线程"""
        while self.running:
            if self.task_queue:
                task_id = self.task_queue.popleft()
                await self._process_task(task_id)
            else:
                await asyncio.sleep(1)
    
    async def _process_task(self, task_id: str):
        """处理任务"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        # 检查任务状态
        if task.status != TaskStatus.PENDING:
            return
        
        try:
            task.update_status(TaskStatus.RUNNING)
            task.update_progress(10)
            task.add_step("开始处理任务")
            
            # 根据任务类型处理
            if task.task_type == "article_generation":
                await self._process_article_generation(task)
            elif task.task_type == "style_analysis":
                await self._process_style_analysis(task)
            elif task.task_type == "article_review":
                await self._process_article_review(task)
            elif task.task_type == "system_status":
                await self._process_system_status(task)
            else:
                await self._process_general_task(task)
                
        except Exception as e:
            task.set_error(str(e))
            logger.error(f"任务处理失败: {task_id}, 错误: {e}")
    
    async def _process_article_generation(self, task: Task):
        """处理文章生成任务"""
        task.add_step("开始文章生成")
        task.update_progress(30)
        
        # 调用 Agent 系统
        context = AgentContext(
            task_id=task.task_id,
            user_input=task.input_data
        )
        
        # 执行完整的文章生成流程
        result = await self.protocol.execute_task(
            task="文章生成",
            initial_input=task.input_data,
            agent_sequence=[
                "BossAgent",
                "SystemAgent",
                "SummaryAgent",
                "WriterAgent",
                "ReviewAgent"
            ]
        )
        
        task.update_progress(80)
        task.add_step("文章生成完成")
        task.set_result(result)
    
    async def _process_style_analysis(self, task: Task):
        """处理风格分析任务"""
        task.add_step("开始风格分析")
        task.update_progress(30)
        
        # 调用 SystemAgent 进行风格分析
        context = AgentContext(
            task_id=task.task_id,
            user_input=task.input_data
        )
        
        result = await self.protocol.call_agent(
            caller="Gateway",
            callee="SystemAgent",
            input_data=task.input_data
        )
        
        task.update_progress(80)
        task.add_step("风格分析完成")
        task.set_result(result.get("result", "分析失败"))
    
    async def _process_article_review(self, task: Task):
        """处理文章审查任务"""
        task.add_step("开始文章审查")
        task.update_progress(30)
        
        # 调用 ReviewAgent 进行文章审查
        context = AgentContext(
            task_id=task.task_id,
            user_input=task.input_data
        )
        
        result = await self.protocol.call_agent(
            caller="Gateway",
            callee="ReviewAgent",
            input_data=task.input_data
        )
        
        task.update_progress(80)
        task.add_step("文章审查完成")
        task.set_result(result.get("result", "审查失败"))
    
    async def _process_system_status(self, task: Task):
        """处理系统状态查询任务"""
        task.add_step("开始系统状态查询")
        task.update_progress(30)
        
        # 调用 SystemAgent 查询系统状态
        context = AgentContext(
            task_id=task.task_id,
            user_input=task.input_data
        )
        
        result = await self.protocol.call_agent(
            caller="Gateway",
            callee="SystemAgent",
            input_data=task.input_data
        )
        
        task.update_progress(80)
        task.add_step("系统状态查询完成")
        task.set_result(result.get("result", "查询失败"))
    
    async def _process_general_task(self, task: Task):
        """处理一般任务"""
        task.add_step("开始处理一般任务")
        task.update_progress(30)
        
        # 调用 BossAgent 处理一般任务
        context = AgentContext(
            task_id=task.task_id,
            user_input=task.input_data
        )
        
        result = await self.protocol.call_agent(
            caller="Gateway",
            callee="BossAgent",
            input_data=task.input_data
        )
        
        task.update_progress(80)
        task.add_step("任务处理完成")
        task.set_result(result.get("result", "处理失败"))
