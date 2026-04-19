"""
风格管理 API

通过 Gateway 层和 StyleManager 实现真实的风格分析和学习
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session
from eleven_blog_tunner.api.routes.common import (
    CommonResponse, SuccessResponse, ErrorResponse, ResponseCode
)
from eleven_blog_tunner.core.config import get_settings
from eleven_blog_tunner.rag.style_manager import StyleManager
from eleven_blog_tunner.common.models import User, Note, Article, get_db
from eleven_blog_tunner.common.auth import get_current_user

router = APIRouter(prefix="/styles", tags=["styles"])


class StyleExtractRequest(BaseModel):
    """风格提取请求"""
    text: str
    style_name: str
    metadata: Optional[Dict[str, Any]] = None
    use_statistical: bool = True
    use_semantic: bool = True
    use_embedding: bool = True


class NoteStyleExtractRequest(BaseModel):
    """从笔记提取风格请求"""
    note_id: str
    style_name: str
    use_statistical: bool = True
    use_semantic: bool = True
    use_embedding: bool = True


class ArticleStyleExtractRequest(BaseModel):
    """从文章提取风格请求"""
    article_id: str
    style_name: str
    use_statistical: bool = True
    use_semantic: bool = True
    use_embedding: bool = True


class StatisticalFeaturesResponse(BaseModel):
    """统计特征响应"""
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


class SemanticFeaturesResponse(BaseModel):
    """语义特征响应"""
    language_style: str
    tone: str
    vocabulary_level: str
    sentence_rhythm: str
    rhetoric_devices: List[str]
    emotional_tendency: str
    perspective: str
    logic_structure: str
    unique_habits: List[str]
    target_audience: str
    domain_characteristics: str
    writing_quirks: str


class FeaturesResponse(BaseModel):
    """完整特征响应"""
    statistical: Optional[StatisticalFeaturesResponse] = None
    semantic: Optional[SemanticFeaturesResponse] = None


class AnalysisModeResponse(BaseModel):
    """分析模式响应"""
    use_statistical: bool
    use_semantic: bool
    use_embedding: bool


class StyleResponseData(BaseModel):
    """风格响应数据"""
    name: str
    features: FeaturesResponse
    vector: List[float]
    metadata: Dict[str, Any]
    analysis_mode: AnalysisModeResponse


@router.post("/learn", response_model=CommonResponse[StyleResponseData])
async def learn_style(request: StyleExtractRequest):
    """
    从文本学习风格 - 混合模式

    - **text**: 文本内容（从笔记中提取的写作样本）
    - **style_name**: 风格名称
    - **metadata**: 可选的元数据
    - **use_statistical**: 是否使用规则统计特征（默认true）
    - **use_semantic**: 是否使用LLM语义分析（默认true）
    - **use_embedding**: 是否使用Embedding向量（默认true）
    """
    try:
        if not request.text or not request.text.strip():
            return ErrorResponse.bad_request("文本内容不能为空")
        
        style_manager = StyleManager()
        
        style_data = await style_manager.extract_style(
            text=request.text,
            style_name=request.style_name,
            metadata=request.metadata or {},
            use_statistical=request.use_statistical,
            use_semantic=request.use_semantic,
            use_embedding=request.use_embedding
        )
        
        # 构建响应数据
        features = style_data['features']
        
        # 统计特征
        statistical_response = None
        if features.get('statistical'):
            stat = features['statistical']
            statistical_response = StatisticalFeaturesResponse(
                vocabulary_diversity=stat.get('vocabulary_diversity', 0.0),
                average_word_length=stat.get('average_word_length', 0.0),
                unique_words_ratio=stat.get('unique_words_ratio', 0.0),
                average_sentence_length=stat.get('average_sentence_length', 0.0),
                sentence_complexity=stat.get('sentence_complexity', 0.0),
                punctuation_density=stat.get('punctuation_density', 0.0),
                paragraph_average_length=stat.get('paragraph_average_length', 0.0),
                transition_words_ratio=stat.get('transition_words_ratio', 0.0),
                passive_voice_ratio=stat.get('passive_voice_ratio', 0.0),
                first_person_ratio=stat.get('first_person_ratio', 0.0),
                emoji_usage=stat.get('emoji_usage', 0.0)
            )
        
        # 语义特征
        semantic_response = None
        if features.get('semantic'):
            sem = features['semantic']
            semantic_response = SemanticFeaturesResponse(
                language_style=sem.get('language_style', ''),
                tone=sem.get('tone', ''),
                vocabulary_level=sem.get('vocabulary_level', ''),
                sentence_rhythm=sem.get('sentence_rhythm', ''),
                rhetoric_devices=sem.get('rhetoric_devices', []),
                emotional_tendency=sem.get('emotional_tendency', ''),
                perspective=sem.get('perspective', ''),
                logic_structure=sem.get('logic_structure', ''),
                unique_habits=sem.get('unique_habits', []),
                target_audience=sem.get('target_audience', ''),
                domain_characteristics=sem.get('domain_characteristics', ''),
                writing_quirks=sem.get('writing_quirks', '')
            )
        
        features_response = FeaturesResponse(
            statistical=statistical_response,
            semantic=semantic_response
        )
        
        analysis_mode = AnalysisModeResponse(
            use_statistical=style_data.get('analysis_mode', {}).get('use_statistical', True),
            use_semantic=style_data.get('analysis_mode', {}).get('use_semantic', True),
            use_embedding=style_data.get('analysis_mode', {}).get('use_embedding', True)
        )
        
        data = StyleResponseData(
            name=style_data['name'],
            features=features_response,
            vector=style_data['vector'],
            metadata=style_data.get('metadata', {}),
            analysis_mode=analysis_mode
        )
        
        return SuccessResponse.build(
            data=data,
            message="风格学习成功"
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
        
        if not content_str or not content_str.strip():
            return ErrorResponse.bad_request("文件内容为空")
        
        style_manager = StyleManager()
        
        style_data = await style_manager.extract_style(
            text=content_str,
            style_name=style_name,
            metadata={"source_file": file.filename}
        )
        
        return SuccessResponse.build(
            data={"style_name": style_name},
            message=f"风格 '{style_name}' 学习成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/list", response_model=CommonResponse)
async def list_styles():
    """
    获取风格列表
    """
    try:
        style_manager = StyleManager()
        styles = await style_manager.list_styles()
        
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
        style_manager = StyleManager()
        style_data = await style_manager.load_style(style_name)
        
        features = style_data.get('features', {})
        
        # 构建统计特征响应
        statistical_data = features.get('statistical', {})
        statistical_response = StatisticalFeaturesResponse(
            vocabulary_diversity=statistical_data.get('vocabulary_diversity', 0.0),
            average_word_length=statistical_data.get('average_word_length', 0.0),
            unique_words_ratio=statistical_data.get('unique_words_ratio', 0.0),
            average_sentence_length=statistical_data.get('average_sentence_length', 0.0),
            sentence_complexity=statistical_data.get('sentence_complexity', 0.0),
            punctuation_density=statistical_data.get('punctuation_density', 0.0),
            paragraph_average_length=statistical_data.get('paragraph_average_length', 0.0),
            transition_words_ratio=statistical_data.get('transition_words_ratio', 0.0),
            passive_voice_ratio=statistical_data.get('passive_voice_ratio', 0.0),
            first_person_ratio=statistical_data.get('first_person_ratio', 0.0),
            emoji_usage=statistical_data.get('emoji_usage', 0.0)
        ) if statistical_data else None
        
        # 构建语义特征响应
        semantic_data = features.get('semantic', {})
        semantic_response = SemanticFeaturesResponse(
            language_style=semantic_data.get('language_style', ''),
            tone=semantic_data.get('tone', ''),
            vocabulary_level=semantic_data.get('vocabulary_level', ''),
            sentence_rhythm=semantic_data.get('sentence_rhythm', ''),
            rhetoric_devices=semantic_data.get('rhetoric_devices', []),
            emotional_tendency=semantic_data.get('emotional_tendency', ''),
            perspective=semantic_data.get('perspective', ''),
            logic_structure=semantic_data.get('logic_structure', ''),
            unique_habits=semantic_data.get('unique_habits', []),
            target_audience=semantic_data.get('target_audience', ''),
            domain_characteristics=semantic_data.get('domain_characteristics', ''),
            writing_quirks=semantic_data.get('writing_quirks', '')
        ) if semantic_data else None
        
        # 构建完整特征响应
        features_response = FeaturesResponse(
            statistical=statistical_response,
            semantic=semantic_response
        )
        
        # 构建分析模式响应
        analysis_mode = style_data.get('analysis_mode', {
            'use_statistical': True,
            'use_semantic': True,
            'use_embedding': True
        })
        analysis_mode_response = AnalysisModeResponse(
            use_statistical=analysis_mode.get('use_statistical', True),
            use_semantic=analysis_mode.get('use_semantic', True),
            use_embedding=analysis_mode.get('use_embedding', True)
        )
        
        data = StyleResponseData(
            name=style_data['name'],
            features=features_response,
            vector=style_data.get('vector', []),
            metadata=style_data.get('metadata', {}),
            analysis_mode=analysis_mode_response
        )
        
        return SuccessResponse.build(
            data=data,
            message="获取风格详情成功"
        )
    except FileNotFoundError:
        return ErrorResponse.not_found(f"风格 '{style_name}' 不存在")
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.delete("/{style_name}", response_model=CommonResponse)
async def delete_style(style_name: str):
    """
    删除指定风格
    """
    try:
        style_manager = StyleManager()
        success = await style_manager.delete_style(style_name)
        
        if not success:
            return ErrorResponse.not_found(f"风格 '{style_name}' 不存在")
        
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
        style_manager = StyleManager()
        references = await style_manager.get_style_references(style_name, top_k)
        
        return SuccessResponse.build(
            data={"references": references},
            message="获取风格参考段落成功"
        )
    except FileNotFoundError:
        return ErrorResponse.not_found(f"风格 '{style_name}' 不存在")
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
        
        if not content_str or not content_str.strip():
            return ErrorResponse.bad_request("文件内容为空")
        
        style_manager = StyleManager()
        result = await style_manager.preview_style(content_str, style_name)
        
        return SuccessResponse.build(
            data=result,
            message="风格预览成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/{style_name}/add-sample", response_model=CommonResponse)
async def add_style_sample(
    style_name: str,
    text: str
):
    """
    添加风格样本

    - **style_name**: 风格名称
    - **text**: 样本文本
    """
    try:
        if not text or not text.strip():
            return ErrorResponse.bad_request("文本内容不能为空")
        
        style_manager = StyleManager()
        style_data = await style_manager.add_style_sample(style_name, text)
        
        return SuccessResponse.build(
            data={"sample_count": style_data.get('sample_count', 1)},
            message="样本添加成功"
        )
    except FileNotFoundError:
        return ErrorResponse.not_found(f"风格 '{style_name}' 不存在")
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.get("/{style_name1}/compare/{style_name2}", response_model=CommonResponse)
async def compare_styles(style_name1: str, style_name2: str):
    """
    比较两种风格的相似度

    - **style_name1**: 第一种风格名称
    - **style_name2**: 第二种风格名称
    """
    try:
        style_manager = StyleManager()
        similarity = await style_manager.compare_styles(style_name1, style_name2)
        
        return SuccessResponse.build(
            data={"similarity": similarity},
            message="风格比较成功"
        )
    except FileNotFoundError:
        return ErrorResponse.not_found("其中一个风格不存在")
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/extract-from-note", response_model=CommonResponse[StyleResponseData])
async def extract_style_from_note(
    request: NoteStyleExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从指定笔记提取并学习风格 - 混合模式

    - **note_id**: 笔记 ID
    - **style_name**: 风格名称
    - **use_statistical**: 是否使用规则统计特征（默认true）
    - **use_semantic**: 是否使用LLM语义分析（默认true）
    - **use_embedding**: 是否使用Embedding向量（默认true）
    """
    try:
        # 处理 ID 前缀，前端可能传递 "note-uuid" 格式
        note_id = request.note_id
        if note_id.startswith('note-'):
            note_id = note_id[5:]
        
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.user_id == current_user.id,
            Note.deleted_at.is_(None)
        ).first()
        
        if not note:
            return ErrorResponse.not_found("笔记不存在或不属于当前用户")
        
        if not note.content or not note.content.strip():
            return ErrorResponse.bad_request("笔记内容为空")
        
        style_manager = StyleManager()
        style_data = await style_manager.extract_style(
            text=note.content,
            style_name=request.style_name,
            metadata={"source": "note", "note_id": str(note.id), "note_title": note.title},
            use_statistical=request.use_statistical,
            use_semantic=request.use_semantic,
            use_embedding=request.use_embedding
        )
        
        # 构建响应数据
        features = style_data['features']
        
        statistical_response = None
        if features.get('statistical'):
            stat = features['statistical']
            statistical_response = StatisticalFeaturesResponse(
                vocabulary_diversity=stat.get('vocabulary_diversity', 0.0),
                average_word_length=stat.get('average_word_length', 0.0),
                unique_words_ratio=stat.get('unique_words_ratio', 0.0),
                average_sentence_length=stat.get('average_sentence_length', 0.0),
                sentence_complexity=stat.get('sentence_complexity', 0.0),
                punctuation_density=stat.get('punctuation_density', 0.0),
                paragraph_average_length=stat.get('paragraph_average_length', 0.0),
                transition_words_ratio=stat.get('transition_words_ratio', 0.0),
                passive_voice_ratio=stat.get('passive_voice_ratio', 0.0),
                first_person_ratio=stat.get('first_person_ratio', 0.0),
                emoji_usage=stat.get('emoji_usage', 0.0)
            )
        
        semantic_response = None
        if features.get('semantic'):
            sem = features['semantic']
            semantic_response = SemanticFeaturesResponse(
                language_style=sem.get('language_style', ''),
                tone=sem.get('tone', ''),
                vocabulary_level=sem.get('vocabulary_level', ''),
                sentence_rhythm=sem.get('sentence_rhythm', ''),
                rhetoric_devices=sem.get('rhetoric_devices', []),
                emotional_tendency=sem.get('emotional_tendency', ''),
                perspective=sem.get('perspective', ''),
                logic_structure=sem.get('logic_structure', ''),
                unique_habits=sem.get('unique_habits', []),
                target_audience=sem.get('target_audience', ''),
                domain_characteristics=sem.get('domain_characteristics', ''),
                writing_quirks=sem.get('writing_quirks', '')
            )
        
        features_response = FeaturesResponse(
            statistical=statistical_response,
            semantic=semantic_response
        )
        
        analysis_mode = AnalysisModeResponse(
            use_statistical=style_data.get('analysis_mode', {}).get('use_statistical', True),
            use_semantic=style_data.get('analysis_mode', {}).get('use_semantic', True),
            use_embedding=style_data.get('analysis_mode', {}).get('use_embedding', True)
        )
        
        data = StyleResponseData(
            name=style_data['name'],
            features=features_response,
            vector=style_data['vector'],
            metadata=style_data.get('metadata', {}),
            analysis_mode=analysis_mode
        )
        
        return SuccessResponse.build(
            data=data,
            message="从笔记提取风格成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))


@router.post("/extract-from-article", response_model=CommonResponse[StyleResponseData])
async def extract_style_from_article(
    request: ArticleStyleExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从指定文章提取并学习风格 - 混合模式

    - **article_id**: 文章 ID
    - **style_name**: 风格名称
    - **use_statistical**: 是否使用规则统计特征（默认true）
    - **use_semantic**: 是否使用LLM语义分析（默认true）
    - **use_embedding**: 是否使用Embedding向量（默认true）
    """
    try:
        # 处理 ID 前缀，前端可能传递 "article-uuid" 格式
        article_id = request.article_id
        if article_id.startswith('article-'):
            article_id = article_id[8:]
        
        article = db.query(Article).filter(
            Article.id == article_id,
            Article.user_id == current_user.id,
            Article.deleted_at.is_(None)
        ).first()
        
        if not article:
            return ErrorResponse.not_found("文章不存在或不属于当前用户")
        
        if not article.content or not article.content.strip():
            return ErrorResponse.bad_request("文章内容为空")
        
        style_manager = StyleManager()
        style_data = await style_manager.extract_style(
            text=article.content,
            style_name=request.style_name,
            metadata={"source": "article", "article_id": str(article.id), "article_title": article.title},
            use_statistical=request.use_statistical,
            use_semantic=request.use_semantic,
            use_embedding=request.use_embedding
        )
        
        # 构建响应数据
        features = style_data['features']
        
        statistical_response = None
        if features.get('statistical'):
            stat = features['statistical']
            statistical_response = StatisticalFeaturesResponse(
                vocabulary_diversity=stat.get('vocabulary_diversity', 0.0),
                average_word_length=stat.get('average_word_length', 0.0),
                unique_words_ratio=stat.get('unique_words_ratio', 0.0),
                average_sentence_length=stat.get('average_sentence_length', 0.0),
                sentence_complexity=stat.get('sentence_complexity', 0.0),
                punctuation_density=stat.get('punctuation_density', 0.0),
                paragraph_average_length=stat.get('paragraph_average_length', 0.0),
                transition_words_ratio=stat.get('transition_words_ratio', 0.0),
                passive_voice_ratio=stat.get('passive_voice_ratio', 0.0),
                first_person_ratio=stat.get('first_person_ratio', 0.0),
                emoji_usage=stat.get('emoji_usage', 0.0)
            )
        
        semantic_response = None
        if features.get('semantic'):
            sem = features['semantic']
            semantic_response = SemanticFeaturesResponse(
                language_style=sem.get('language_style', ''),
                tone=sem.get('tone', ''),
                vocabulary_level=sem.get('vocabulary_level', ''),
                sentence_rhythm=sem.get('sentence_rhythm', ''),
                rhetoric_devices=sem.get('rhetoric_devices', []),
                emotional_tendency=sem.get('emotional_tendency', ''),
                perspective=sem.get('perspective', ''),
                logic_structure=sem.get('logic_structure', ''),
                unique_habits=sem.get('unique_habits', []),
                target_audience=sem.get('target_audience', ''),
                domain_characteristics=sem.get('domain_characteristics', ''),
                writing_quirks=sem.get('writing_quirks', '')
            )
        
        features_response = FeaturesResponse(
            statistical=statistical_response,
            semantic=semantic_response
        )
        
        analysis_mode = AnalysisModeResponse(
            use_statistical=style_data.get('analysis_mode', {}).get('use_statistical', True),
            use_semantic=style_data.get('analysis_mode', {}).get('use_semantic', True),
            use_embedding=style_data.get('analysis_mode', {}).get('use_embedding', True)
        )
        
        data = StyleResponseData(
            name=style_data['name'],
            features=features_response,
            vector=style_data['vector'],
            metadata=style_data.get('metadata', {}),
            analysis_mode=analysis_mode
        )
        
        return SuccessResponse.build(
            data=data,
            message="从文章提取风格成功"
        )
    except Exception as e:
        return ErrorResponse.internal_error(message=str(e))
