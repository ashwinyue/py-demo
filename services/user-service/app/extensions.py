from flask_sqlalchemy import SQLAlchemy
import redis
import nacos
import logging
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional

# 数据库实例
db = SQLAlchemy()


class RedisClient:
    """Redis客户端封装"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    def init_app(self, app):
        """初始化Redis客户端"""
        try:
            self.redis_client = redis.Redis(
                host=app.config['REDIS_HOST'],
                port=app.config['REDIS_PORT'],
                password=app.config['REDIS_PASSWORD'],
                db=app.config['REDIS_DB'],
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # 测试连接
            self.redis_client.ping()
            app.logger.info("Redis connected successfully")
        except Exception as e:
            app.logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logging.error(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logging.error(f"Redis set error: {e}")
            return False
    
    def delete(self, *keys) -> int:
        """删除缓存键"""
        if not self.redis_client:
            return 0
        try:
            return self.redis_client.delete(*keys)
        except Exception as e:
            logging.error(f"Redis delete error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logging.error(f"Redis exists error: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logging.error(f"Redis incr error: {e}")
            return None
    
    def expire(self, key: str, time: int) -> bool:
        """设置过期时间"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.expire(key, time)
        except Exception as e:
            logging.error(f"Redis expire error: {e}")
            return False
    
    def sadd(self, name: str, *values) -> int:
        """添加集合成员"""
        if not self.redis_client:
            return 0
        try:
            return self.redis_client.sadd(name, *values)
        except Exception as e:
            logging.error(f"Redis sadd error: {e}")
            return 0
    
    def srem(self, name: str, *values) -> int:
        """删除集合成员"""
        if not self.redis_client:
            return 0
        try:
            return self.redis_client.srem(name, *values)
        except Exception as e:
            logging.error(f"Redis srem error: {e}")
            return 0
    
    def sismember(self, name: str, value: str) -> bool:
        """检查是否为集合成员"""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.sismember(name, value))
        except Exception as e:
            logging.error(f"Redis sismember error: {e}")
            return False
    
    def flushdb(self) -> bool:
        """清空当前数据库"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logging.error(f"Redis flushdb error: {e}")
            return False


class NacosClient:
    """Nacos客户端封装"""
    
    def __init__(self):
        self.client: Optional[nacos.NacosClient] = None
        self.service_name: Optional[str] = None
        self.service_ip: Optional[str] = None
        self.service_port: Optional[int] = None
    
    def init_app(self, app):
        """初始化Nacos客户端"""
        try:
            server_addresses = app.config['NACOS_SERVER']
            namespace = app.config['NACOS_NAMESPACE']
            username = app.config.get('NACOS_USERNAME')
            password = app.config.get('NACOS_PASSWORD')
            
            self.client = nacos.NacosClient(
                server_addresses=server_addresses,
                namespace=namespace,
                username=username,
                password=password
            )
            
            self.service_name = app.config['SERVICE_NAME']
            self.service_ip = app.config['SERVICE_HOST']
            self.service_port = app.config['SERVICE_PORT']
            
            app.logger.info("Nacos client initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize Nacos client: {e}")
            self.client = None
    
    def register_service(self, service_name: str, ip: str, port: int, metadata: dict = None):
        """注册服务"""
        if not self.client:
            return False
        try:
            return self.client.add_naming_instance(
                service_name=service_name,
                ip=ip,
                port=port,
                metadata=metadata or {}
            )
        except Exception as e:
            logging.error(f"Failed to register service: {e}")
            return False
    
    def discover_service(self, service_name: str):
        """发现服务实例"""
        if not self.client:
            return []
        try:
            return self.client.list_naming_instance(service_name=service_name)
        except Exception as e:
            logging.error(f"Failed to discover service: {e}")
            return []


# 创建实例
redis_client = RedisClient()
nacos_client = NacosClient()


def get_redis_client():
    """获取Redis客户端实例"""
    return redis_client


def get_nacos_client():
    """获取Nacos客户端实例"""
    return nacos_client


def token_required(f):
    """Token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            from app.models import User
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            from app.models import User
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
            if not current_user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated