from flask import request, jsonify, current_app
from app import db
from app.models import User
from app.api import bp
from app.api.errors import bad_request, not_found
from app.extensions import get_redis_client, token_required, admin_required
import json
from datetime import datetime

@bp.route('/users', methods=['GET'])
@token_required
def get_users():
    """获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', current_app.config['USERS_PER_PAGE'], type=int), 100)
        
        redis_client = get_redis_client()
        cache_key = f'users_page_{page}_per_{per_page}'
        
        # 尝试从Redis缓存获取
        if redis_client:
            cached_users = redis_client.get(cache_key)
            if cached_users:
                return jsonify(json.loads(cached_users))
        
        # 从数据库获取
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = [user.to_dict() for user in users.items]
        
        response_data = {
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }
        
        # 缓存到Redis（5分钟过期）
        if redis_client:
            redis_client.setex(cache_key, 300, json.dumps(response_data))
        
        return jsonify(response_data)
    
    except Exception as e:
        current_app.logger.error(f'获取用户列表失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """创建用户"""
    data = request.get_json() or {}
    
    # 验证必填字段
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('Must include username, email and password fields')
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return bad_request('Username already exists')
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return bad_request('Email already exists')
    
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            is_active=data.get('is_active', True),
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # 清除用户列表缓存
        redis_client = get_redis_client()
        if redis_client:
            for key in redis_client.scan_iter(match='users_page_*'):
                redis_client.delete(key)
        
        current_app.logger.info(f'用户创建成功: {user.username}')
        return jsonify(user.to_dict(include_email=True)), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'用户创建失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """获取用户详情"""
    user = User.query.get(user_id)
    if not user:
        return not_found('User not found')
    
    # 只有管理员或用户本人可以查看详细信息
    current_user = User.query.get(request.current_user_id)
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    include_email = current_user.is_admin or current_user.id == user_id
    return jsonify(user.to_dict(include_email=include_email))

@bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """更新用户信息"""
    user = User.query.get(user_id)
    if not user:
        return not_found('User not found')
    
    # 只有管理员或用户本人可以更新信息
    current_user = User.query.get(request.current_user_id)
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    
    try:
        # 更新用户名
        if 'username' in data and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return bad_request('Username already exists')
            user.username = data['username']
        
        # 更新邮箱
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return bad_request('Email already exists')
            user.email = data['email']
        
        # 更新密码
        if 'password' in data:
            user.set_password(data['password'])
        
        # 只有管理员可以更新这些字段
        if current_user.is_admin:
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'is_admin' in data:
                user.is_admin = data['is_admin']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 清除缓存
        redis_client = get_redis_client()
        if redis_client:
            for key in redis_client.scan_iter(match='users_page_*'):
                redis_client.delete(key)
        
        current_app.logger.info(f'用户更新成功: {user.username}')
        return jsonify(user.to_dict(include_email=True))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'用户更新失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = User.query.get(user_id)
    if not user:
        return not_found('User not found')
    
    # 防止删除管理员账户
    if user.is_admin:
        return jsonify({'error': 'Cannot delete admin user'}), 403
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        # 清除缓存
        redis_client = get_redis_client()
        if redis_client:
            for key in redis_client.scan_iter(match='users_page_*'):
                redis_client.delete(key)
        
        current_app.logger.info(f'用户删除成功: {username}')
        return jsonify({'message': 'User deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'用户删除失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/users/search', methods=['GET'])
@token_required
def search_users():
    """搜索用户"""
    query = request.args.get('q', '').strip()
    if not query:
        return bad_request('Search query is required')
    
    try:
        users = User.query.filter(
            db.or_(
                User.username.contains(query),
                User.email.contains(query)
            )
        ).limit(20).all()
        
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            'users': users_data,
            'total': len(users_data),
            'query': query
        })
    
    except Exception as e:
        current_app.logger.error(f'用户搜索失败: {e}')
        return jsonify({'error': str(e)}), 500