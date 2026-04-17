from loguru import logger
import sys
import os
from typing import Optional
from eleven_blog_tunner.core.config import get_project_root

class Logger:
    _instance: Optional['Logger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self):
        log_dir = os.path.join(get_project_root(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logger.remove()
        
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        logger.add(
            os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log"),
            rotation="00:00",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
        
        logger.add(
            os.path.join(log_dir, "error_{time:YYYY-MM-DD}.log"),
            rotation="00:00",
            retention="14 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
    
    def get_logger(self):
        return logger

logger_instance = Logger().get_logger()
