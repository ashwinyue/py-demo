"""基础配置模块"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class BaseConfig:
    """基础配置类"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///miniblog.db')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'miniblog')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'miniblog123')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'miniblog')
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    
    # 服务配置
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'miniblog')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 跨域配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        if cls.DATABASE_URL.startswith('mysql'):
            return cls.DATABASE_URL
        return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
    
    @classmethod
    def get_redis_url(cls) -> str:
        """获取Redis连接URL"""
        if cls.REDIS_URL.startswith('redis'):
            return cls.REDIS_URL
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境使用不同的Redis数据库
    REDIS_DB = 0


class TestingConfig(BaseConfig):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    
    # 测试环境使用内存数据库
    DATABASE_URL = 'sqlite:///:memory:'
    REDIS_DB = 1


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境必须设置的配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    def __init__(self):
        if not self.SECRET_KEY:
            raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
        if not self.JWT_SECRET_KEY:
            raise ValueError("生产环境必须设置 JWT_SECRET_KEY 环境变量")


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env: Optional[str] = None) -> BaseConfig:
    """获取配置对象"""
    env = env or os.getenv('FLASK_ENV', 'development')
    config_class = config_map.get(env, config_map['default'])
    return config_class()