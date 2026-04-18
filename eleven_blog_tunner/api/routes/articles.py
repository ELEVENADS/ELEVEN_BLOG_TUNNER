"""
文章生成与管理 API

通过 Gateway 层统一处理文章生成任务
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import time
import httpx
from eleven_blog_tunner.api.routes.common import (
    CommonResponse, SuccessResponse, ErrorResponse, ResponseCode
)
from eleven_blog_tunner.core.config import get_settings

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleStatus(str, Enum):
    """文章状态"""
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class OutlineSection(BaseModel):
    """大纲章节"""
    title: str
    description: str
    word_count: Optional[str] = None


class ArticleGenerateRequest(BaseModel):
    """文章生成请求"""
    topic: str
    style_name: Optional[str] = None
    outline: Optional[List[OutlineSection]] = None
    target_length: Optional[int] = 1000
    metadata: Optional[Dict[str, Any]] = None


class ArticleGenerateResponseData(BaseModel):
    """文章生成响应数据"""
    task_id: str
    status: str


class ArticleResponseData(BaseModel):
    """文章响应数据"""
    id: str
    title: str
    content: str
    topic: str
    style_name: Optional[str]
    status: ArticleStatus
    outline: Optional[List[OutlineSection]] = None
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float
    version: int = 1


class ArticleListResponseData(BaseModel):
    """
    文章列表响应数据
    """
    articles: List[ArticleResponseData]
    total: int


class ArticleVersionData(BaseModel):
    """文章版本数据"""
    version: int
    content: str
    created_at: float
    reason: Optional[str] = None


# 本地存储（后续可迁移到数据库）
articles_storage: Dict[str, ArticleResponseData] = {}
article_versions: Dict[str, List[ArticleVersionData]] = {}


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


@router.post("/generate", response_model=CommonResponse[ArticleGenerateResponseData])
async def generate_article(request: ArticleGenerateRequest):
    """
    生成文章（通过 Gateway 层）

    - **topic**: 文章主题/标题
    - **style_name**: 风格名称（从已学习的风格中选择）
    - **outline**: 可选的自定义大纲
    - **target_length**: 目标字数
    """
    try:
        # 构建任务输入数据
        input_data = {
            "topic": request.topic,
            "style_name": request.style_name,
            "outline": [s.model_dump() for s in request.outline] if request.outline else None,
            "target_length": request.target_length,
            "metadata": request.metadata or {}
        }

        # 通过 Gateway 创建文章生成任务
        result = await call_gateway_api(
            "/tasks",
            method="POST",
            data={
                "task_type": "article_generation",
                "input_data": str(input_data),
                "user_id": "default"
            }
        )

        task_id = result["data"]["task_id"]

        # 创建文章记录
        article = ArticleResponseData(
            id=task_id,
            title=request.topic,
            content="",
            topic=request.topic,
            style_name=request.style_name,
            status=ArticleStatus.GENERATING,
            outline=request.outline,
            metadata=input_data,
            created_at=time.time(),
            updated_at=time.time()
        )
        articles_storage[task_id] = article

        return SuccessResponse.build(
            data=ArticleGenerateResponseData(
                task_id=task_id,
                status="generating"
            ),
            message=f"文章生成任务已创建，主题：{request.topic}"
        )
    except HTTPException as e:
        return ErrorResponse.build(
            code=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/{article_id}", response_model=CommonResponse[ArticleResponseData])
async def get_article(article_id: str):
    """
    获取文章详情
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    article = articles_storage[article_id]
    
    # 如果文章状态是 generating，检查任务状态
    if article.status == ArticleStatus.GENERATING:
        try:
            # 检查 Gateway 任务状态
            task_status = await call_gateway_api(
                f"/tasks/{article_id}",
                method="GET"
            )
            
            task_data = task_status["data"]["data"]
            if task_data.get("status") == "completed":
                # 获取任务结果
                task_result = await call_gateway_api(
                    f"/tasks/{article_id}/result",
                    method="GET"
                )
                
                # 更新文章内容和状态
                article.content = task_result["data"]["data"].get("result", "")
                article.status = ArticleStatus.DRAFT
                article.updated_at = time.time()
        except Exception:
            # 忽略 Gateway 调用错误，保持原有状态
            pass

    return SuccessResponse.build(
        data=article,
        message="获取文章详情成功"
    )


@router.get("", response_model=CommonResponse)
async def list_articles(
    status: Optional[ArticleStatus] = None,
    style_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    """
    获取文章列表

    - **status**: 按状态筛选
    - **style_name**: 按风格筛选
    - **skip**: 跳过数量
    - **limit**: 返回数量
    """
    articles = list(articles_storage.values())

    if status:
        articles = [a for a in articles if a.status == status]
    if style_name:
        articles = [a for a in articles if a.style_name == style_name]

    articles.sort(key=lambda x: x.updated_at, reverse=True)

    total = len(articles)
    paginated = articles[skip:skip + limit]

    return SuccessResponse.build(
        data=ArticleListResponseData(articles=paginated, total=total),
        message="获取文章列表成功"
    )


@router.put("/{article_id}", response_model=CommonResponse[ArticleResponseData])
async def update_article(article_id: str, content: str, reason: Optional[str] = None):
    """
    更新文章内容

    - **content**: 新的文章内容
    - **reason**: 版本更新原因
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    article = articles_storage[article_id]

    if article_id not in article_versions:
        article_versions[article_id] = []

    article_versions[article_id].append(ArticleVersionData(
        version=article.version,
        content=article.content,
        created_at=time.time(),
        reason=reason
    ))

    article.content = content
    article.updated_at = time.time()
    article.version += 1
    article.status = ArticleStatus.DRAFT

    return SuccessResponse.build(
        data=article,
        message=f"文章已更新，新版本：{article.version}"
    )


@router.delete("/{article_id}", response_model=CommonResponse)
async def delete_article(article_id: str):
    """
    删除文章
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    # 尝试取消 Gateway 任务
    try:
        await call_gateway_api(
            f"/tasks/{article_id}",
            method="DELETE"
        )
    except Exception:
        # 忽略取消错误
        pass

    del articles_storage[article_id]
    if article_id in article_versions:
        del article_versions[article_id]

    return SuccessResponse.build(message="文章已删除")


@router.get("/{article_id}/versions", response_model=CommonResponse)
async def get_article_versions(article_id: str):
    """
    获取文章版本历史
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    versions = article_versions.get(article_id, [])
    return SuccessResponse.build(
        data={"versions": versions},
        message="获取版本历史成功"
    )


@router.get("/{article_id}/versions/{version}", response_model=CommonResponse[ArticleVersionData])
async def get_specific_version(article_id: str, version: int):
    """
    获取特定版本的文章
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    versions = article_versions.get(article_id, [])
    for v in versions:
        if v.version == version:
            return SuccessResponse.build(
                data=v,
                message=f"获取版本 {version} 成功"
            )

    return ErrorResponse.not_found(message="版本不存在")


@router.post("/{article_id}/versions/{version}/restore", response_model=CommonResponse)
async def restore_version(article_id: str, version: int):
    """
    恢复到特定版本
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    versions = article_versions.get(article_id, [])
    version_to_restore = None

    for v in versions:
        if v.version == version:
            version_to_restore = v
            break

    if not version_to_restore:
        return ErrorResponse.not_found(message="版本不存在")

    article = articles_storage[article_id]

    article_versions[article_id].append(ArticleVersionData(
        version=article.version,
        content=article.content,
        created_at=time.time(),
        reason="恢复到版本 " + str(version)
    ))

    article.content = version_to_restore.content
    article.updated_at = time.time()
    article.version += 1
    article.status = ArticleStatus.DRAFT

    return SuccessResponse.build(
        data={
            "current_version": article.version
        },
        message=f"已恢复到版本 {version}"
    )


@router.post("/{article_id}/outline", response_model=CommonResponse[ArticleResponseData])
async def generate_outline(article_id: str, topic: str, style_name: Optional[str] = None):
    """
    为文章生成或更新大纲

    - **topic**: 文章主题
    - **style_name**: 风格名称
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    try:
        # 通过 Gateway 创建风格分析任务
        input_data = {
            "topic": topic,
            "style_name": style_name
        }

        result = await call_gateway_api(
            "/tasks",
            method="POST",
            data={
                "task_type": "style_analysis",
                "input_data": str(input_data),
                "user_id": "default"
            }
        )

        # 模拟大纲生成
        outline = [
            OutlineSection(title="引言", description="介绍主题背景"),
            OutlineSection(title="主要内容", description="详细论述"),
            OutlineSection(title="总结", description="总结要点")
        ]

        article = articles_storage[article_id]
        article.outline = outline
        article.metadata["topic"] = topic
        article.metadata["style_name"] = style_name
        article.updated_at = time.time()

        return SuccessResponse.build(
            data=article,
            message="大纲生成成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/{article_id}/polish", response_model=CommonResponse[ArticleResponseData])
async def polish_article(article_id: str, style_name: Optional[str] = None):
    """
    润色文章

    - **style_name**: 可选的新风格名称
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    try:
        article = articles_storage[article_id]

        # 通过 Gateway 创建文章审核任务（用于润色）
        input_data = {
            "content": article.content,
            "style_name": style_name or article.style_name
        }

        result = await call_gateway_api(
            "/tasks",
            method="POST",
            data={
                "task_type": "article_review",
                "input_data": str(input_data),
                "user_id": "default"
            }
        )

        # 模拟润色结果
        polished_content = article.content  # 实际应该使用 Gateway 返回的结果

        article.content = polished_content
        article.updated_at = time.time()

        if style_name:
            article.style_name = style_name

        return SuccessResponse.build(
            data=article,
            message="文章润色成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/{article_id}/review", response_model=CommonResponse)
async def review_article(article_id: str):
    """
    提交文章审核
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    article = articles_storage[article_id]
    article.status = ArticleStatus.REVIEWING
    article.updated_at = time.time()

    return SuccessResponse.build(
        data={"status": article.status},
        message="文章已提交审核"
    )


@router.post("/{article_id}/approve", response_model=CommonResponse)
async def approve_article(article_id: str):
    """
    审核通过文章
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    article = articles_storage[article_id]
    article.status = ArticleStatus.APPROVED
    article.updated_at = time.time()

    return SuccessResponse.build(
        data={"status": article.status},
        message="文章已通过审核"
    )


@router.post("/{article_id}/reject", response_model=CommonResponse)
async def reject_article(article_id: str, reason: Optional[str] = None):
    """
    拒绝文章

    - **reason**: 拒绝原因
    """
    if article_id not in articles_storage:
        return ErrorResponse.not_found(message="文章不存在")

    article = articles_storage[article_id]
    article.status = ArticleStatus.REJECTED
    article.metadata["reject_reason"] = reason
    article.updated_at = time.time()

    return SuccessResponse.build(
        data={"status": article.status, "reason": reason},
        message="文章已拒绝"
    )