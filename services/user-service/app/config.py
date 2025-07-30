import os
from datetime import timedelta
from decouple import config as env_config

class Config:
    """基础配置"""
    # 基本配置
    SECRET_KEY = env_config('SECRET_KEY', default='dev-secret-key-change-in-production')
    
    # 服务配置
    SERVICE_NAME = env_config('SERVICE_NAME', default='user-service')
    
    # 数据库配置
    MYSQL_HOST = env_config('MYSQL_HOST', default='localhost')
    MYSQL_PORT = env_config('MYSQL_PORT', default=3306, cast=int)
    MYSQL_USER = env_config('MYSQL_USER', default='root')
    MYSQL_PASSWORD = env_config('MYSQL_PASSWORD', default='password')
    MYSQL_DATABASE = env_config('MYSQL_DATABASE', default='miniblog_users')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': -1,
        'max_overflow': 0
    }
    
    # Redis配置
    REDIS_HOST = env_config('REDIS_HOST', default='localhost')
    REDIS_PORT = env_config('REDIS_PORT', default=6379, cast=int)
    REDIS_PASSWORD = env_config('REDIS_PASSWORD', default=None)
    REDIS_DB = env_config('REDIS_DB', default=1, cast=int)
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # JWT配置
    JWT_SECRET_KEY = env_config('JWT_SECRET_KEY', default=SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 服务配置
    SERVICE_NAME = env_config('SERVICE_NAME', default='user-service')
    SERVICE_HOST = env_config('SERVICE_HOST', default='127.0.0.1')
    SERVICE_PORT = env_config('SERVICE_PORT', default=5001, cast=int)
    SERVICE_VERSION = env_config('SERVICE_VERSION', default='1.0.0')
    
    # Nacos配置
    NACOS_SERVER = env_config('NACOS_SERVER', default='127.0.0.1:8848')
    NACOS_NAMESPACE = env_config('NACOS_NAMESPACE', default='public')
    NACOS_GROUP = env_config('NACOS_GROUP', default='DEFAULT_GROUP')
    NACOS_USERNAME = env_config('NACOS_USERNAME', default=None)
    NACOS_PASSWORD = env_config('NACOS_PASSWORD', default=None)
    
    # 日志配置
    LOG_TO_STDOUT = env_config('LOG_TO_STDOUT', default=True, cast=bool)
    LOG_LEVEL = env_config('LOG_LEVEL', default='INFO')
    
    # 安全配置
    PASSWORD_HASH_ROUNDS = 12
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_TIMEOUT = 900  # 15分钟
    
    # 邮件配置
    MAIL_SERVER = env_config('MAIL_SERVER', default='smtp.gmail.com')
    MAIL_PORT = env_config('MAIL_PORT', default=587, cast=int)
    MAIL_USE_TLS = env_config('MAIL_USE_TLS', default=True, cast=bool)
    MAIL_USERNAME = env_config('MAIL_USERNAME', default=None)
    MAIL_PASSWORD = env_config('MAIL_PASSWORD', default=None)
    MAIL_DEFAULT_SENDER = env_config('MAIL_DEFAULT_SENDER', default=MAIL_USERNAME)
    
    # 验证码配置
    VERIFICATION_CODE_EXPIRES = 600  # 10分钟
    VERIFICATION_CODE_LENGTH = 6
    
    # 分页配置
    USERS_PER_PAGE = 20
    MAX_PER_PAGE = 100
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = env_config('UPLOAD_FOLDER', default='uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # API限流配置
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # 开发环境使用较短的token过期时间
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # 开发环境日志级别
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境密码哈希轮数较少
    PASSWORD_HASH_ROUNDS = 4


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境使用环境变量中的密钥
    SECRET_KEY = env_config('SECRET_KEY')
    JWT_SECRET_KEY = env_config('JWT_SECRET_KEY')
    
    # 生产环境日志级别
    LOG_LEVEL = 'WARNING'
    
    # 生产环境更严格的安全配置
    PASSWORD_HASH_ROUNDS = 15
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_ATTEMPT_TIMEOUT = 1800  # 30分钟


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    
    # 测试数据库
    MYSQL_DATABASE = env_config('TEST_MYSQL_DATABASE', default='test_miniblog_users')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@"
        f"{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    
    # 测试Redis数据库
    REDIS_DB = 15
    REDIS_URL = f"redis://:{Config.REDIS_PASSWORD}@{Config.REDIS_HOST}:{Config.REDIS_PORT}/{REDIS_DB}" if Config.REDIS_PASSWORD else f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{REDIS_DB}"
    
    # 测试环境使用较短的token过期时间
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)
    
    # 测试环境密码哈希轮数最少
    PASSWORD_HASH_ROUNDS = 1
    
    # 禁用CSRF保护
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}