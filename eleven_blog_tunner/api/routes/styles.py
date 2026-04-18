"""
风格管理 API

通过 Gateway 层统一处理风格学习任务
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
from eleven_blog_tunner.api.routes.common import (
    CommonResponse, SuccessResponse, ErrorResponse, ResponseCode
)
from eleven_blog_tunner.core.config import get_settings

router = APIRouter(prefix="/styles", tags=["styles"])


class StyleExtractRequest(BaseModel):
    """风格提取请求"""
    text: str
    style_name: str
    metadata: Optional[Dict[str, Any]] = None


class StyleFeaturesResponse(BaseModel):
    """风格特征响应"""
    vocabulary_diversity: float
    average_word_length: float
    unique_words_ratio: float
    average_sentence_length: float
    sentence_complexity: float
    punctuation_density: float
    paragraph_average_length: float
    transition_words_ratio: float
    passive_voice_ratio: float
    first_person_ratio: float
    emoji_usage: float


class StyleResponseData(BaseModel):
    """风格响应数据"""
    name: str
    features: StyleFeaturesResponse
    vector: List[float]
    metadata: Dict[str, Any]


async def call_gateway_api(endpoint: str, method: str = "POST", data: dict = None) -> Dict:
    """
    调用 Gateway API
    """
    settings = get_settings()
    url = f"{settings.api_base_url}/api/v1/gateway{endpoint}"
    async with httpx.AsyncClient() as client:
        if method == "POST":
            response = await client.post(url, json=data)
        elif method == "GET":
            response = await client.get(url)
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Gateway API 调用失败")
            )
        
        return response.json()


@router.post("/learn", response_model=CommonResponse[StyleResponseData])
async def learn_style(request: StyleExtractRequest):
    """
    从文本学习风格

    - **text**: 文本内容（从笔记中提取的写作样本）
    - **style_name**: 风格名称
    - **metadata**: 可选的元数据
    """
    try:
        # 构建任务输入数据
        input_data = {
            "text": request.text,
            "style_name": request.style_name,
            "metadata": request.metadata or {}
        }

        # 通过 Gateway 创建风格分析任务
        result = await call_gateway_api(
            "/tasks",
            method="POST",
            data={
                "task_type": "style_analysis",
                "input_data": str(input_data),
                "user_id": "default"
            }
        )

        # 模拟风格学习结果
        # 实际应该从 Gateway 任务结果中获取
        style_data = {
            "name": request.style_name,
            "features": {
                "vocabulary_diversity": 0.75,
                "average_word_length": 4.2,
                "unique_words_ratio": 0.65,
                "average_sentence_length": 25.3,
                "sentence_complexity": 1.8,
                "punctuation_density": 0.12,
                "paragraph_average_length": 150.5,
                "transition_words_ratio": 0.08,
                "passive_voice_ratio": 0.15,
                "first_person_ratio": 0.20,
                "emoji_usage": 0.02
            },
            "vector": [0.1] * 10,  # 模拟向量
            "metadata": request.metadata or {}
        }

        features = style_data['features']
        features_response = StyleFeaturesResponse(
            vocabulary_diversity=features.get('vocabulary_diversity', 0.0),
            average_word_length=features.get('average_word_length', 0.0),
            unique_words_ratio=features.get('unique_words_ratio', 0.0),
            average_sentence_length=features.get('average_sentence_length', 0.0),
            sentence_complexity=features.get('sentence_complexity', 0.0),
            punctuation_density=features.get('punctuation_density', 0.0),
            paragraph_average_length=features.get('paragraph_average_length', 0.0),
            transition_words_ratio=features.get('transition_words_ratio', 0.0),
            passive_voice_ratio=features.get('passive_voice_ratio', 0.0),
            first_person_ratio=features.get('first_person_ratio', 0.0),
            emoji_usage=features.get('emoji_usage', 0.0)
        )

        data = StyleResponseData(
            name=style_data['name'],
            features=features_response,
            vector=style_data['vector'],
            metadata=style_data.get('metadata', {})
        )

        return SuccessResponse.build(
            data=data,
            message="风格学习成功"
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/learn-from-file", response_model=CommonResponse)
async def learn_style_from_file(
    file: UploadFile = File(...),
    style_name: str = Form(...)
):
    """
    从上传的文件学习风格

    - **file**: 文本文件 (Markdown/TXT)
    - **style_name**: 风格名称
    """
    try:
        content = await file.read()
        content_str = content.decode("utf-8")

        # 构建任务输入数据
        input_data = {
            "text": content_str,
            "style_name": style_name,
            "metadata": {"source_file": file.filename}
        }

        # 通过 Gateway 创建风格分析任务
        result = await call_gateway_api(
            "/tasks",
            method="POST",
            data={
                "task_type": "style_analysis",
                "input_data": str(input_data),
                "user_id": "default"
            }
        )

        return SuccessResponse.build(
            data={"style_name": style_name},
            message=f"风格 '{style_name}' 学习成功"
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/list", response_model=CommonResponse)
async def list_styles():
    """
    获取风格列表
    """
    try:
        # 模拟风格列表
        # 实际应该从 Gateway 或数据库获取
        styles = ["my_style", "formal_style", "casual_style"]
        return SuccessResponse.build(
            data={"styles": styles},
            message="获取风格列表成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/{style_name}", response_model=CommonResponse[StyleResponseData])
async def get_style(style_name: str):
    """
    获取指定风格的详细信息
    """
    try:
        # 模拟风格数据
        # 实际应该从 Gateway 或数据库获取
        style_data = {
            "name": style_name,
            "features": {
                "vocabulary_diversity": 0.75,
                "average_word_length": 4.2,
                "unique_words_ratio": 0.65,
                "average_sentence_length": 25.3,
                "sentence_complexity": 1.8,
                "punctuation_density": 0.12,
                "paragraph_average_length": 150.5,
                "transition_words_ratio": 0.08,
                "passive_voice_ratio": 0.15,
                "first_person_ratio": 0.20,
                "emoji_usage": 0.02
            },
            "vector": [0.1] * 10,
            "metadata": {}
        }

        features = style_data['features']
        features_response = StyleFeaturesResponse(
            vocabulary_diversity=features.get('vocabulary_diversity', 0.0),
            average_word_length=features.get('average_word_length', 0.0),
            unique_words_ratio=features.get('unique_words_ratio', 0.0),
            average_sentence_length=features.get('average_sentence_length', 0.0),
            sentence_complexity=features.get('sentence_complexity', 0.0),
            punctuation_density=features.get('punctuation_density', 0.0),
            paragraph_average_length=features.get('paragraph_average_length', 0.0),
            transition_words_ratio=features.get('transition_words_ratio', 0.0),
            passive_voice_ratio=features.get('passive_voice_ratio', 0.0),
            first_person_ratio=features.get('first_person_ratio', 0.0),
            emoji_usage=features.get('emoji_usage', 0.0)
        )

        data = StyleResponseData(
            name=style_data['name'],
            features=features_response,
            vector=style_data['vector'],
            metadata=style_data.get('metadata', {})
        )

        return SuccessResponse.build(
            data=data,
            message="获取风格详情成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.delete("/{style_name}", response_model=CommonResponse)
async def delete_style(style_name: str):
    """
    删除指定风格
    """
    try:
        # 模拟删除操作
        # 实际应该通过 Gateway 或数据库操作
        return SuccessResponse.build(
            message=f"风格 '{style_name}' 已删除"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/{style_name}/references", response_model=CommonResponse)
async def get_style_references(style_name: str, top_k: int = 5):
    """
    获取风格参考段落

    - **style_name**: 风格名称
    - **top_k**: 返回的参考段落数量
    """
    try:
        # 模拟参考段落
        # 实际应该从 Gateway 或数据库获取
        references = [
            {"content": "参考段落内容 1", "score": 0.92},
            {"content": "参考段落内容 2", "score": 0.85}
        ]
        return SuccessResponse.build(
            data={"references": references},
            message="获取风格参考段落成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/preview", response_model=CommonResponse)
async def preview_style(
    file: UploadFile = File(...),
    style_name: str = Form(None)
):
    """
    预览风格特征（不保存）

    - **file**: 文本文件
    - **style_name**: 可选的风格名称用于对比
    """
    try:
        content = await file.read()
        content_str = content.decode("utf-8")

        # 构建任务输入数据
        input_data = {
            "text": content_str,
            "style_name": style_name
        }

        # 通过 Gateway 创建风格分析任务
        result = await call_gateway_api(
            "/tasks",
            method="POST",
            data={
                "task_type": "style_analysis",
                "input_data": str(input_data),
                "user_id": "default"
            }
        )

        # 模拟风格预览结果
        data = {
            "features": {
                "vocabulary_diversity": 0.75,
                "average_word_length": 4.2,
                "unique_words_ratio": 0.65,
                "average_sentence_length": 25.3,
                "sentence_complexity": 1.8,
                "punctuation_density": 0.12,
                "paragraph_average_length": 150.5,
                "transition_words_ratio": 0.08,
                "passive_voice_ratio": 0.15,
                "first_person_ratio": 0.20,
                "emoji_usage": 0.02
            },
            "vector_length": 10
        }

        if style_name:
            data["similarity"] = 0.85

        return SuccessResponse.build(
            data=data,
            message="风格预览成功"
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))