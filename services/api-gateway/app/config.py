import os
from datetime import timedelta

class Config:
    """基础配置"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'api-gateway-secret-key-2024'
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_DECODE_RESPONSES = True
    
    # Nacos配置
    NACOS_SERVER = os.environ.get('NACOS_SERVER') or 'localhost:8848'
    NACOS_NAMESPACE = os.environ.get('NACOS_NAMESPACE') or 'public'
    NACOS_USERNAME = os.environ.get('NACOS_USERNAME') or 'nacos'
    NACOS_PASSWORD = os.environ.get('NACOS_PASSWORD') or 'nacos'
    
    # 服务配置
    SERVICE_NAME = 'api-gateway'
    SERVICE_HOST = os.environ.get('SERVICE_HOST') or 'localhost'
    SERVICE_PORT = int(os.environ.get('SERVICE_PORT') or 5000)
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = 'HS256'
    
    # 缓存配置
    CACHE_DEFAULT_TIMEOUT = 300  # 5分钟
    CACHE_LONG_TIMEOUT = 3600   # 1小时
    
    # 限流配置
    RATE_LIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    RATE_LIMIT_DEFAULT = "100 per hour"  # 默认限流
    RATE_LIMIT_PER_METHOD = True
    
    # 请求超时配置
    REQUEST_TIMEOUT = 30  # 30秒
    CONNECT_TIMEOUT = 5   # 5秒
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 0.3
    
    # 熔断器配置
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION = Exception
    
    # 负载均衡配置
    LOAD_BALANCER_STRATEGY = 'round_robin'  # round_robin, random, weighted
    
    # 健康检查配置
    HEALTH_CHECK_INTERVAL = 30  # 30秒
    HEALTH_CHECK_TIMEOUT = 5    # 5秒
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # CORS配置
    CORS_ORIGINS = ['*']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    
    # 服务发现配置
    SERVICE_DISCOVERY_CACHE_TTL = 60  # 服务发现缓存时间
    
    # 监控配置
    METRICS_ENABLED = True
    METRICS_PATH = '/metrics'
    
    # 后端服务配置
    BACKEND_SERVICES = {
        'user-service': {
            'path_prefix': '/users',
            'health_check': '/healthz',
            'timeout': 30,
            'retries': 3
        },
        'blog-service': {
            'path_prefix': '/blog',
            'health_check': '/healthz',
            'timeout': 30,
            'retries': 3
        }
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    # 开发环境下的特殊配置
    RATE_LIMIT_DEFAULT = "1000 per hour"  # 开发环境放宽限流
    
    # 开发环境服务地址
    BACKEND_SERVICES = {
        'user-service': {
            'path_prefix': '/users',
            'health_check': '/healthz',
            'timeout': 30,
            'retries': 3,
            'fallback_url': 'http://localhost:5002'  # 开发环境备用地址
        },
        'blog-service': {
            'path_prefix': '/blog',
            'health_check': '/healthz',
            'timeout': 30,
            'retries': 3,
            'fallback_url': 'http://localhost:5001'  # 开发环境备用地址
        }
    }

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # 生产环境限流更严格
    RATE_LIMIT_DEFAULT = "50 per hour"
    
    # 生产环境超时时间更短
    REQUEST_TIMEOUT = 15
    CONNECT_TIMEOUT = 3
    
    # 生产环境CORS更严格
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # 生产环境日志级别
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 测试环境使用内存数据库
    REDIS_DB = 15  # 使用不同的Redis数据库
    
    # 测试环境不限流
    RATE_LIMIT_DEFAULT = "10000 per hour"
    
    # 测试环境超时时间更短
    REQUEST_TIMEOUT = 5
    CONNECT_TIMEOUT = 1
    
    # 测试环境禁用服务注册
    NACOS_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}