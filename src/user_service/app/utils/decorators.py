# -*- coding: utf-8 -*-
"""
装饰器工具函数
"""

from jose import jwt
import time
from functools import wraps
from datetime import datetime
from flask import request, jsonify, current_app
from ..models import User
from ..extensions import redis_client


def token_required(f):
    """
    JWT令牌验证装饰器 - 简化版本，依赖Tyk进行认证
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token is missing'
            }), 401
        
        try:
            # 由于Tyk已经验证了令牌，我们只需要解码获取用户信息
            # 不验证签名，因为Tyk已经验证过了
            payload = jwt.decode(token, options={"verify_signature": False})
            
            user_id = payload.get('user_id')
            current_user = User.query.get(user_id)
            
            if not current_user or not current_user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'User not found or inactive'
                }), 401
            
            # 将当前用户传递给被装饰的函数
            return f(current_user, *args, **kwargs)
            
        except jwt.DecodeError:
            return jsonify({
                'success': False,
                'message': 'Invalid token format'
            }), 401
        except Exception as e:
            current_app.logger.error(f'Token validation error: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Token validation failed'
            }), 401
    
    return decorated


def admin_required(f):
    """
    管理员权限验证装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin privileges required'
            }), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def permission_required(permission_name):
    """
    权限验证装饰器
    
    Args:
        permission_name: 所需权限名称
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if not current_user.has_permission(permission_name):
                return jsonify({
                    'success': False,
                    'message': f'Permission "{permission_name}" required'
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    
    return decorator


def role_required(role_name):
    """
    角色验证装饰器
    
    Args:
        role_name: 所需角色名称
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if not current_user.has_role(role_name):
                return jsonify({
                    'success': False,
                    'message': f'Role "{role_name}" required'
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    
    return decorator


def rate_limit(max_requests=100, window=3600, per_user=True):
    """
    速率限制装饰器
    
    Args:
        max_requests: 最大请求次数
        window: 时间窗口（秒）
        per_user: 是否按用户限制
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 获取客户端标识
            if per_user:
                # 尝试从token获取用户ID
                user_id = None
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.replace('Bearer ', '')
                    try:
                        payload = jwt.decode(
                            token,
                            current_app.config['SECRET_KEY'],
                            algorithms=['HS256']
                        )
                        user_id = payload.get('user_id')
                    except:
                        pass
                
                client_id = f"user:{user_id}" if user_id else f"ip:{request.remote_addr}"
            else:
                client_id = f"ip:{request.remote_addr}"
            
            # 构建Redis键
            rate_limit_key = f"rate_limit:{f.__name__}:{client_id}"
            
            try:
                # 获取当前请求次数
                current_requests = redis_client.get(rate_limit_key)
                current_requests = int(current_requests) if current_requests else 0
                
                if current_requests >= max_requests:
                    return jsonify({
                        'success': False,
                        'message': 'Rate limit exceeded',
                        'retry_after': window
                    }), 429
                
                # 增加请求计数
                pipe = redis_client.pipeline()
                if pipe:
                    pipe.incr(rate_limit_key)
                    pipe.expire(rate_limit_key, window)
                    pipe.execute()
                else:
                    # 如果pipeline不可用，使用单独的命令
                    redis_client.incr(rate_limit_key)
                    redis_client.expire(rate_limit_key, window)
                
            except Exception as e:
                current_app.logger.error(f'Rate limit error: {str(e)}')
                # 如果Redis出错，允许请求通过
                pass
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def cache_result(timeout=300, key_prefix=None):
    """
    结果缓存装饰器
    
    Args:
        timeout: 缓存超时时间（秒）
        key_prefix: 缓存键前缀
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 构建缓存键
            cache_key_parts = [key_prefix or f.__name__]
            
            # 添加参数到缓存键
            for arg in args:
                if hasattr(arg, 'id'):  # 对象有ID属性
                    cache_key_parts.append(str(arg.id))
                elif isinstance(arg, (str, int, float)):
                    cache_key_parts.append(str(arg))
            
            for key, value in kwargs.items():
                if isinstance(value, (str, int, float)):
                    cache_key_parts.append(f"{key}:{value}")
            
            cache_key = f"cache:{'_'.join(cache_key_parts)}"
            
            try:
                # 尝试从缓存获取结果
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    import json
                    return json.loads(cached_result)
                
                # 执行函数并缓存结果
                result = f(*args, **kwargs)
                
                # 只缓存成功的响应
                if hasattr(result, 'status_code') and result.status_code == 200:
                    import json
                    redis_client.setex(cache_key, timeout, json.dumps(result.get_json()))
                
                return result
                
            except Exception as e:
                current_app.logger.error(f'Cache error: {str(e)}')
                # 如果缓存出错，直接执行函数
                return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def validate_json(*required_fields):
    """
    JSON数据验证装饰器
    
    Args:
        required_fields: 必需的字段列表
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Content-Type must be application/json'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON data'
                }), 400
            
            # 检查必需字段
            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None or data[field] == '':
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator