"""
Gateway API 路由

提供任务管理、状态查询等接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from eleven_blog_tunner.api.routes.common import (
    CommonResponse, SuccessResponse, ErrorResponse
)
from eleven_blog_tunner.gateway.api_handler import APIHandler
from eleven_blog_tunner.gateway.task_manager import TaskManager

router = APIRouter(prefix="/gateway", tags=["gateway"])

# 创建 APIHandler 实例
api_handler = APIHandler()


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    task_type: str
    input_data: str
    user_id: str


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    progress: int = 0


@router.on_event("startup")
async def startup_event():
    """启动时初始化"""
    await api_handler.start()


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    await api_handler.stop()


@router.post("/tasks", response_model=CommonResponse)
async def create_task(request: CreateTaskRequest):
    """
    创建新任务
    
    任务类型：
    - article_generation: 文章生成
    - style_analysis: 风格分析
    - article_review: 文章审查
    - system_status: 系统状态查询
    """
    try:
        result = await api_handler.create_task(
            task_type=request.task_type,
            input_data=request.input_data,
            user_id=request.user_id
        )
        return SuccessResponse.build(
            data=result,
            message="任务创建成功"
        )
    except HTTPException as e:
        return ErrorResponse(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/tasks/{task_id}", response_model=CommonResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        result = await api_handler.get_task_status(task_id)
        return SuccessResponse.build(
            data=result,
            message="获取任务状态成功"
        )
    except HTTPException as e:
        return ErrorResponse(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/tasks/{task_id}/result", response_model=CommonResponse)
async def get_task_result(task_id: str):
    """获取任务结果"""
    try:
        result = await api_handler.get_task_result(task_id)
        return SuccessResponse.build(
            data=result,
            message="获取任务结果成功"
        )
    except HTTPException as e:
        return ErrorResponse(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.delete("/tasks/{task_id}", response_model=CommonResponse)
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        result = await api_handler.cancel_task(task_id)
        return SuccessResponse.build(
            data=result,
            message="任务取消成功"
        )
    except HTTPException as e:
        return ErrorResponse(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/tasks", response_model=CommonResponse)
async def list_tasks(user_id: Optional[str] = None):
    """列出任务"""
    try:
        result = await api_handler.list_tasks(user_id)
        return SuccessResponse.build(
            data=result,
            message="获取任务列表成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/health", response_model=CommonResponse)
async def health_check():
    """健康检查"""
    try:
        result = await api_handler.health_check()
        if result.get("success"):
            return SuccessResponse.build(
                data=result,
                message="系统健康"
            )
        else:
            return ErrorResponse.internal_error(
                message=result.get("error", "系统不健康")
            )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))
