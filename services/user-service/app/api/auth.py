# -*- coding: utf-8 -*-
"""
用户认证相关API
"""

import jwt
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Role, Permission, LoginLog
from app.extensions import db, redis_client
from app.utils import (
    validate_email, validate_password, validate_username,
    get_client_ip, parse_user_agent, generate_verification_code,
    mask_email, sanitize_input, token_required, rate_limit,
    cache_verification_code, get_cached_verification_code,
    delete_verification_code, cache_blacklist_token,
    is_token_blacklisted, cache_clear_user
)
from . import api

@api.route('/auth/register', methods=['POST'])
@rate_limit(max_requests=5, window=300)  # 5次/5分钟
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required'
                }), 400
        
        username = sanitize_input(data['username'].strip())
        email = sanitize_input(data['email'].strip().lower())
        password = data['password']
        nickname = sanitize_input(data.get('nickname', '').strip())
        
        # 验证输入格式
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        if not validate_username(username):
            return jsonify({
                'success': False,
                'message': 'Invalid username format'
            }), 400
        
        password_validation = validate_password(password)
        if not password_validation['valid']:
            return jsonify({
                'success': False,
                'message': password_validation['message']
            }), 400
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'Email already exists'
            }), 409
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            nickname=nickname or username,
            created_at=datetime.utcnow(),
            is_active=False  # 需要邮箱验证
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 生成验证码并缓存
        verification_code = generate_verification_code()
        cache_verification_code(email, verification_code, 300)  # 5分钟过期
        
        # 发送验证邮件（这里需要实现邮件发送功能）
        # send_verification_email(email, verification_code)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful. Please check your email for verification code.',
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': mask_email(user.email)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Registration failed'
        }), 500


@api.route('/auth/login', methods=['POST'])
@rate_limit(max_requests=10, window=300)  # 10次/5分钟
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400
        
        username = sanitize_input(data['username'].strip())
        password = data['password']
        
        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            # 记录失败的登录尝试
            client_ip = get_client_ip(request)
            user_agent_info = parse_user_agent(request.headers.get('User-Agent', ''))
            
            login_log = LoginLog(
                user_id=user.id if user else None,
                ip_address=client_ip,
                user_agent=request.headers.get('User-Agent', ''),
                browser=user_agent_info.get('browser', 'Unknown'),
                os=user_agent_info.get('os', 'Unknown'),
                device=user_agent_info.get('device', 'Unknown'),
                login_time=datetime.utcnow(),
                is_successful=False
            )
            
            db.session.add(login_log)
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
        
        # 检查用户状态
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Account is not activated. Please verify your email.'
            }), 401
        
        # 生成JWT令牌
        now = datetime.utcnow()
        access_token_payload = {
            'user_id': user.id,
            'username': user.username,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(hours=24)
        }
        
        refresh_token_payload = {
            'user_id': user.id,
            'username': user.username,
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(days=30)
        }
        
        access_token = jwt.encode(
            access_token_payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            refresh_token_payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        # 获取客户端信息
        client_ip = get_client_ip()
        user_agent_info = parse_user_agent()
        
        # 记录登录日志
        login_log = LoginLog(
            user_id=user.id,
            ip_address=client_ip,
            user_agent=request.headers.get('User-Agent', ''),
            browser=user_agent_info.get('browser', 'Unknown'),
            os=user_agent_info.get('os', 'Unknown'),
            device=user_agent_info.get('device', 'Unknown'),
            login_time=datetime.utcnow(),
            is_successful=True
        )
        
        db.session.add(login_log)
        
        # 更新用户最后登录时间
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 86400,  # 24小时
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname,
                    'is_active': user.is_active
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Login failed'
        }), 500


def generate_token(user_id, token_type='access', expires_delta=None):
    """生成JWT令牌"""
    if expires_delta is None:
        if token_type == 'access':
            expires_delta = timedelta(hours=current_app.config['JWT_ACCESS_TOKEN_EXPIRES_HOURS'])
        else:
            expires_delta = timedelta(days=current_app.config['JWT_REFRESH_TOKEN_EXPIRES_DAYS'])
    
    payload = {
        'user_id': user_id,
        'type': token_type,
        'exp': datetime.utcnow() + expires_delta,
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )


@api.route('/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户登出"""
    try:
        # 获取当前令牌
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if token:
            # 将令牌加入黑名单
            token_key = f"blacklist_token:{token[:10]}"
            redis_client.set(token_key, '1', ex=current_app.config['JWT_ACCESS_TOKEN_EXPIRES_HOURS'] * 3600)
            
            # 删除用户令牌缓存
            user_token_key = f"user_token:{current_user.id}:{token[:10]}"
            redis_client.delete(user_token_key)
            
            # 更新登录日志
            login_log = LoginLog.query.filter_by(
                user_id=current_user.id,
                token_id=token[:10],
                logout_time=None
            ).first()
            
            if login_log:
                login_log.mark_logout()
                db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Logout error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Logout failed'
        }), 500


@api.route('/auth/verify-token', methods=['POST'])
def verify_token():
    """验证令牌"""
    try:
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Authorization header is required'
            }), 401
        
        token = auth_header.replace('Bearer ', '')
        
        # 检查令牌是否在黑名单中
        blacklist_key = f"blacklist_token:{token[:10]}"
        if redis_client.exists(blacklist_key):
            return jsonify({
                'success': False,
                'message': 'Token has been revoked'
            }), 401
        
        # 验证JWT令牌
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if payload.get('type') != 'access':
                raise jwt.InvalidTokenError('Invalid token type')
            
            user_id = payload.get('user_id')
            user = User.query.get(user_id)
            
            if not user or not user.is_active:
                raise jwt.InvalidTokenError('User not found or inactive')
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_verified': user.is_verified,
                'roles': [role.name for role in user.get_roles()],
                'permissions': [perm.name for perm in user.get_permissions()]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Token verification error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Token verification failed'
        }), 500


@api.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新访问令牌"""
    try:
        data = request.get_json() or {}
        
        if 'refresh_token' not in data:
            return jsonify({
                'success': False,
                'message': 'Refresh token is required'
            }), 400
        
        refresh_token = data['refresh_token']
        
        # 验证刷新令牌
        try:
            payload = jwt.decode(
                refresh_token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if payload.get('type') != 'refresh':
                raise jwt.InvalidTokenError('Invalid token type')
            
            user_id = payload.get('user_id')
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Refresh token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Invalid refresh token'
            }), 401
        
        # 检查用户是否存在且活跃
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': 'User not found or inactive'
            }), 401
        
        # 检查刷新令牌是否在黑名单中
        blacklist_key = f"blacklist_token:{refresh_token[:10]}"
        if redis_client.exists(blacklist_key):
            return jsonify({
                'success': False,
                'message': 'Refresh token has been revoked'
            }), 401
        
        # 生成新的访问令牌
        access_token = generate_token(user.id, 'access')
        
        # 可选：生成新的刷新令牌（更安全的做法）
        new_refresh_token = generate_token(
            user.id, 
            'refresh', 
            timedelta(days=current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
        )
        
        # 将旧的刷新令牌加入黑名单
        old_blacklist_key = f"blacklist_token:{refresh_token[:10]}"
        redis_client.set(
            old_blacklist_key, 
            '1', 
            ex=current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30) * 24 * 3600
        )
        
        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'data': {
                'access_token': access_token,
                'refresh_token': new_refresh_token,
                'expires_in': current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1) * 3600,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Token refresh error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Token refresh failed'
        }), 500


@api.route('/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户信息"""
    try:
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'user': current_user.to_dict(include_email=True),
                'roles': [role.name for role in current_user.get_roles()],
                'permissions': [perm.name for perm in current_user.get_permissions()]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Get profile error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve profile'
        }), 500


@api.route('/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """修改密码"""
    try:
        data = request.get_json() or {}
        
        # 验证必需字段
        required_fields = ['current_password', 'new_password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'{field} is required'
                }), 400
        
        # 验证当前密码
        if not current_user.check_password(data['current_password']):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400
        
        # 验证新密码强度
        password_validation = validate_password(data['new_password'])
        if not password_validation['valid']:
            return jsonify({
                'success': False,
                'message': 'Password validation failed',
                'errors': password_validation['errors']
            }), 400
        
        # 检查新密码是否与当前密码相同
        if current_user.check_password(data['new_password']):
            return jsonify({
                'success': False,
                'message': 'New password must be different from current password'
            }), 400
        
        # 更新密码
        current_user.set_password(data['new_password'])
        current_user.password_changed_at = datetime.utcnow()
        db.session.commit()
        
        # 记录密码修改日志
        LoginLog.create_log(
            user_id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            login_type='password_change',
            login_method='web',
            login_result='success',
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent', '')
        )
        
        current_app.logger.info(f'Password changed successfully for user: {current_user.username}')
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Change password error: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to change password'
        }), 500


@api.route('/auth/verify-email', methods=['POST'])
def verify_email():
    """验证邮箱"""
    try:
        data = request.get_json() or {}
        
        if 'email' not in data or 'code' not in data:
            return jsonify({
                'success': False,
                'message': 'Email and verification code are required'
            }), 400
        
        email = sanitize_input(data['email'].lower().strip())
        code = sanitize_input(data['code'].strip())
        
        # 验证邮箱格式
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # 查找用户
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # 检查验证码
        stored_code = get_cached_verification_code(email)
        if not stored_code or stored_code != code:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired verification code'
            }), 400
        
        # 激活用户邮箱
        user.is_verified = True
        user.is_active = True
        user.email_verified_at = datetime.utcnow()
        
        # 删除验证码
        delete_verification_code(email)
        
        db.session.commit()
        
        current_app.logger.info(f'Email verified successfully for user: {user.username}')
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully',
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Email verification error: {e}")
        return jsonify({
            'success': False,
            'message': 'Email verification failed'
        }), 500