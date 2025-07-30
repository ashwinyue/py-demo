"""日志工具模块"""

import logging
import sys
from typing import Optional
from pathlib import Path

from ..config.base import get_config


def setup_logger(
    name: str,
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """设置日志记录器"""
    config = get_config()
    
    # 获取日志级别
    if level is None:
        level = getattr(config, 'LOG_LEVEL', 'INFO')
    
    # 获取日志格式
    if format_string is None:
        format_string = getattr(
            config,
            'LOG_FORMAT',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(format_string)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_service_logger(service_name: str) -> logging.Logger:
    """获取服务专用的日志记录器"""
    config = get_config()
    log_dir = Path(config.PROJECT_ROOT) / "logs"
    log_file = log_dir / f"{service_name}.log"
    
    return setup_logger(
        name=service_name,
        log_file=log_file
    )