"""
文章生成与管理 API

支持两种生成模式：
1. 笔记整合模式（默认）- 基于笔记内容检索和整合生成文章
2. 风格+主题模式 - 基于风格配置和主题生成文章
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import time
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from eleven_blog_tunner.api.routes.common import (
    CommonResponse, SuccessResponse, ErrorResponse, ResponseCode
)
from eleven_blog_tunner.core.config import get_settings
from eleven_blog_tunner.common.models import Article, ArticleVersion, get_db
from eleven_blog_tunner.agents.writer_agent import WriterAgent
from eleven_blog_tunner.rag.style_manager import StyleManager
from eleven_blog_tunner.rag.note_retriever import RetrievalStrategy
from eleven_blog_tunner.services.article_generator import (
    ArticleGenerator, ArticleGenerationRequest, GenerationMode
)

# 导入 Celery 任务
try:
    from eleven_blog_tunner.tasks.article_tasks import generate_article_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleStatus(str, Enum):
    """文章状态"""
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class OutlineSection(BaseModel):
    """大纲章节"""
    title: str
    description: str
    word_count: Optional[str] = None


class ArticleGenerateRequest(BaseModel):
    """文章生成请求（兼容旧版）"""
    topic: str
    style_name: Optional[str] = None
    outline: Optional[List[OutlineSection]] = None
    target_length: Optional[int] = 1000
    metadata: Optional[Dict[str, Any]] = None


class GenerationModeEnum(str, Enum):
    """生成模式枚举"""
    NOTE_INTEGRATION = "note_integration"    # 笔记整合模式（默认）
    STYLE_TOPIC = "style_topic"                # 风格+主题模式


class ArticleGenerateRequestV2(BaseModel):
    """文章生成请求 V2 - 支持笔记整合模式
    
    这是新的文章生成接口，支持两种模式：
    - note_integration: 基于笔记内容检索和整合生成文章（默认）
    - style_topic: 基于风格配置和主题生成文章
    """
    topic: str
    mode: GenerationModeEnum = GenerationModeEnum.NOTE_INTEGRATION
    style_name: Optional[str] = None           # 可选的风格名称
    note_ids: Optional[List[str]] = None       # 指定笔记ID列表（mode=note_integration时有效）
    retrieval_strategy: str = "hybrid"         # 检索策略: vector/keyword/hybrid
    top_k: int = 10                            # 检索片段数量
    outline: Optional[List[OutlineSection]] = None
    target_length: int = 1000
    metadata: Optional[Dict[str, Any]] = None


class ArticleGenerateResponseData(BaseModel):
    """文章生成响应数据"""
    task_id: str
    status: str
    celery_task_id: Optional[str] = None


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
    """文章列表响应数据"""
    articles: List[ArticleResponseData]
    total: int


class ArticleVersionData(BaseModel):
    """文章版本数据"""
    version: int
    content: str
    created_at: float
    reason: Optional[str] = None


class PolishRequest(BaseModel):
    """润色请求"""
    style_name: Optional[str] = None


def article_to_dict(article: Article) -> Dict[str, Any]:
    """将 Article 模型转换为字典"""
    return {
        "id": str(article.id),
        "title": article.title,
        "content": article.content or "",
        "topic": article.source_topic or "",
        "style_name": None,  # 需要从 style_id 查询
        "status": article.status,
        "outline": article.outline,
        "metadata": article.metadata or {},
        "celery_task_id": article.celery_task_id,
        "created_at": article.created_at.timestamp() if article.created_at else time.time(),
        "updated_at": article.updated_at.timestamp() if article.updated_at else time.time(),
        "version": article.version or 1
    }


@router.post("/generate", response_model=CommonResponse[ArticleGenerateResponseData])
async def generate_article(
    request: ArticleGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    生成文章（通过 Celery 异步任务）
    
    流程：
    1. 创建文章记录，状态为 generating
    2. 启动 Celery 异步任务
    3. 返回任务ID，前端可以轮询检查状态
    """
    try:
        # 获取风格 ID（如果提供了风格名称）
        style_id = None
        if request.style_name:
            style_manager = StyleManager()
            try:
                style_data = await style_manager.load_style(request.style_name)
                # 风格存储在文件系统，使用风格名称作为标识
                style_id = uuid.uuid4()  # 临时生成，实际应该从风格存储中获取
            except FileNotFoundError:
                return ErrorResponse.bad_request(f"风格 '{request.style_name}' 不存在")
        
        # 创建文章记录
        article_id = uuid.uuid4()
        article = Article(
            id=article_id,
            user_id=uuid.uuid4(),  # TODO: 从认证获取
            style_id=style_id or uuid.uuid4(),
            title=request.topic,
            content="",
            source_topic=request.topic,
            status="generating",
            outline=[s.model_dump() for s in request.outline] if request.outline else None,
            word_count=0,
            version=1,
            metadata={
                "target_length": request.target_length,
                "style_name": request.style_name,
                "requested_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        # 启动 Celery 异步任务
        celery_task_id = None
        if CELERY_AVAILABLE:
            # 异步执行任务
            task = generate_article_task.delay(
                article_id=str(article_id),
                topic=request.topic,
                style_name=request.style_name,
                outline=[s.model_dump() for s in request.outline] if request.outline else None,
                target_length=request.target_length or 1000,
                user_id=str(article.user_id)
            )
            celery_task_id = task.id
            
            # 更新文章记录中的 Celery 任务ID
            article.celery_task_id = celery_task_id
            db.commit()
            
            logger.info(f"[Articles] 启动 Celery 任务: article_id={article_id}, celery_task_id={celery_task_id}")
        else:
            # Celery 不可用，使用后台任务（降级方案）
            logger.warning("[Articles] Celery 不可用，使用后台任务")
            # TODO: 实现同步执行或后台任务
        
        return SuccessResponse.build(
            data=ArticleGenerateResponseData(
                task_id=str(article_id),
                status="generating",
                celery_task_id=celery_task_id
            ),
            message=f"文章生成任务已创建，主题：{request.topic}"
        )
    except Exception as e:
        db.rollback()
        logger.exception(f"[Articles] 创建文章生成任务失败: {e}")
        return ErrorResponse.internal_error(message=str(e))


@router.get("/{article_id}/status", response_model=CommonResponse)
async def get_article_status(article_id: str, db: Session = Depends(get_db)):
    """
    获取文章生成状态
    
    如果文章正在生成中，会同时查询 Celery 任务状态
    """
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    response_data = {
        "article_id": str(article.id),
        "status": article.status,
        "progress": 0,
        "step": "",
        "celery_task_id": article.celery_task_id
    }
    
    # 如果文章正在生成中，查询 Celery 任务状态
    if article.status == "generating" and article.celery_task_id and CELERY_AVAILABLE:
        try:
            from celery.result import AsyncResult
            from eleven_blog_tunner.tasks.celery_app import celery_app
            
            task_result = AsyncResult(article.celery_task_id, app=celery_app)
            
            if task_result.state == 'PENDING':
                response_data["progress"] = 0
                response_data["step"] = "等待执行"
            elif task_result.state == 'PROGRESS':
                meta = task_result.info or {}
                response_data["progress"] = meta.get("progress", 50)
                response_data["step"] = meta.get("step", "执行中")
            elif task_result.state == 'SUCCESS':
                response_data["progress"] = 100
                response_data["step"] = "完成"
                # 如果 Celery 任务已完成但文章状态未更新，可能是回调失败
                # 这里可以触发一次状态同步
            elif task_result.state == 'FAILURE':
                response_data["progress"] = 0
                response_data["step"] = f"执行失败: {str(task_result.info)}"
            else:
                response_data["step"] = f"状态: {task_result.state}"
                
        except Exception as e:
            logger.error(f"[Articles] 查询 Celery 任务状态失败: {e}")
            response_data["step"] = "无法获取任务状态"
    
    return SuccessResponse.build(
        data=response_data,
        message="获取文章状态成功"
    )


@router.get("/{article_id}", response_model=CommonResponse[ArticleResponseData])
async def get_article(article_id: str, db: Session = Depends(get_db)):
    """获取文章详情"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    # 如果文章状态是 generating，检查是否需要更新
    if article.status == "generating":
        # 查询 Celery 任务状态
        if article.celery_task_id and CELERY_AVAILABLE:
            try:
                from celery.result import AsyncResult
                from eleven_blog_tunner.tasks.celery_app import celery_app
                
                task_result = AsyncResult(article.celery_task_id, app=celery_app)
                
                if task_result.state == 'SUCCESS':
                    # 任务已完成，更新文章状态
                    result = task_result.result
                    if result and result.get('success'):
                        article.status = 'draft'
                        db.commit()
                elif task_result.state == 'FAILURE':
                    # 任务失败
                    article.status = 'failed'
                    article.metadata = article.metadata or {}
                    article.metadata['error'] = str(task_result.info)
                    db.commit()
            except Exception as e:
                logger.error(f"[Articles] 同步 Celery 任务状态失败: {e}")
    
    return SuccessResponse.build(
        data=article_to_dict(article),
        message="获取文章详情成功"
    )


@router.get("", response_model=CommonResponse)
async def list_articles(
    status: Optional[str] = None,
    style_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    query = db.query(Article).filter(Article.deleted_at.is_(None))
    
    if status:
        query = query.filter(Article.status == status)
    
    total = query.count()
    articles = query.order_by(Article.updated_at.desc()).offset(skip).limit(limit).all()
    
    return SuccessResponse.build(
        data=ArticleListResponseData(
            articles=[article_to_dict(a) for a in articles],
            total=total
        ),
        message="获取文章列表成功"
    )


@router.put("/{article_id}", response_model=CommonResponse[ArticleResponseData])
async def update_article(
    article_id: str,
    content: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新文章内容"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    # 保存当前版本
    version = ArticleVersion(
        id=uuid.uuid4(),
        article_id=article.id,
        version=article.version,
        title=article.title,
        outline=article.outline,
        content=article.content or "",
        change_summary=reason
    )
    db.add(version)
    
    # 更新文章
    article.content = content
    article.version += 1
    article.status = "draft"
    article.updated_at = datetime.utcnow()
    article.word_count = len(content)
    
    db.commit()
    db.refresh(article)
    
    return SuccessResponse.build(
        data=article_to_dict(article),
        message=f"文章已更新，新版本：{article.version}"
    )


@router.delete("/{article_id}", response_model=CommonResponse)
async def delete_article(article_id: str, db: Session = Depends(get_db)):
    """删除文章（软删除）"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    article.deleted_at = datetime.utcnow()
    db.commit()
    
    return SuccessResponse.build(message="文章已删除")


@router.get("/{article_id}/versions", response_model=CommonResponse)
async def get_article_versions(article_id: str, db: Session = Depends(get_db)):
    """获取文章版本历史"""
    versions = db.query(ArticleVersion).filter(
        ArticleVersion.article_id == article_id
    ).order_by(ArticleVersion.version.desc()).all()
    
    return SuccessResponse.build(
        data={
            "versions": [
                {
                    "version": v.version,
                    "content": v.content,
                    "created_at": v.created_at.timestamp() if v.created_at else time.time(),
                    "reason": v.change_summary
                }
                for v in versions
            ]
        },
        message="获取版本历史成功"
    )


@router.get("/{article_id}/versions/{version}", response_model=CommonResponse)
async def get_specific_version(
    article_id: str,
    version: int,
    db: Session = Depends(get_db)
):
    """获取特定版本的文章"""
    version_record = db.query(ArticleVersion).filter(
        ArticleVersion.article_id == article_id,
        ArticleVersion.version == version
    ).first()
    
    if not version_record:
        return ErrorResponse.not_found(message="版本不存在")
    
    return SuccessResponse.build(
        data={
            "version": version_record.version,
            "content": version_record.content,
            "created_at": version_record.created_at.timestamp() if version_record.created_at else time.time(),
            "reason": version_record.change_summary
        },
        message=f"获取版本 {version} 成功"
    )


@router.post("/{article_id}/versions/{version}/restore", response_model=CommonResponse)
async def restore_version(
    article_id: str,
    version: int,
    db: Session = Depends(get_db)
):
    """恢复到特定版本"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    version_record = db.query(ArticleVersion).filter(
        ArticleVersion.article_id == article_id,
        ArticleVersion.version == version
    ).first()
    
    if not version_record:
        return ErrorResponse.not_found(message="版本不存在")
    
    # 保存当前版本
    current_version = ArticleVersion(
        id=uuid.uuid4(),
        article_id=article.id,
        version=article.version,
        title=article.title,
        outline=article.outline,
        content=article.content or "",
        change_summary=f"恢复到版本 {version}"
    )
    db.add(current_version)
    
    # 恢复到指定版本
    article.content = version_record.content
    article.version += 1
    article.status = "draft"
    article.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(article)
    
    return SuccessResponse.build(
        data={"current_version": article.version},
        message=f"已恢复到版本 {version}"
    )


@router.post("/{article_id}/polish", response_model=CommonResponse)
async def polish_article(
    article_id: str,
    request: PolishRequest,
    db: Session = Depends(get_db)
):
    """
    润色文章 - 使用 AI 改进文章质量
    """
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    try:
        # 保存当前版本
        version = ArticleVersion(
            id=uuid.uuid4(),
            article_id=article.id,
            version=article.version,
            title=article.title,
            outline=article.outline,
            content=article.content or "",
            change_summary="AI 润色"
        )
        db.add(version)
        
        # 使用 WriterAgent 润色文章
        writer = WriterAgent()
        
        # 构建润色提示
        polish_prompt = f"""请对以下文章进行润色，改进语言表达、逻辑结构和可读性。

原文：
{article.content}

请直接输出润色后的文章内容，保持原文的核心意思和结构，但提升写作质量。"""
        
        # 调用 LLM 进行润色
        messages = [
            {"role": "system", "content": "你是一位专业的文章编辑，擅长润色和优化文章。"},
            {"role": "user", "content": polish_prompt}
        ]
        
        polished_content = await writer.call_llm(messages, temperature=0.7)
        
        # 更新文章
        article.content = polished_content
        article.version += 1
        article.status = "draft"
        article.updated_at = datetime.utcnow()
        article.word_count = len(polished_content)
        
        db.commit()
        db.refresh(article)
        
        return SuccessResponse.build(
            data=article_to_dict(article),
            message="文章润色成功"
        )
    except Exception as e:
        db.rollback()
        return ErrorResponse.internal_error(message=f"润色失败: {str(e)}")


@router.post("/{article_id}/review", response_model=CommonResponse)
async def review_article(article_id: str, db: Session = Depends(get_db)):
    """提交文章审核"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    article.status = "reviewing"
    article.updated_at = datetime.utcnow()
    db.commit()
    
    return SuccessResponse.build(
        data={"status": article.status},
        message="文章已提交审核"
    )


@router.post("/{article_id}/approve", response_model=CommonResponse)
async def approve_article(article_id: str, db: Session = Depends(get_db)):
    """审核通过文章"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    article.status = "approved"
    article.updated_at = datetime.utcnow()
    db.commit()
    
    return SuccessResponse.build(
        data={"status": article.status},
        message="文章已通过审核"
    )


@router.post("/{article_id}/reject", response_model=CommonResponse)
async def reject_article(
    article_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """拒绝文章"""
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.deleted_at.is_(None)
    ).first()
    
    if not article:
        return ErrorResponse.not_found(message="文章不存在")
    
    article.status = "rejected"
    article.updated_at = datetime.utcnow()
    db.commit()
    
    return SuccessResponse.build(
        data={"status": article.status, "reason": reason},
        message="文章已拒绝"
    )


@router.post("/generate-v2", response_model=CommonResponse)
async def generate_article_v2(
    request: ArticleGenerateRequestV2,
    db: Session = Depends(get_db)
):
    """
    生成文章 V2 - 支持笔记整合模式
    
    这是新的文章生成接口，支持两种模式：
    
    **笔记整合模式** (mode=note_integration, 默认):
    - 根据主题自动检索相关笔记内容
    - 整合笔记内容生成文章
    - 可选：应用指定风格
    - 可选：指定特定笔记ID列表
    
    **风格+主题模式** (mode=style_topic):
    - 基于已学习的风格配置生成文章
    - 类似原版的生成方式
    
    参数：
    - topic: 文章主题（必填）
    - mode: 生成模式，note_integration 或 style_topic（默认: note_integration）
    - style_name: 风格名称（可选）
    - note_ids: 指定笔记ID列表（可选，仅在note_integration模式下有效）
    - retrieval_strategy: 检索策略，vector/keyword/hybrid（默认: hybrid）
    - top_k: 检索片段数量（默认: 10）
    - outline: 文章大纲（可选）
    - target_length: 目标字数（默认: 1000）
    """
    try:
        logger.info(f"[Articles V2] 开始生成文章: mode={request.mode.value}, topic={request.topic}")
        
        # 创建文章记录
        article_id = uuid.uuid4()
        article = Article(
            id=article_id,
            user_id=uuid.uuid4(),  # TODO: 从认证获取
            style_id=None,
            title=request.topic,
            content="",
            source_topic=request.topic,
            status="generating",
            outline=[s.model_dump() for s in request.outline] if request.outline else None,
            word_count=0,
            version=1,
            metadata={
                "target_length": request.target_length,
                "style_name": request.style_name,
                "mode": request.mode.value,
                "note_ids": request.note_ids,
                "retrieval_strategy": request.retrieval_strategy,
                "requested_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        # 解析检索策略
        try:
            strategy = RetrievalStrategy(request.retrieval_strategy)
        except ValueError:
            strategy = RetrievalStrategy.HYBRID
        
        # 创建生成请求
        gen_request = ArticleGenerationRequest(
            topic=request.topic,
            mode=GenerationMode(request.mode.value),
            style_name=request.style_name,
            note_ids=request.note_ids,
            retrieval_strategy=strategy,
            top_k=request.top_k,
            outline=[s.model_dump() for s in request.outline] if request.outline else None,
            target_length=request.target_length,
            user_id=str(article.user_id)
        )
        
        # 启动异步生成任务
        async def generate_async():
            try:
                generator = ArticleGenerator()
                result = await generator.generate(gen_request)
                
                # 更新文章记录
                article.content = result.content
                article.status = "draft"
                article.word_count = len(result.content)
                article.updated_at = datetime.utcnow()
                
                # 更新metadata
                article.metadata = article.metadata or {}
                article.metadata.update({
                    "generated_at": datetime.utcnow().isoformat(),
                    "used_notes": result.used_notes,
                    "style_applied": result.style_applied,
                    "outline": result.outline,
                    "generation_metadata": result.metadata
                })
                
                db.commit()
                logger.info(f"[Articles V2] 文章生成完成: article_id={article_id}")
                
            except Exception as e:
                logger.exception(f"[Articles V2] 文章生成失败: {e}")
                article.status = "failed"
                article.metadata = article.metadata or {}
                article.metadata["error"] = str(e)
                db.commit()
        
        # 使用后台任务执行
        import asyncio
        asyncio.create_task(generate_async())
        
        return SuccessResponse.build(
            data=ArticleGenerateResponseData(
                task_id=str(article_id),
                status="generating",
                celery_task_id=None
            ),
            message=f"文章生成任务已创建（{request.mode.value}模式），主题：{request.topic}"
        )
        
    except Exception as e:
        db.rollback()
        logger.exception(f"[Articles V2] 创建文章生成任务失败: {e}")
        return ErrorResponse.internal_error(message=str(e))


@router.get("/search-notes-for-topic", response_model=CommonResponse)
async def search_notes_for_topic(
    topic: str,
    strategy: str = "hybrid",
    top_k: int = 10,
    user_id: Optional[str] = None
):
    """
    根据主题搜索相关笔记
    
    用于在生成文章前预览哪些笔记会被使用
    
    参数：
    - topic: 主题/关键词
    - strategy: 检索策略 (vector/keyword/hybrid)
    - top_k: 返回片段数量
    """
    try:
        from eleven_blog_tunner.rag.note_retriever import NoteRetriever
        
        retriever = NoteRetriever()
        
        try:
            retrieval_strategy = RetrievalStrategy(strategy)
        except ValueError:
            retrieval_strategy = RetrievalStrategy.HYBRID
        
        result = await retriever.retrieve_by_topic(
            topic=topic,
            top_k=top_k,
            strategy=retrieval_strategy,
            user_id=user_id
        )
        
        # 格式化返回结果
        notes_info = []
        seen_notes = set()
        for chunk in result.chunks:
            if chunk.note_id not in seen_notes:
                seen_notes.add(chunk.note_id)
                notes_info.append({
                    "note_id": chunk.note_id,
                    "note_title": chunk.note_title,
                    "relevance_score": round(chunk.score, 4)
                })
        
        return SuccessResponse.build(
            data={
                "topic": topic,
                "total_notes": result.total_notes,
                "total_chunks": len(result.chunks),
                "strategy": result.strategy.value,
                "notes": notes_info,
                "chunks": [
                    {
                        "content": c.content[:200] + "..." if len(c.content) > 200 else c.content,
                        "note_title": c.note_title,
                        "score": round(c.score, 4)
                    }
                    for c in result.chunks
                ]
            },
            message=f"找到 {result.total_notes} 篇相关笔记，共 {len(result.chunks)} 个片段"
        )
        
    except Exception as e:
        logger.exception(f"搜索笔记失败: {e}")
        return ErrorResponse.internal_error(message=str(e))


# 导入 logger
from eleven_blog_tunner.utils.logger import logger_instance as logger
