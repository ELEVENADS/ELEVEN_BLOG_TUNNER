"""
Celery 任务模块

负责异步执行文章生成等耗时任务
"""
from eleven_blog_tunner.tasks.celery_app import celery_app
from eleven_blog_tunner.tasks.article_tasks import generate_article_task

__all__ = ['celery_app', 'generate_article_task']
