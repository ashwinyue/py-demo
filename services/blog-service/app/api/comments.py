from flask import request, jsonify, current_app, g
from app import db
from app.models import Comment, Post
from app.api import bp
from app.api.errors import bad_request, not_found, forbidden
from app.extensions import (
    get_redis_client, token_required, admin_required,
    get_user_info, invalidate_posts_cache
)
from datetime import datetime
import json

@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """获取文章评论列表"""
    post = Post.query.get(post_id)
    if not post:
        return not_found('Post not found')
    
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, like_count
        order = request.args.get('order', 'desc')  # asc, desc
        
        # 尝试从缓存获取
        cache_key = f'post_comments_{post_id}:page_{page}:per_page_{per_page}:sort_{sort_by}_{order}'
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    current_app.logger.info(f'从缓存获取评论列表: {cache_key}')
                    return jsonify(json.loads(cached_result))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 构建查询（只获取顶级评论，回复会在评论详情中包含）
        query = Comment.query.filter_by(
            post_id=post_id,
            parent_id=None,
            status='published'
        )
        
        # 排序
        if sort_by == 'like_count':
            sort_column = Comment.like_count
        else:
            sort_column = Comment.created_at
        
        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # 分页
        comments_pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        comments = comments_pagination.items
        
        # 获取评论者信息
        user_ids = list(set(comment.user_id for comment in comments))
        # 同时获取回复的用户ID
        for comment in comments:
            for reply in comment.replies.filter_by(status='published'):
                user_ids.append(reply.user_id)
        
        user_ids = list(set(user_ids))
        users_info = {}
        
        for user_id in user_ids:
            user_info = get_user_info(user_id)
            if user_info:
                users_info[user_id] = user_info
        
        # 构建响应数据
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict(include_replies=True)
            
            # 添加评论者信息
            if comment.user_id in users_info:
                comment_dict['author'] = users_info[comment.user_id]
            
            # 为回复添加作者信息
            if 'replies' in comment_dict:
                for reply in comment_dict['replies']:
                    if reply['user_id'] in users_info:
                        reply['author'] = users_info[reply['user_id']]
            
            comments_data.append(comment_dict)
        
        result = {
            'post_id': post_id,
            'comments': comments_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': comments_pagination.total,
                'pages': comments_pagination.pages,
                'has_prev': comments_pagination.has_prev,
                'has_next': comments_pagination.has_next,
                'prev_num': comments_pagination.prev_num,
                'next_num': comments_pagination.next_num
            }
        }
        
        # 缓存结果
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    current_app.config['CACHE_DEFAULT_TIMEOUT'],
                    json.dumps(result, default=str)
                )
            except Exception as e:
                current_app.logger.error(f'缓存写入失败: {e}')
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f'获取评论列表失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    """获取评论详情"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return not_found('Comment not found')
        
        # 获取评论者信息
        author_info = get_user_info(comment.user_id)
        
        # 构建响应数据
        comment_data = {
            'comment': comment.to_dict(include_replies=True),
            'author': author_info
        }
        
        # 为回复添加作者信息
        if 'replies' in comment_data['comment']:
            reply_user_ids = [reply['user_id'] for reply in comment_data['comment']['replies']]
            for user_id in set(reply_user_ids):
                user_info = get_user_info(user_id)
                if user_info:
                    for reply in comment_data['comment']['replies']:
                        if reply['user_id'] == user_id:
                            reply['author'] = user_info
        
        return jsonify(comment_data)
    
    except Exception as e:
        current_app.logger.error(f'获取评论详情失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@token_required
def create_comment(post_id):
    """创建评论"""
    post = Post.query.get(post_id)
    if not post:
        return not_found('Post not found')
    
    data = request.get_json() or {}
    
    # 验证必需字段
    if 'content' not in data:
        return bad_request('Comment content is required')
    
    try:
        # 获取当前用户信息
        user_info = g.current_user
        
        # 验证父评论（如果是回复）
        parent_id = data.get('parent_id')
        if parent_id:
            parent_comment = Comment.query.get(parent_id)
            if not parent_comment:
                return bad_request('Parent comment not found')
            if parent_comment.post_id != post_id:
                return bad_request('Parent comment does not belong to this post')
        
        # 创建评论
        comment = Comment(
            content=data['content'],
            post_id=post_id,
            user_id=user_info['id'],
            author_name=user_info.get('username', 'Unknown'),
            parent_id=parent_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # 更新文章评论数
        post.update_comment_count()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除文章评论缓存
                keys = redis_client.keys(f'post_comments_{post_id}:*')
                if keys:
                    redis_client.delete(*keys)
                # 清除文章缓存
                invalidate_posts_cache(post_id=post_id)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'评论创建成功: Post {post_id} by {user_info["username"]}')
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': comment.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'评论创建失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/comments/<int:comment_id>', methods=['PUT'])
@token_required
def update_comment(comment_id):
    """更新评论"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return not_found('Comment not found')
    
    # 检查权限
    user_info = g.current_user
    if comment.user_id != user_info['id'] and not user_info.get('is_admin'):
        return forbidden('You can only edit your own comments')
    
    data = request.get_json() or {}
    
    # 验证必需字段
    if 'content' not in data:
        return bad_request('Comment content is required')
    
    try:
        # 更新评论
        comment.content = data['content']
        comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除文章评论缓存
                keys = redis_client.keys(f'post_comments_{comment.post_id}:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'评论更新成功: {comment_id}')
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'评论更新失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(comment_id):
    """删除评论"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return not_found('Comment not found')
    
    # 检查权限
    user_info = g.current_user
    if comment.user_id != user_info['id'] and not user_info.get('is_admin'):
        return forbidden('You can only delete your own comments')
    
    try:
        post_id = comment.post_id
        
        # 删除评论（级联删除回复）
        db.session.delete(comment)
        db.session.commit()
        
        # 更新文章评论数
        post = Post.query.get(post_id)
        if post:
            post.update_comment_count()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除文章评论缓存
                keys = redis_client.keys(f'post_comments_{post_id}:*')
                if keys:
                    redis_client.delete(*keys)
                # 清除文章缓存
                invalidate_posts_cache(post_id=post_id)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'评论删除成功: {comment_id}')
        
        return jsonify({'message': 'Comment deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'评论删除失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@token_required
def like_comment(comment_id):
    """点赞评论"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return not_found('Comment not found')
    
    try:
        # 检查是否已点赞（使用Redis记录）
        user_id = g.current_user['id']
        redis_client = get_redis_client()
        
        if redis_client:
            like_key = f'comment_like_{comment_id}_{user_id}'
            if redis_client.exists(like_key):
                return jsonify({'message': 'Already liked'}), 400
            
            # 记录点赞
            redis_client.setex(like_key, 86400, '1')  # 24小时过期
        
        # 增加点赞数
        comment.like_count += 1
        db.session.commit()
        
        # 清除相关缓存
        if redis_client:
            try:
                # 清除文章评论缓存
                keys = redis_client.keys(f'post_comments_{comment.post_id}:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        return jsonify({
            'message': 'Comment liked successfully',
            'like_count': comment.like_count
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'评论点赞失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/comments/<int:comment_id>/status', methods=['PUT'])
@token_required
@admin_required
def update_comment_status(comment_id):
    """更新评论状态（管理员功能）"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return not_found('Comment not found')
    
    data = request.get_json() or {}
    
    if 'status' not in data:
        return bad_request('Status is required')
    
    if data['status'] not in ['published', 'hidden', 'deleted']:
        return bad_request('Invalid status. Must be one of: published, hidden, deleted')
    
    try:
        comment.status = data['status']
        comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 更新文章评论数
        post = Post.query.get(comment.post_id)
        if post:
            post.update_comment_count()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除文章评论缓存
                keys = redis_client.keys(f'post_comments_{comment.post_id}:*')
                if keys:
                    redis_client.delete(*keys)
                # 清除文章缓存
                invalidate_posts_cache(post_id=comment.post_id)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'评论状态更新成功: {comment_id} -> {data["status"]}')
        
        return jsonify({
            'message': 'Comment status updated successfully',
            'comment': comment.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'评论状态更新失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/comments', methods=['GET'])
@token_required
@admin_required
def get_all_comments():
    """获取所有评论（管理员功能）"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', 'all')  # all, published, hidden, deleted
        post_id = request.args.get('post_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        # 构建查询
        query = Comment.query
        
        if status != 'all':
            query = query.filter(Comment.status == status)
        
        if post_id:
            query = query.filter(Comment.post_id == post_id)
        
        if user_id:
            query = query.filter(Comment.user_id == user_id)
        
        # 排序
        query = query.order_by(Comment.created_at.desc())
        
        # 分页
        comments_pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        comments = comments_pagination.items
        
        # 获取评论者信息
        user_ids = list(set(comment.user_id for comment in comments))
        users_info = {}
        
        for user_id in user_ids:
            user_info = get_user_info(user_id)
            if user_info:
                users_info[user_id] = user_info
        
        # 构建响应数据
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict(include_replies=False)
            
            # 添加评论者信息
            if comment.user_id in users_info:
                comment_dict['author'] = users_info[comment.user_id]
            
            # 添加文章信息
            if comment.post:
                comment_dict['post'] = {
                    'id': comment.post.id,
                    'title': comment.post.title
                }
            
            comments_data.append(comment_dict)
        
        return jsonify({
            'comments': comments_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': comments_pagination.total,
                'pages': comments_pagination.pages,
                'has_prev': comments_pagination.has_prev,
                'has_next': comments_pagination.has_next,
                'prev_num': comments_pagination.prev_num,
                'next_num': comments_pagination.next_num
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'获取所有评论失败: {e}')
        return jsonify({'error': str(e)}), 500