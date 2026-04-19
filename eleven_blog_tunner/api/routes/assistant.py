"""
Assistant Agent API 路由

提供辅助文本生成功能的 HTTP 接口
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from eleven_blog_tunner.agents.assistant_agent import AssistantAgent
from eleven_blog_tunner.agents.base_agent import AgentContext
from eleven_blog_tunner.rag.style_manager import StyleManager
from eleven_blog_tunner.common.auth import get_current_user
from eleven_blog_tunner.api.routes.common import CommonResponse, SuccessResponse, ErrorResponse

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantExecuteRequest(BaseModel):
    """辅助任务执行请求"""
    task_type: str = Field(..., description="任务类型: continue/extract_style/rewrite/polish/suggest/expand/summarize")
    selected_text: str = Field(..., description="选中的文本内容")
    context: Optional[str] = Field(None, description="上下文内容")
    style: Optional[str] = Field(None, description="目标风格（用于改写）")
    style_hint: Optional[str] = Field(None, description="风格提示")
    length: Optional[int] = Field(200, description="生成长度")
    target_length: Optional[int] = Field(300, description="目标长度（用于扩写）")


class AssistantExecuteResponse(BaseModel):
    """辅助任务执行响应"""
    result: str
    task_type: str
    metadata: Optional[Dict[str, Any]] = None


class ExtractStyleFromEditorRequest(BaseModel):
    """从编辑器提取风格请求"""
    content: str = Field(..., description="编辑器内容")
    selection_start: Optional[int] = Field(None, description="选区开始位置")
    selection_end: Optional[int] = Field(None, description="选区结束位置")
    use_llm: bool = Field(True, description="是否使用 LLM 分析")


class ExtractStyleFromEditorResponse(BaseModel):
    """从编辑器提取风格响应"""
    style_name: str = "editor_style"
    features: Dict[str, Any]
    analysis_mode: Dict[str, bool]


@router.post("/execute", response_model=CommonResponse[AssistantExecuteResponse])
async def execute_assistant_task(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    执行辅助任务

    - **task_type**: 任务类型
        - continue: 续写
        - extract_style: 提取风格
        - rewrite: 改写
        - polish: 润色
        - suggest: 生成建议
        - expand: 扩写
        - summarize: 总结
    - **selected_text**: 选中的文本
    - **context**: 上下文（可选）
    - **style**: 目标风格（改写时必需）
    - **length**: 生成长度（续写时可选，默认200）
    - **target_length**: 目标长度（扩写时可选，默认300）
    """
    try:
        # 创建 AssistantAgent 实例
        agent = AssistantAgent(llm_provider="openai", use_memory=False)

        # 构建上下文
        context = AgentContext(
            user_input=request.selected_text,
            metadata={
                "task_type": request.task_type,
                "selected_text": request.selected_text,
                "context": request.context or "",
                "style": request.style,
                "style_hint": request.style_hint,
                "length": request.length,
                "target_length": request.target_length
            }
        )

        # 执行任务
        result = await agent.execute(context)

        # 构建响应
        response_data = AssistantExecuteResponse(
            result=result,
            task_type=request.task_type,
            metadata={
                "word_count": len(result),
                "selected_length": len(request.selected_text)
            }
        )

        return SuccessResponse.build(
            data=response_data,
            message="任务执行成功"
        )

    except Exception as e:
        return ErrorResponse.internal_error(message=f"任务执行失败: {str(e)}")


@router.post("/extract-style", response_model=CommonResponse[ExtractStyleFromEditorResponse])
async def extract_style_from_editor(
    request: ExtractStyleFromEditorRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    从编辑器内容提取风格

    - **content**: 编辑器完整内容
    - **selection_start**: 选区开始位置（可选）
    - **selection_end**: 选区结束位置（可选）
    - **use_llm**: 是否使用 LLM 分析（默认true）
    """
    try:
        if not request.content or len(request.content) < 100:
            return ErrorResponse.bad_request("内容太短，无法提取风格（至少需要100字符）")

        # 如果有选区，优先使用选区内容
        if request.selection_start is not None and request.selection_end is not None:
            text = request.content[request.selection_start:request.selection_end]
        else:
            text = request.content

        # 使用 StyleManager 提取风格
        style_manager = StyleManager(use_llm=request.use_llm)

        style_data = await style_manager.extract_style(
            text=text,
            style_name="editor_style",
            metadata={"source": "editor", "use_llm": request.use_llm},
            use_statistical=True,
            use_semantic=request.use_llm,
            use_embedding=True
        )

        # 构建响应
        response_data = ExtractStyleFromEditorResponse(
            style_name=style_data["name"],
            features=style_data["features"],
            analysis_mode=style_data.get("analysis_mode", {
                "use_statistical": True,
                "use_semantic": request.use_llm,
                "use_embedding": True
            })
        )

        return SuccessResponse.build(
            data=response_data,
            message="风格提取成功"
        )

    except Exception as e:
        return ErrorResponse.internal_error(message=f"风格提取失败: {str(e)}")


@router.post("/continue", response_model=CommonResponse[AssistantExecuteResponse])
async def continue_writing(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """续写文本"""
    request.task_type = "continue"
    return await execute_assistant_task(request, current_user)


@router.post("/extract-selection-style", response_model=CommonResponse[AssistantExecuteResponse])
async def extract_selection_style(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """提取选中内容的风格"""
    request.task_type = "extract_style"
    return await execute_assistant_task(request, current_user)


@router.post("/rewrite", response_model=CommonResponse[AssistantExecuteResponse])
async def rewrite_content(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """改写内容"""
    request.task_type = "rewrite"
    if not request.style:
        return ErrorResponse.bad_request("改写需要提供目标风格")
    return await execute_assistant_task(request, current_user)


@router.post("/polish", response_model=CommonResponse[AssistantExecuteResponse])
async def polish_text(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """润色文本"""
    request.task_type = "polish"
    return await execute_assistant_task(request, current_user)


@router.post("/suggest", response_model=CommonResponse[AssistantExecuteResponse])
async def generate_suggestions(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """生成写作建议"""
    request.task_type = "suggest"
    return await execute_assistant_task(request, current_user)


@router.post("/expand", response_model=CommonResponse[AssistantExecuteResponse])
async def expand_content(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """扩写内容"""
    request.task_type = "expand"
    return await execute_assistant_task(request, current_user)


@router.post("/summarize", response_model=CommonResponse[AssistantExecuteResponse])
async def summarize_content(
    request: AssistantExecuteRequest,
    current_user: Any = Depends(get_current_user)
):
    """总结内容"""
    request.task_type = "summarize"
    return await execute_assistant_task(request, current_user)
