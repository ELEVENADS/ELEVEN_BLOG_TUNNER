"""
文件树相关 API 接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from eleven_blog_tunner.common.models import User, Note, Article, NoteCategory, get_db
from eleven_blog_tunner.common.auth import get_current_user
from eleven_blog_tunner.utils.logger import logger
from .common import SuccessResponse, ErrorResponse, CommonResponse

router = APIRouter(tags=["file-tree"])


class FolderCreate(BaseModel):
    """创建文件夹请求模型"""
    name: str
    type: str = "all"  # all, note, article
    parent_id: Optional[str] = None


class CategoryUpdate(BaseModel):
    """更新分类请求模型"""
    name: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None


class NoteCreate(BaseModel):
    """创建笔记请求模型"""
    title: str
    content: str
    category_id: Optional[str] = None


class NoteUpdate(BaseModel):
    """更新笔记请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[str] = None


class ArticleCreate(BaseModel):
    """创建文章请求模型"""
    title: str
    content: Optional[str] = None
    style_id: Optional[str] = None
    category_id: Optional[str] = None


class ArticleUpdate(BaseModel):
    """更新文章请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[str] = None


class MoveNodeRequest(BaseModel):
    """移动节点请求模型"""
    node_id: str
    node_type: str  # category, note, article
    target_parent_id: Optional[str] = None
    position: Optional[int] = None


class NoteImportFile(BaseModel):
    """导入笔记文件模型"""
    path: str
    content: str
    category_id: Optional[str] = None


class NoteImportRequest(BaseModel):
    """批量导入笔记请求模型"""
    files: List[NoteImportFile]
    auto_create_folders: bool = True


class TreeNode(BaseModel):
    """文件树节点模型"""
    id: str
    label: str
    type: str  # folder, note, article
    children: Optional[List['TreeNode']] = None
    data: Optional[dict] = None


class FileTreeResponse(BaseModel):
    """文件树响应模型"""
    tree: List[TreeNode]


@router.get("/file-tree", response_model=CommonResponse[FileTreeResponse])
async def get_file_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的完整文件树
    返回笔记和文章的联合树形结构
    """
    try:
        # 1. 获取用户的分类（文件夹）
        categories = db.query(NoteCategory).filter(
            NoteCategory.user_id == current_user.id
        ).all()
        
        # 2. 获取用户的笔记
        notes = db.query(Note).filter(
            Note.user_id == current_user.id,
            Note.deleted_at.is_(None)
        ).all()
        
        # 3. 获取用户的文章
        articles = db.query(Article).filter(
            Article.user_id == current_user.id,
            Article.deleted_at.is_(None)
        ).all()
        
        # 4. 构建树形结构
        tree = build_file_tree(categories, notes, articles)
        
        return SuccessResponse.build(
            data=FileTreeResponse(tree=tree),
            message="获取文件树成功"
        )
    except Exception as e:
        logger.error(f"获取文件树失败: {e}")
        return ErrorResponse.internal_error("获取文件树失败")


def build_file_tree(categories, notes, articles):
    """构建文件树"""
    # 创建分类节点
    category_map = {c.id: c for c in categories}
    
    # 按 type 分组分类
    note_folders = [c for c in categories if c.type in ['note', 'all']]
    article_folders = [c for c in categories if c.type in ['article', 'all']]
    
    tree = []
    
    # 添加笔记文件夹
    if note_folders:
        tree.append({
            "id": "notes-root",
            "label": "笔记",
            "type": "folder",
            "children": build_folder_tree(note_folders, notes, 'note')
        })
    
    # 添加文章文件夹
    if article_folders:
        tree.append({
            "id": "articles-root",
            "label": "文章",
            "type": "folder",
            "children": build_folder_tree(article_folders, articles, 'article')
        })
    
    return tree


def build_folder_tree(folders, items, item_type):
    """构建文件夹子树"""
    # 按 category_id 分组
    items_by_category = {}
    for item in items:
        cat_id = item.category_id
        if cat_id not in items_by_category:
            items_by_category[cat_id] = []
        items_by_category[cat_id].append(item)
    
    result = []
    for folder in folders:
        node = {
            "id": str(folder.id),
            "label": folder.name,
            "type": "folder",
            "children": []
        }
        
        # 添加子文件夹
        child_folders = [f for f in folders if f.parent_id == folder.id]
        if child_folders:
            node["children"].extend(build_folder_tree(child_folders, items, item_type))
        
        # 添加文件
        if folder.id in items_by_category:
            for item in items_by_category[folder.id]:
                node["children"].append({
                    "id": f"{item_type}-{item.id}",
                    "label": item.title,
                    "type": item_type,
                    "data": {
                        "id": str(item.id),
                        "title": item.title,
                        "content": getattr(item, 'content', None),
                        "created_at": item.created_at.isoformat() if item.created_at else None
                    }
                })
        
        result.append(node)
    
    return result


@router.post("/categories", response_model=CommonResponse[dict])
async def create_category(
    request: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建文件夹/分类
    """
    try:
        # 检查父分类是否存在
        parent = None
        if request.parent_id:
            parent = db.query(NoteCategory).filter(
                NoteCategory.id == request.parent_id,
                NoteCategory.user_id == current_user.id
            ).first()
            if not parent:
                return ErrorResponse.not_found("父分类不存在")
        
        # 创建新分类
        category = NoteCategory(
            user_id=current_user.id,
            parent_id=request.parent_id,
            name=request.name,
            type=request.type
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return SuccessResponse.build(
            data={
                "id": str(category.id),
                "name": category.name,
                "type": category.type,
                "parent_id": category.parent_id
            },
            message="创建分类成功"
        )
    except Exception as e:
        logger.error(f"创建分类失败: {e}")
        return ErrorResponse.internal_error("创建分类失败")


@router.delete("/categories/{category_id}", response_model=CommonResponse[dict])
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除分类
    """
    try:
        # 检查分类是否存在
        category = db.query(NoteCategory).filter(
            NoteCategory.id == category_id,
            NoteCategory.user_id == current_user.id
        ).first()
        if not category:
            return ErrorResponse.not_found("分类不存在")
        
        # 检查是否有子分类
        child_count = db.query(NoteCategory).filter(
            NoteCategory.parent_id == category_id
        ).count()
        if child_count > 0:
            return ErrorResponse.bad_request("该分类下有子分类，无法删除")
        
        # 检查是否有笔记或文章
        note_count = db.query(Note).filter(
            Note.category_id == category_id
        ).count()
        article_count = db.query(Article).filter(
            Article.category_id == category_id
        ).count()
        if note_count > 0 or article_count > 0:
            return ErrorResponse.bad_request("该分类下有文件，无法删除")
        
        # 删除分类
        db.delete(category)
        db.commit()
        
        return SuccessResponse.build(
            data={"message": "分类删除成功"},
            message="分类删除成功"
        )
    except Exception as e:
        logger.error(f"删除分类失败: {e}")
        return ErrorResponse.internal_error("删除分类失败")


@router.post("/notes/import", response_model=CommonResponse[dict])
async def import_notes(
    request: NoteImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量导入笔记（支持 Obsidian 目录结构）
    自动根据路径创建分类
    """
    try:
        created_notes = []
        
        for file in request.files:
            # 解析路径，创建分类
            if request.auto_create_folders:
                category = await ensure_category_from_path(
                    db, current_user.id, file.path, "note"
                )
            else:
                category = None
                if file.category_id:
                    category = db.query(NoteCategory).filter(
                        NoteCategory.id == file.category_id,
                        NoteCategory.user_id == current_user.id
                    ).first()
            
            # 创建笔记
            note = Note(
                user_id=current_user.id,
                category_id=category.id if category else None,
                title=extract_filename(file.path),
                content=file.content,
                source_type="markdown",
                word_count=len(file.content),
                status="active"
            )
            db.add(note)
            created_notes.append(note)
        
        db.commit()
        
        return SuccessResponse.build(
            data={
                "success": True,
                "imported_count": len(created_notes),
                "notes": [{"id": str(n.id), "title": n.title} for n in created_notes]
            },
            message=f"成功导入 {len(created_notes)} 条笔记"
        )
    except Exception as e:
        logger.error(f"导入笔记失败: {e}")
        return ErrorResponse.internal_error("导入笔记失败")


async def ensure_category_from_path(db, user_id, path, category_type):
    """根据路径自动创建分类"""
    # 解析路径：/编程/Python基础.md -> ["编程", "Python基础.md"]
    parts = path.strip("/").split("/")[:-1]  # 去掉文件名
    
    parent_id = None
    current_type = category_type
    
    for i, part in enumerate(parts):
        # 检查是否已存在
        existing = db.query(NoteCategory).filter(
            NoteCategory.user_id == user_id,
            NoteCategory.name == part,
            NoteCategory.parent_id == parent_id
        ).first()
        
        if existing:
            parent_id = existing.id
            continue
        
        # 确定类型：中间层级用 'all'，最后一级用具体类型
        if i == len(parts) - 1:
            cat_type = current_type
        else:
            cat_type = 'all'
        
        # 创建新分类
        new_category = NoteCategory(
            user_id=user_id,
            parent_id=parent_id,
            name=part,
            type=cat_type
        )
        db.add(new_category)
        db.flush()
        
        parent_id = new_category.id
    
    return db.query(NoteCategory).filter(
        NoteCategory.id == parent_id
    ).first()


def extract_filename(path):
    """从路径中提取文件名"""
    return path.split("/")[-1] if path else ""


@router.put("/categories/{category_id}", response_model=CommonResponse[dict])
async def update_category(
    category_id: str,
    request: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新分类/文件夹（重命名、移动、排序）
    """
    try:
        # 检查分类是否存在
        category = db.query(NoteCategory).filter(
            NoteCategory.id == category_id,
            NoteCategory.user_id == current_user.id
        ).first()
        if not category:
            return ErrorResponse.not_found("分类不存在")
        
        # 检查目标父分类是否存在（如果有）
        if request.parent_id is not None and request.parent_id != category.parent_id:
            if request.parent_id:
                parent = db.query(NoteCategory).filter(
                    NoteCategory.id == request.parent_id,
                    NoteCategory.user_id == current_user.id
                ).first()
                if not parent:
                    return ErrorResponse.not_found("目标父分类不存在")
                
                # 检查是否会形成循环引用
                if await is_circular_reference(db, category_id, request.parent_id):
                    return ErrorResponse.bad_request("不能移动到自己的子分类下")
        
        # 更新分类
        if request.name is not None:
            category.name = request.name
        if request.parent_id is not None:
            category.parent_id = request.parent_id
        if request.sort_order is not None:
            category.sort_order = request.sort_order
        
        db.commit()
        db.refresh(category)
        
        return SuccessResponse.build(
            data={
                "id": str(category.id),
                "name": category.name,
                "parent_id": category.parent_id
            },
            message="分类更新成功"
        )
    except Exception as e:
        logger.error(f"更新分类失败: {e}")
        return ErrorResponse.internal_error("更新分类失败")


async def is_circular_reference(db, category_id, target_parent_id):
    """检查是否会形成循环引用"""
    visited = set()
    current_id = target_parent_id
    
    while current_id:
        if current_id == category_id:
            return True
        if current_id in visited:
            return False
        visited.add(current_id)
        
        category = db.query(NoteCategory).filter(
            NoteCategory.id == current_id
        ).first()
        if not category:
            break
        current_id = category.parent_id
    
    return False


@router.put("/notes/{note_id}", response_model=CommonResponse[dict])
async def update_note(
    note_id: str,
    request: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新笔记（重命名、移动分类）
    """
    try:
        # 检查笔记是否存在
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == current_user.id
        ).first()
        if not note:
            return ErrorResponse.not_found("笔记不存在")
        
        # 检查目标分类是否存在（如果有）
        if request.category_id is not None and request.category_id != note.category_id:
            if request.category_id:
                category = db.query(NoteCategory).filter(
                    NoteCategory.id == request.category_id,
                    NoteCategory.user_id == current_user.id
                ).first()
                if not category:
                    return ErrorResponse.not_found("目标分类不存在")
        
        # 更新笔记
        if request.title is not None:
            note.title = request.title
        if request.category_id is not None:
            note.category_id = request.category_id
        
        db.commit()
        db.refresh(note)
        
        return SuccessResponse.build(
            data={
                "id": str(note.id),
                "title": note.title,
                "category_id": note.category_id
            },
            message="笔记更新成功"
        )
    except Exception as e:
        logger.error(f"更新笔记失败: {e}")
        return ErrorResponse.internal_error("更新笔记失败")


@router.delete("/notes/{note_id}", response_model=CommonResponse[dict])
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除笔记
    """
    try:
        # 检查笔记是否存在
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == current_user.id
        ).first()
        if not note:
            return ErrorResponse.not_found("笔记不存在")
        
        # 软删除笔记
        from datetime import datetime
        note.deleted_at = datetime.utcnow()
        db.commit()
        
        return SuccessResponse.build(
            data={"message": "笔记删除成功"},
            message="笔记删除成功"
        )
    except Exception as e:
        logger.error(f"删除笔记失败: {e}")
        return ErrorResponse.internal_error("删除笔记失败")


@router.put("/articles/{article_id}", response_model=CommonResponse[dict])
async def update_article(
    article_id: str,
    request: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新文章（重命名、移动分类）
    """
    try:
        # 检查文章是否存在
        article = db.query(Article).filter(
            Article.id == article_id,
            Article.user_id == current_user.id
        ).first()
        if not article:
            return ErrorResponse.not_found("文章不存在")
        
        # 检查目标分类是否存在（如果有）
        if request.category_id is not None and request.category_id != article.category_id:
            if request.category_id:
                category = db.query(NoteCategory).filter(
                    NoteCategory.id == request.category_id,
                    NoteCategory.user_id == current_user.id
                ).first()
                if not category:
                    return ErrorResponse.not_found("目标分类不存在")
        
        # 更新文章
        if request.title is not None:
            article.title = request.title
        if request.category_id is not None:
            article.category_id = request.category_id
        
        db.commit()
        db.refresh(article)
        
        return SuccessResponse.build(
            data={
                "id": str(article.id),
                "title": article.title,
                "category_id": article.category_id
            },
            message="文章更新成功"
        )
    except Exception as e:
        logger.error(f"更新文章失败: {e}")
        return ErrorResponse.internal_error("更新文章失败")


@router.delete("/articles/{article_id}", response_model=CommonResponse[dict])
async def delete_article(
    article_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除文章
    """
    try:
        # 检查文章是否存在
        article = db.query(Article).filter(
            Article.id == article_id,
            Article.user_id == current_user.id
        ).first()
        if not article:
            return ErrorResponse.not_found("文章不存在")
        
        # 软删除文章
        from datetime import datetime
        article.deleted_at = datetime.utcnow()
        db.commit()
        
        return SuccessResponse.build(
            data={"message": "文章删除成功"},
            message="文章删除成功"
        )
    except Exception as e:
        logger.error(f"删除文章失败: {e}")
        return ErrorResponse.internal_error("删除文章失败")


@router.get("/notes/{note_id}", response_model=CommonResponse[dict])
async def get_note_detail(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取笔记详情
    """
    try:
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == current_user.id,
            Note.deleted_at.is_(None)
        ).first()
        
        if not note:
            return ErrorResponse.not_found("笔记不存在")
        
        return SuccessResponse.build(
            data={
                "id": str(note.id),
                "title": note.title,
                "content": note.content,
                "category_id": note.category_id,
                "word_count": note.word_count,
                "source_type": note.source_type,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None
            },
            message="获取笔记详情成功"
        )
    except Exception as e:
        logger.error(f"获取笔记详情失败: {e}")
        return ErrorResponse.internal_error("获取笔记详情失败")


@router.post("/notes", response_model=CommonResponse[dict])
async def create_note(
    request: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建笔记
    """
    try:
        # 检查分类是否存在
        category = None
        if request.category_id:
            category = db.query(NoteCategory).filter(
                NoteCategory.id == request.category_id,
                NoteCategory.user_id == current_user.id
            ).first()
            if not category:
                return ErrorResponse.not_found("分类不存在")
        
        # 创建笔记
        note = Note(
            user_id=current_user.id,
            category_id=request.category_id,
            title=request.title,
            content=request.content,
            source_type="markdown",
            word_count=len(request.content),
            status="active"
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        
        return SuccessResponse.build(
            data={
                "id": str(note.id),
                "title": note.title,
                "category_id": note.category_id
            },
            message="创建笔记成功"
        )
    except Exception as e:
        logger.error(f"创建笔记失败: {e}")
        return ErrorResponse.internal_error("创建笔记失败")


@router.get("/articles/{article_id}", response_model=CommonResponse[dict])
async def get_article_detail(
    article_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取文章详情
    """
    try:
        article = db.query(Article).filter(
            Article.id == article_id,
            Article.user_id == current_user.id,
            Article.deleted_at.is_(None)
        ).first()
        
        if not article:
            return ErrorResponse.not_found("文章不存在")
        
        return SuccessResponse.build(
            data={
                "id": str(article.id),
                "title": article.title,
                "content": article.content,
                "category_id": article.category_id,
                "style_id": article.style_id,
                "word_count": article.word_count,
                "status": article.status,
                "quality_score": article.quality_score,
                "originality_score": article.originality_score,
                "fluency_score": article.fluency_score,
                "style_match_score": article.style_match_score,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None
            },
            message="获取文章详情成功"
        )
    except Exception as e:
        logger.error(f"获取文章详情失败: {e}")
        return ErrorResponse.internal_error("获取文章详情失败")


@router.post("/articles", response_model=CommonResponse[dict])
async def create_article(
    request: ArticleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建文章
    """
    try:
        # 检查分类是否存在
        category = None
        if request.category_id:
            category = db.query(NoteCategory).filter(
                NoteCategory.id == request.category_id,
                NoteCategory.user_id == current_user.id
            ).first()
            if not category:
                return ErrorResponse.not_found("分类不存在")
        
        # 创建文章
        article = Article(
            user_id=current_user.id,
            category_id=request.category_id,
            style_id=request.style_id,
            title=request.title,
            content=request.content or "",
            word_count=len(request.content) if request.content else 0,
            status="draft"
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        return SuccessResponse.build(
            data={
                "id": str(article.id),
                "title": article.title,
                "category_id": article.category_id
            },
            message="创建文章成功"
        )
    except Exception as e:
        logger.error(f"创建文章失败: {e}")
        return ErrorResponse.internal_error("创建文章失败")


@router.post("/file-tree/move", response_model=CommonResponse[dict])
async def move_node(
    request: MoveNodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    通用移动节点接口
    """
    try:
        node_id = request.node_id
        node_type = request.node_type
        target_parent_id = request.target_parent_id
        
        if node_type == "category":
            # 移动分类
            category = db.query(NoteCategory).filter(
                NoteCategory.id == node_id,
                NoteCategory.user_id == current_user.id
            ).first()
            if not category:
                return ErrorResponse.not_found("分类不存在")
            
            # 检查目标父分类是否存在
            if target_parent_id:
                parent = db.query(NoteCategory).filter(
                    NoteCategory.id == target_parent_id,
                    NoteCategory.user_id == current_user.id
                ).first()
                if not parent:
                    return ErrorResponse.not_found("目标父分类不存在")
                
                # 检查循环引用
                if await is_circular_reference(db, node_id, target_parent_id):
                    return ErrorResponse.bad_request("不能移动到自己的子分类下")
            
            category.parent_id = target_parent_id
            db.commit()
            
        elif node_type == "note":
            # 移动笔记
            note = db.query(Note).filter(
                Note.id == node_id,
                Note.user_id == current_user.id
            ).first()
            if not note:
                return ErrorResponse.not_found("笔记不存在")
            
            # 检查目标分类是否存在
            if target_parent_id:
                category = db.query(NoteCategory).filter(
                    NoteCategory.id == target_parent_id,
                    NoteCategory.user_id == current_user.id
                ).first()
                if not category:
                    return ErrorResponse.not_found("目标分类不存在")
            
            note.category_id = target_parent_id
            db.commit()
            
        elif node_type == "article":
            # 移动文章
            article = db.query(Article).filter(
                Article.id == node_id,
                Article.user_id == current_user.id
            ).first()
            if not article:
                return ErrorResponse.not_found("文章不存在")
            
            # 检查目标分类是否存在
            if target_parent_id:
                category = db.query(NoteCategory).filter(
                    NoteCategory.id == target_parent_id,
                    NoteCategory.user_id == current_user.id
                ).first()
                if not category:
                    return ErrorResponse.not_found("目标分类不存在")
            
            article.category_id = target_parent_id
            db.commit()
            
        else:
            return ErrorResponse.bad_request("不支持的节点类型")
        
        return SuccessResponse.build(
            data={"message": "节点移动成功"},
            message="节点移动成功"
        )
    except Exception as e:
        logger.error(f"移动节点失败: {e}")
        return ErrorResponse.internal_error("移动节点失败")
