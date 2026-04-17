"""
Agent 相关 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from eleven_blog_tunner.agents.boss_agent import BossAgent
from eleven_blog_tunner.agents.base_agent import AgentContext
import uuid
import asyncio

router = APIRouter(prefix="/agent", tags=["agent"])

# 任务存储
tasks = {}


class TaskRequest(BaseModel):
    """任务请求模型"""
    user_input: str
    metadata: Optional[dict] = {}


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str


@router.post("/tasks", response_model=TaskStatus)
async def create_task(request: TaskRequest):
    """创建任务"""
    task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    tasks[task_id] = {
        "status": "pending",
        "result": None,
        "error": None
    }
    
    # 异步执行任务
    async def execute_task():
        try:
            tasks[task_id]["status"] = "running"
            
            # 创建 Boss Agent
            boss_agent = BossAgent(llm_provider="openai", use_memory=True)
            
            # 创建上下文
            context = AgentContext(
                task_id=task_id,
                user_input=request.user_input,
                metadata=request.metadata
            )
            
            # 执行任务
            result = await boss_agent.execute(context)
            
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = result
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
    
    # 启动异步任务
    asyncio.create_task(execute_task())
    
    return TaskStatus(task_id=task_id, status="pending")


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskStatus(task_id=task_id, status=task["status"])


@router.get("/tasks/{task_id}/result", response_model=TaskResponse)
async def get_task_result(task_id: str):
    """获取任务结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"],
        error=task["error"]
    )


@router.delete("/tasks/{task_id}", response_model=TaskStatus)
async def cancel_task(task_id: str):
    """取消任务"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 这里简化处理，实际应该终止正在执行的任务
    tasks[task_id]["status"] = "cancelled"
    
    return TaskStatus(task_id=task_id, status="cancelled")


@router.get("/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """列出所有任务"""
    return [
        TaskStatus(task_id=task_id, status=task["status"])
        for task_id, task in tasks.items()
    ]


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
