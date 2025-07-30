import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'blog-service-secret-key-2024'
    
    # 服务配置
    SERVICE_NAME = os.environ.get('SERVICE_NAME') or 'blog-service'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://root:password@localhost:3306/blog_service'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 1)  # 博客服务使用DB 1
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_DECODE_RESPONSES = True
    

    
    # 服务配置
    SERVICE_NAME = 'blog-service'
    SERVICE_IP = os.environ.get('SERVICE_IP') or '127.0.0.1'
    SERVICE_PORT = int(os.environ.get('SERVICE_PORT') or 5002)
    
    # 用户服务配置
    USER_SERVICE_NAME = 'user-service'
    USER_SERVICE_TIMEOUT = 5  # 秒
    
    # JWT配置（用于验证用户服务的令牌）
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'shared-jwt-secret-key-2024'
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # 分页配置
    POSTS_PER_PAGE = int(os.environ.get('POSTS_PER_PAGE') or 10)
    MAX_POSTS_PER_PAGE = int(os.environ.get('MAX_POSTS_PER_PAGE') or 100)
    
    # 缓存配置
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT') or 300)  # 5分钟
    CACHE_POSTS_TIMEOUT = int(os.environ.get('CACHE_POSTS_TIMEOUT') or 600)  # 10分钟
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/blog-service.log'
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建日志目录
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'mysql+pymysql://root:password@localhost:3306/blog_service_dev'
    
    # 开发环境使用较短的缓存时间
    CACHE_DEFAULT_TIMEOUT = 60
    CACHE_POSTS_TIMEOUT = 120

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://root:password@mysql:3306/blog_service'
    
    # 生产环境Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'redis'
    

    
    # 生产环境服务配置
    SERVICE_IP = os.environ.get('SERVICE_IP') or '0.0.0.0'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                'logs/blog-service.log',
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('博客服务启动')

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:'
    
    # 测试环境禁用CSRF保护
    WTF_CSRF_ENABLED = False
    
    # 测试环境使用内存Redis
    REDIS_HOST = 'localhost'
    REDIS_DB = 15  # 使用专门的测试数据库
    
    # 测试环境缓存配置
    CACHE_DEFAULT_TIMEOUT = 1
    CACHE_POSTS_TIMEOUT = 1

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}