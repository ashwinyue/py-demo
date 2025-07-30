from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "Blog Service"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "mysql+pymysql://root:123456@localhost:3306/miniblog"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # JWT配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 分页配置
    posts_per_page: int = 10
    max_posts_per_page: int = 100
    
    # 缓存配置
    cache_timeout: int = 300  # 5分钟
    
    # 用户服务配置
    user_service_url: str = "http://localhost:5001"
    
    # Nacos配置
    nacos_host: str = "localhost"
    nacos_port: int = 8848
    nacos_namespace: str = "public"
    nacos_group: str = "DEFAULT_GROUP"
    
    # CORS配置
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()

# 兼容旧的Flask配置结构
class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 10
    MAX_POSTS_PER_PAGE = 100
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:123456@localhost:3306/miniblog'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:123456@mysql:3306/miniblog'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}