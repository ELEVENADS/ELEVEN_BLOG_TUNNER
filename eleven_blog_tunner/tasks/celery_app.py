"""
Celery 应用配置
"""
import os
from celery import Celery
from eleven_blog_tunner.core.config import get_settings

settings = get_settings()

# 创建 Celery 应用
celery_app = Celery(
    'eleven_blog_tunner',
    broker=settings.celery_broker_url or 'redis://localhost:6379/0',
    backend=settings.celery_result_backend or 'redis://localhost:6379/0',
    include=['eleven_blog_tunner.tasks.article_tasks']
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务执行设置
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3300,  # 55分钟软超时
    
    # 结果存储设置
    result_expires=3600 * 24 * 7,  # 结果保留7天
    result_extended=True,
    
    # 并发设置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 重试设置
    task_default_retry_delay=60,  # 默认60秒后重试
    task_max_retries=3,  # 最大重试3次
)

# 自动发现任务
celery_app.autodiscover_tasks()
