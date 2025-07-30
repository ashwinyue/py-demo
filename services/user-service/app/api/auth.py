import jwt
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from werkzeug.security import check_password_hash
from . import api
from ..models import User, LoginLog, VerificationCode
from ..extensions import db, redis_client
from ..utils.validators import validate_email, validate_password
from ..utils.decorators import token_required, rate_limit
from ..utils.helpers import get_client_ip, parse_user_agent
from ..utils.email import send_verification_email

@bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json() or {}
    
    if 'username' not in data or 'password' not in data:
        return bad_request('Must include username and password')
    
    try:
        # 查找用户
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 401
        
        # 生成令牌
        access_token, refresh_token = generate_tokens(user.id)
        
        # 创建会话记录
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        )
        
        # 更新用户最后登录时间
        user.last_login = datetime.utcnow()
        
        db.session.add(session)
        db.session.commit()
        
        # 缓存用户信息到Redis
        redis_client = get_redis_client()
        if redis_client:
            user_cache_key = f'user_session_{user.id}'
            redis_client.setex(
                user_cache_key, 
                3600,  # 1小时过期
                access_token
            )
        
        current_app.logger.info(f'用户登录成功: {user.username}')
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(include_email=True),
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            }
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'登录失败: {e}')
        return jsonify({'error': 'Login failed'}), 500

@bp.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    """用户登出"""
    try:
        user_id = request.current_user_id
        
        # 获取当前令牌
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(' ')[1]
            
            # 将令牌加入黑名单（Redis）
            redis_client = get_redis_client()
            if redis_client:
                # 令牌黑名单
                blacklist_key = f'token_blacklist_{token}'
                redis_client.setex(blacklist_key, 3600, 'blacklisted')
                
                # 清除用户会话缓存
                user_cache_key = f'user_session_{user_id}'
                redis_client.delete(user_cache_key)
        
        # 标记数据库中的会话为非活跃
        UserSession.query.filter_by(
            user_id=user_id,
            session_token=token,
            is_active=True
        ).update({'is_active': False})
        
        db.session.commit()
        
        current_app.logger.info(f'用户登出成功: {user_id}')
        return jsonify({'message': 'Logout successful'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'登出失败: {e}')
        return jsonify({'error': 'Logout failed'}), 500

@bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新访问令牌"""
    data = request.get_json() or {}
    
    if 'refresh_token' not in data:
        return bad_request('Refresh token is required')
    
    try:
        # 验证刷新令牌
        payload = verify_token(data['refresh_token'], token_type='refresh')
        if not payload:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        user_id = payload['user_id']
        
        # 检查用户是否存在且活跃
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # 检查会话是否存在且活跃
        session = UserSession.query.filter_by(
            user_id=user_id,
            refresh_token=data['refresh_token'],
            is_active=True
        ).first()
        
        if not session:
            return jsonify({'error': 'Invalid session'}), 401
        
        # 生成新的访问令牌
        new_access_token, new_refresh_token = generate_tokens(user_id)
        
        # 更新会话
        session.session_token = new_access_token
        session.refresh_token = new_refresh_token
        session.expires_at = datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        
        db.session.commit()
        
        # 更新Redis缓存
        redis_client = get_redis_client()
        if redis_client:
            user_cache_key = f'user_session_{user_id}'
            redis_client.setex(user_cache_key, 3600, new_access_token)
        
        current_app.logger.info(f'令牌刷新成功: {user.username}')
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'tokens': {
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
                'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            }
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'令牌刷新失败: {e}')
        return jsonify({'error': 'Token refresh failed'}), 500

@bp.route('/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """获取当前用户信息"""
    try:
        user = User.query.get(request.current_user_id)
        if not user:
            return not_found('User not found')
        
        return jsonify({
            'user': user.to_dict(include_email=True),
            'permissions': {
                'is_admin': user.is_admin,
                'is_active': user.is_active
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'获取用户信息失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/auth/change-password', methods=['POST'])
@token_required
def change_password():
    """修改密码"""
    data = request.get_json() or {}
    
    if 'current_password' not in data or 'new_password' not in data:
        return bad_request('Must include current_password and new_password')
    
    try:
        user = User.query.get(request.current_user_id)
        if not user:
            return not_found('User not found')
        
        # 验证当前密码
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # 设置新密码
        user.set_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 清除所有会话，强制重新登录
        UserSession.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
        db.session.commit()
        
        # 清除Redis缓存
        redis_client = get_redis_client()
        if redis_client:
            user_cache_key = f'user_session_{user.id}'
            redis_client.delete(user_cache_key)
        
        current_app.logger.info(f'密码修改成功: {user.username}')
        return jsonify({'message': 'Password changed successfully'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'密码修改失败: {e}')
        return jsonify({'error': 'Password change failed'}), 500

@bp.route('/auth/verify', methods=['POST'])
def verify_user_token():
    """验证用户令牌（供其他服务调用）"""
    data = request.get_json() or {}
    
    if 'token' not in data:
        return bad_request('Token is required')
    
    try:
        # 检查令牌是否在黑名单中
        redis_client = get_redis_client()
        if redis_client:
            blacklist_key = f'token_blacklist_{data["token"]}'
            if redis_client.exists(blacklist_key):
                return jsonify({'valid': False, 'error': 'Token is blacklisted'}), 401
        
        # 验证令牌
        payload = verify_token(data['token'])
        if not payload:
            return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 401
        
        # 获取用户信息
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'valid': False, 'error': 'User not found or inactive'}), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin,
                'is_active': user.is_active
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'令牌验证失败: {e}')
        return jsonify({'valid': False, 'error': 'Token verification failed'}), 500