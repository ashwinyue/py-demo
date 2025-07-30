from flask import request, jsonify, current_app, g
from app.api import bp
from app.extensions import make_service_request, get_redis_client, rate_limit
from functools import wraps
import jwt
import json
from datetime import datetime

def verify_token_with_user_service(token):
    """通过用户服务验证令牌"""
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = make_service_request(
            service_name='user-service',
            path='/api/auth/verify',
            method='POST',
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        current_app.logger.error(f'令牌验证失败: {e}')
        return None

def verify_token_locally(token):
    """本地验证JWT令牌"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        
        # 检查令牌是否在黑名单中
        redis_client = get_redis_client()
        if redis_client:
            blacklist_key = f'token_blacklist_{token}'
            if redis_client.exists(blacklist_key):
                return None
        
        return payload
    
    except jwt.ExpiredSignatureError:
        current_app.logger.warning('令牌已过期')
        return None
    except jwt.InvalidTokenError:
        current_app.logger.warning('无效令牌')
        return None
    except Exception as e:
        current_app.logger.error(f'令牌验证失败: {e}')
        return None

def get_user_info_from_cache(user_id):
    """从缓存获取用户信息"""
    redis_client = get_redis_client()
    if not redis_client:
        return None
    
    try:
        cache_key = f'user_info_{user_id}'
        cached_user = redis_client.get(cache_key)
        if cached_user:
            return json.loads(cached_user)
        return None
    except Exception as e:
        current_app.logger.error(f'从缓存获取用户信息失败: {e}')
        return None

def cache_user_info(user_id, user_info):
    """缓存用户信息"""
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        cache_key = f'user_info_{user_id}'
        redis_client.setex(
            cache_key,
            current_app.config['CACHE_DEFAULT_TIMEOUT'],
            json.dumps(user_info)
        )
    except Exception as e:
        current_app.logger.error(f'缓存用户信息失败: {e}')

def token_required(f):
    """令牌验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'error': 'Invalid Authorization header format',
                    'message': 'Authorization header must be in format: Bearer <token>'
                }), 401
        
        if not token:
            return jsonify({
                'error': 'Token missing',
                'message': 'Authorization token is required'
            }), 401
        
        # 首先尝试本地验证
        payload = verify_token_locally(token)
        
        if payload:
            # 本地验证成功，从缓存获取用户信息
            user_info = get_user_info_from_cache(payload.get('user_id'))
            
            if not user_info:
                # 缓存中没有用户信息，通过用户服务验证
                verification_result = verify_token_with_user_service(token)
                if verification_result and verification_result.get('valid'):
                    user_info = verification_result.get('user')
                    if user_info:
                        cache_user_info(user_info['id'], user_info)
                else:
                    return jsonify({
                        'error': 'Invalid token',
                        'message': 'Token verification failed'
                    }), 401
        else:
            # 本地验证失败，通过用户服务验证
            verification_result = verify_token_with_user_service(token)
            if verification_result and verification_result.get('valid'):
                user_info = verification_result.get('user')
                if user_info:
                    cache_user_info(user_info['id'], user_info)
            else:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Token verification failed'
                }), 401
        
        if not user_info:
            return jsonify({
                'error': 'User not found',
                'message': 'User information not available'
            }), 401
        
        # 将用户信息存储到g对象中
        g.current_user = user_info
        g.token = token
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please login first'
            }), 401
        
        if not g.current_user.get('is_admin'):
            return jsonify({
                'error': 'Admin access required',
                'message': 'This operation requires administrator privileges'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated

@bp.route('/verify-token', methods=['POST'])
@rate_limit("1000 per hour")
def verify_token():
    """验证令牌接口（供其他服务调用）"""
    try:
        data = request.get_json() or {}
        token = data.get('token')
        
        if not token:
            # 尝试从Authorization头获取
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(' ')[1]
                except IndexError:
                    pass
        
        if not token:
            return jsonify({
                'valid': False,
                'error': 'Token missing',
                'message': 'Token is required'
            }), 400
        
        # 首先尝试本地验证
        payload = verify_token_locally(token)
        
        if payload:
            # 本地验证成功，获取用户信息
            user_info = get_user_info_from_cache(payload.get('user_id'))
            
            if not user_info:
                # 缓存中没有用户信息，通过用户服务验证
                verification_result = verify_token_with_user_service(token)
                if verification_result and verification_result.get('valid'):
                    user_info = verification_result.get('user')
                    if user_info:
                        cache_user_info(user_info['id'], user_info)
                else:
                    return jsonify({
                        'valid': False,
                        'error': 'Token verification failed',
                        'message': 'Unable to verify token with user service'
                    }), 401
            
            return jsonify({
                'valid': True,
                'user': user_info,
                'payload': payload,
                'verified_by': 'gateway_local'
            })
        else:
            # 本地验证失败，通过用户服务验证
            verification_result = verify_token_with_user_service(token)
            if verification_result:
                if verification_result.get('valid'):
                    user_info = verification_result.get('user')
                    if user_info:
                        cache_user_info(user_info['id'], user_info)
                    
                    return jsonify({
                        'valid': True,
                        'user': user_info,
                        'verified_by': 'user_service'
                    })
                else:
                    return jsonify({
                        'valid': False,
                        'error': verification_result.get('error', 'Token invalid'),
                        'message': verification_result.get('message', 'Token verification failed')
                    }), 401
            else:
                return jsonify({
                    'valid': False,
                    'error': 'Service unavailable',
                    'message': 'Unable to verify token - user service unavailable'
                }), 503
    
    except Exception as e:
        current_app.logger.error(f'令牌验证接口失败: {e}')
        return jsonify({
            'valid': False,
            'error': 'Internal error',
            'message': str(e)
        }), 500

@bp.route('/user-info', methods=['GET'])
@token_required
def get_current_user_info():
    """获取当前用户信息"""
    try:
        return jsonify({
            'user': g.current_user,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f'获取用户信息失败: {e}')
        return jsonify({
            'error': 'Failed to get user info',
            'message': str(e)
        }), 500

@bp.route('/refresh-user-cache', methods=['POST'])
@token_required
def refresh_user_cache():
    """刷新用户缓存"""
    try:
        user_id = g.current_user['id']
        
        # 清除缓存
        redis_client = get_redis_client()
        if redis_client:
            cache_key = f'user_info_{user_id}'
            redis_client.delete(cache_key)
        
        # 重新获取用户信息
        verification_result = verify_token_with_user_service(g.token)
        if verification_result and verification_result.get('valid'):
            user_info = verification_result.get('user')
            if user_info:
                cache_user_info(user_info['id'], user_info)
                g.current_user = user_info
                
                return jsonify({
                    'message': 'User cache refreshed successfully',
                    'user': user_info
                })
        
        return jsonify({
            'error': 'Failed to refresh cache',
            'message': 'Unable to get updated user information'
        }), 500
    
    except Exception as e:
        current_app.logger.error(f'刷新用户缓存失败: {e}')
        return jsonify({
            'error': 'Failed to refresh user cache',
            'message': str(e)
        }), 500

@bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """登出（将令牌加入黑名单）"""
    try:
        token = g.token
        
        # 将令牌加入黑名单
        redis_client = get_redis_client()
        if redis_client:
            blacklist_key = f'token_blacklist_{token}'
            # 设置过期时间为令牌的剩余有效期
            redis_client.setex(blacklist_key, 86400, '1')  # 24小时
        
        # 清除用户缓存
        user_id = g.current_user['id']
        cache_key = f'user_info_{user_id}'
        if redis_client:
            redis_client.delete(cache_key)
        
        # 通知用户服务登出
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            make_service_request(
                service_name='user-service',
                path='/api/auth/logout',
                method='POST',
                headers=headers
            )
        except Exception as e:
            current_app.logger.warning(f'通知用户服务登出失败: {e}')
        
        return jsonify({
            'message': 'Logged out successfully'
        })
    
    except Exception as e:
        current_app.logger.error(f'登出失败: {e}')
        return jsonify({
            'error': 'Logout failed',
            'message': str(e)
        }), 500