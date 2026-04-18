"""
Gateway 相关 API

统一通过 Gateway 层处理所有任务请求
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from eleven_blog_tunner.gateway.api_handler import APIHandler
from eleven_blog_tunner.api.routes.common import CommonResponse, SuccessResponse, ErrorResponse

router = APIRouter(prefix="/gateway", tags=["gateway"])

# 全局 APIHandler 实例
api_handler = APIHandler()

class GatewayTaskRequest(BaseModel):
    """网关任务请求模型"""
    task_type: str
    input_data: str
    user_id: str = "default"


class GatewayTaskResponse(BaseModel):
    """网关任务响应模型"""
    task_id: str
    status: str
    message: str


class GatewayTaskStatus(BaseModel):
    """网关任务状态模型"""
    task_id: str
    status: str
    data: Optional[Dict[str, Any]] = None


class GatewayTaskResult(BaseModel):
    """网关任务结果模型"""
    task_id: str
    status: str
    data: Optional[Dict[str, Any]] = None


@router.post("/tasks", response_model=CommonResponse[GatewayTaskResponse])
async def create_gateway_task(request: GatewayTaskRequest):
    """
    创建网关任务

    - **task_type**: 任务类型 (article_generation, style_analysis, article_review, system_status)
    - **input_data**: 输入数据
    - **user_id**: 用户 ID
    """
    try:
        result = await api_handler.create_task(
            task_type=request.task_type,
            input_data=request.input_data,
            user_id=request.user_id
        )
        return SuccessResponse.build(
            data=GatewayTaskResponse(
                task_id=result["task_id"],
                status="created",
                message=result["message"]
            ),
            message=result["message"]
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/tasks/{task_id}", response_model=CommonResponse[GatewayTaskStatus])
async def get_gateway_task_status(task_id: str):
    """
    获取网关任务状态
    """
    try:
        result = await api_handler.get_task_status(task_id)
        return SuccessResponse.build(
            data=GatewayTaskStatus(
                task_id=task_id,
                status=result["data"].get("status", "unknown"),
                data=result["data"]
            ),
            message="获取任务状态成功"
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/tasks/{task_id}/result", response_model=CommonResponse[GatewayTaskResult])
async def get_gateway_task_result(task_id: str):
    """
    获取网关任务结果
    """
    try:
        result = await api_handler.get_task_result(task_id)
        return SuccessResponse.build(
            data=GatewayTaskResult(
                task_id=task_id,
                status="completed",
                data=result["data"]
            ),
            message="获取任务结果成功"
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.delete("/tasks/{task_id}", response_model=CommonResponse[GatewayTaskStatus])
async def cancel_gateway_task(task_id: str):
    """
    取消网关任务
    """
    try:
        result = await api_handler.cancel_task(task_id)
        return SuccessResponse.build(
            data=GatewayTaskStatus(
                task_id=task_id,
                status="cancelled"
            ),
            message=result["message"]
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/tasks", response_model=CommonResponse)
async def list_gateway_tasks(user_id: Optional[str] = None):
    """
    列出网关任务

    - **user_id**: 可选的用户 ID
    """
    try:
        result = await api_handler.list_tasks(user_id)
        return SuccessResponse.build(
            data={
                "tasks": result["data"],
                "total": result["total"]
            },
            message="获取任务列表成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/health", response_model=CommonResponse)
async def gateway_health_check():
    """
    网关健康检查
    """
    try:
        result = await api_handler.health_check()
        return SuccessResponse.build(
            data=result,
            message="健康检查成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))