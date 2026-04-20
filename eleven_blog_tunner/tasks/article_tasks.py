"""
文章生成相关 Celery 任务
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from eleven_blog_tunner.tasks.celery_app import celery_app
from eleven_blog_tunner.gateway.task_manager import TaskManager
from eleven_blog_tunner.gateway.integration import Integration
from eleven_blog_tunner.common.models import Article, get_db_session
from eleven_blog_tunner.agents import get_protocol
from eleven_blog_tunner.agents.base_agent import AgentContext
from eleven_blog_tunner.utils.logger import logger_instance as logger

# 创建任务管理器和集成模块实例
task_manager = TaskManager()
integration = Integration()


@celery_app.task(bind=True, max_retries=3)
def generate_article_task(
    self,
    article_id: str,
    topic: str,
    style_name: Optional[str] = None,
    outline: Optional[list] = None,
    target_length: int = 1000,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    异步生成文章任务
    
    Args:
        article_id: 文章ID
        topic: 文章主题
        style_name: 风格名称
        outline: 文章大纲
        target_length: 目标字数
        user_id: 用户ID
        
    Returns:
        任务执行结果
    """
    task_id = self.request.id
    logger.info(f"[Celery] 开始执行文章生成任务: article_id={article_id}, task_id={task_id}")
    
    # 更新任务状态为开始
    self.update_state(
        state='PROGRESS',
        meta={
            'progress': 10,
            'step': '初始化文章生成任务',
            'article_id': article_id
        }
    )
    
    try:
        # 构建输入数据
        input_data = json.dumps({
            'article_id': article_id,
            'topic': topic,
            'style_name': style_name,
            'outline': outline,
            'target_length': target_length,
            'user_id': user_id
        }, ensure_ascii=False)
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 20,
                'step': '调用 BossAgent 执行任务链',
                'article_id': article_id
            }
        )
        
        # 使用 Integration 执行任务链（包含 BossAgent 调用）
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 执行任务链
            result = loop.run_until_complete(
                integration.execute_task_chain(
                    task_type='article_generation',
                    input_data=input_data,
                    task_id=task_id
                )
            )
        finally:
            loop.close()
        
        # 检查执行结果
        if not result.get('success'):
            error_msg = result.get('error', '任务执行失败')
            logger.error(f"[Celery] 文章生成失败: {error_msg}")
            
            # 更新数据库状态为失败
            _update_article_status(article_id, 'failed', error=error_msg)
            
            # 重试逻辑
            if self.request.retries < self.max_retries:
                logger.info(f"[Celery] 任务将在60秒后重试，当前重试次数: {self.request.retries}")
                raise self.retry(countdown=60)
            
            return {
                'success': False,
                'error': error_msg,
                'article_id': article_id,
                'task_id': task_id
            }
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 80,
                'step': '更新文章内容和状态',
                'article_id': article_id
            }
        )
        
        # 提取生成的文章内容
        generated_content = result.get('result', '')
        if isinstance(generated_content, dict):
            generated_content = generated_content.get('content', '')
        
        # 更新数据库中的文章内容
        _update_article_content(
            article_id=article_id,
            content=generated_content,
            status='draft',
            word_count=len(generated_content)
        )
        
        # 更新进度为完成
        self.update_state(
            state='SUCCESS',
            meta={
                'progress': 100,
                'step': '文章生成完成',
                'article_id': article_id
            }
        )
        
        logger.info(f"[Celery] 文章生成完成: article_id={article_id}")
        
        return {
            'success': True,
            'article_id': article_id,
            'task_id': task_id,
            'content_length': len(generated_content),
            'message': '文章生成成功'
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"[Celery] 文章生成任务超时: article_id={article_id}")
        _update_article_status(article_id, 'failed', error='任务执行超时')
        return {
            'success': False,
            'error': '任务执行超时',
            'article_id': article_id,
            'task_id': task_id
        }
        
    except Exception as e:
        logger.exception(f"[Celery] 文章生成任务异常: {e}")
        
        # 更新数据库状态为失败
        _update_article_status(article_id, 'failed', error=str(e))
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"[Celery] 任务将在60秒后重试，当前重试次数: {self.request.retries}")
            raise self.retry(countdown=60)
        
        return {
            'success': False,
            'error': str(e),
            'article_id': article_id,
            'task_id': task_id
        }


@celery_app.task(bind=True)
def process_gateway_task(self, task_id: str, task_type: str, input_data: str, user_id: str) -> Dict[str, Any]:
    """
    处理 Gateway 任务
    
    Args:
        task_id: 任务ID
        task_type: 任务类型
        input_data: 输入数据
        user_id: 用户ID
        
    Returns:
        任务执行结果
    """
    logger.info(f"[Celery] 处理 Gateway 任务: task_id={task_id}, type={task_type}")
    
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 使用 TaskManager 处理任务
            loop.run_until_complete(task_manager.start())
            
            # 创建任务
            created_task_id = loop.run_until_complete(
                task_manager.create_task(task_type, input_data, user_id)
            )
            
            # 等待任务完成（轮询检查）
            import time
            max_wait = 3600  # 最大等待1小时
            wait_interval = 5  # 每5秒检查一次
            waited = 0
            
            while waited < max_wait:
                status = loop.run_until_complete(task_manager.get_task_status(created_task_id))
                
                if status.get('status') == 'completed':
                    result = loop.run_until_complete(task_manager.get_task_result(created_task_id))
                    return {
                        'success': True,
                        'task_id': task_id,
                        'result': result
                    }
                elif status.get('status') == 'failed':
                    return {
                        'success': False,
                        'task_id': task_id,
                        'error': status.get('error', '任务执行失败')
                    }
                
                time.sleep(wait_interval)
                waited += wait_interval
                
                # 更新进度
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': min(90, int(waited / max_wait * 100)),
                        'step': f'任务执行中，已等待 {waited} 秒'
                    }
                )
            
            return {
                'success': False,
                'task_id': task_id,
                'error': '任务等待超时'
            }
            
        finally:
            loop.run_until_complete(task_manager.stop())
            loop.close()
            
    except Exception as e:
        logger.exception(f"[Celery] Gateway 任务处理异常: {e}")
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e)
        }


def _update_article_status(article_id: str, status: str, error: Optional[str] = None):
    """更新文章状态"""
    try:
        db = get_db_session()
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if article:
                article.status = status
                article.updated_at = datetime.utcnow()
                if error:
                    # 可以将错误信息存储在 meta_data 中
                    article.meta_data = article.meta_data or {}
                    article.meta_data['error'] = error
                    article.meta_data['failed_at'] = datetime.utcnow().isoformat()
                db.commit()
                logger.info(f"[Celery] 更新文章状态: article_id={article_id}, status={status}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[Celery] 更新文章状态失败: {e}")


def _update_article_content(
    article_id: str,
    content: str,
    status: str = 'draft',
    word_count: int = 0
):
    """更新文章内容"""
    try:
        db = get_db_session()
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if article:
                article.content = content
                article.status = status
                article.word_count = word_count
                article.updated_at = datetime.utcnow()
                db.commit()
                logger.info(
                    f"[Celery] 更新文章内容: article_id={article_id}, "
                    f"status={status}, word_count={word_count}"
                )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[Celery] 更新文章内容失败: {e}")
