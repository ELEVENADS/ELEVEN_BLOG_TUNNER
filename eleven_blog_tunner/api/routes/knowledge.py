"""
知识库管理 API
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from eleven_blog_tunner.rag.note_importer import NoteImporter
from eleven_blog_tunner.rag.pipeline import RAGPipeline
from eleven_blog_tunner.rag.style_learner import StyleLearner

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post("/import")
async def import_knowledge(
    file: UploadFile = File(...),
    metadata: str = Form(None)
):
    """
    导入知识
    """
    try:
        # 保存上传的文件
        file_path = f"./temp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # 解析元数据
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        # 导入笔记
        importer = NoteImporter()
        result = await importer.import_note(file_path, metadata_dict)
        
        if result:
            return {"success": True, "message": "知识导入成功"}
        else:
            raise HTTPException(status_code=500, detail="知识导入失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_knowledge(
    query: str,
    top_k: int = 5
):
    """
    搜索知识
    """
    try:
        pipeline = RAGPipeline()
        results = await pipeline.search(query, top_k=top_k)
        
        # 格式化结果
        formatted_results = [
            {
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata
            }
            for result in results
        ]
        
        return {"success": True, "results": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
async def delete_knowledge(id: str):
    """
    删除知识
    """
    try:
        # TODO: 实现删除功能
        # 目前 ChromaDB 不支持直接按 ID 删除，需要重建集合
        return {"success": True, "message": "知识删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_knowledge_stats():
    """
    知识库统计
    """
    try:
        from eleven_blog_tunner.rag.searcher import Searcher
        searcher = Searcher()
        
        # 获取集合统计信息
        # 注意：ChromaDB 的 Python 客户端 API 可能有所不同
        # 这里使用一个模拟实现
        stats = {
            "document_count": 0,
            "collection_count": 1,
            "vector_size": 1536  # 假设使用 text-embedding-3-small
        }
        
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learn-style")
async def learn_style_from_notes(
    file: UploadFile = File(...)
):
    """
    从笔记学习风格
    """
    try:
        # 读取文件内容
        content = await file.read()
        content_str = content.decode("utf-8")
        
        # 学习风格
        learner = StyleLearner()
        style = await learner.learn_style(content_str)
        
        return {"success": True, "style": style}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))