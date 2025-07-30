from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    # 应用基本配置
    app_name: str = "User Service"
    debug: bool = True
    
    # 数据库配置 (使用SQLite进行演示)
    database_url: str = "sqlite:///./users.db"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: Optional[str] = None
    
    # JWT配置
    jwt_secret_key: str = "miniblog-jwt-secret-key-2024"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24小时
    jwt_refresh_token_expire_days: int = 30
    
    # 缓存配置
    cache_timeout: int = 300  # 5分钟
    
    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100
    
    # 安全配置
    password_hash_rounds: int = 12
    max_login_attempts: int = 5
    login_attempt_timeout: int = 900  # 15分钟
    
    # 验证码配置
    verification_code_expires: int = 600  # 10分钟
    verification_code_length: int = 6
    
    # CORS配置
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

# 全局设置实例
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """获取设置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings