from flask import request, jsonify, current_app, g
from sqlalchemy import or_, and_
from app import db
from app.models import Post, Category, Tag, Comment
from app.api import bp
from app.api.errors import bad_request, not_found, forbidden
from app.extensions import (
    get_redis_client, token_required, admin_required,
    get_user_info, cache_key_for_posts, invalidate_posts_cache
)
from datetime import datetime
import json

@bp.route('/posts', methods=['GET'])
def get_posts():
    """获取文章列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', current_app.config['POSTS_PER_PAGE'], type=int),
                      current_app.config['MAX_POSTS_PER_PAGE'])
        
        category_id = request.args.get('category_id', type=int)
        tag_id = request.args.get('tag_id', type=int)
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status', 'published')
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, updated_at, view_count, like_count
        order = request.args.get('order', 'desc')  # asc, desc
        
        # 生成缓存键
        cache_key = cache_key_for_posts(page, per_page, category_id, tag_id, user_id, status)
        if search:
            cache_key += f':search_{hash(search)}'
        cache_key += f':sort_{sort_by}_{order}'
        
        # 尝试从缓存获取
        redis_client = get_redis_client()
        if redis_client and not search:  # 搜索结果不缓存
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    current_app.logger.info(f'从缓存获取文章列表: {cache_key}')
                    return jsonify(json.loads(cached_result))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 构建查询
        query = Post.query
        
        # 状态过滤
        if status != 'all':
            query = query.filter(Post.status == status)
        
        # 分类过滤
        if category_id:
            query = query.filter(Post.category_id == category_id)
        
        # 标签过滤
        if tag_id:
            query = query.join(Post.tags).filter(Tag.id == tag_id)
        
        # 用户过滤
        if user_id:
            query = query.filter(Post.user_id == user_id)
        
        # 搜索过滤
        if search:
            search_filter = or_(
                Post.title.contains(search),
                Post.content.contains(search),
                Post.summary.contains(search)
            )
            query = query.filter(search_filter)
        
        # 排序
        if sort_by == 'created_at':
            sort_column = Post.created_at
        elif sort_by == 'updated_at':
            sort_column = Post.updated_at
        elif sort_by == 'view_count':
            sort_column = Post.view_count
        elif sort_by == 'like_count':
            sort_column = Post.like_count
        elif sort_by == 'published_at':
            sort_column = Post.published_at
        else:
            sort_column = Post.created_at
        
        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # 分页
        posts_pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        posts = posts_pagination.items
        
        # 获取作者信息
        user_ids = list(set(post.user_id for post in posts))
        users_info = {}
        
        for user_id in user_ids:
            user_info = get_user_info(user_id)
            if user_info:
                users_info[user_id] = user_info
        
        # 构建响应数据
        posts_data = []
        for post in posts:
            post_dict = post.to_dict(include_content=False)
            
            # 添加作者信息
            if post.user_id in users_info:
                post_dict['author'] = users_info[post.user_id]
            
            posts_data.append(post_dict)
        
        result = {
            'posts': posts_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': posts_pagination.total,
                'pages': posts_pagination.pages,
                'has_prev': posts_pagination.has_prev,
                'has_next': posts_pagination.has_next,
                'prev_num': posts_pagination.prev_num,
                'next_num': posts_pagination.next_num
            }
        }
        
        # 缓存结果（不缓存搜索结果）
        if redis_client and not search:
            try:
                redis_client.setex(
                    cache_key,
                    current_app.config['CACHE_POSTS_TIMEOUT'],
                    json.dumps(result, default=str)
                )
            except Exception as e:
                current_app.logger.error(f'缓存写入失败: {e}')
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f'获取文章列表失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """获取文章详情"""
    try:
        # 尝试从缓存获取
        cache_key = f'post_{post_id}'
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                cached_post = redis_client.get(cache_key)
                if cached_post:
                    post_data = json.loads(cached_post)
                    # 增加浏览量（异步更新）
                    post = Post.query.get(post_id)
                    if post:
                        post.increment_view()
                    
                    current_app.logger.info(f'从缓存获取文章详情: {post_id}')
                    return jsonify(post_data)
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 从数据库获取
        post = Post.query.get(post_id)
        if not post:
            return not_found('Post not found')
        
        # 增加浏览量
        post.increment_view()
        
        # 获取作者信息
        author_info = get_user_info(post.user_id)
        
        # 构建响应数据
        post_data = {
            'post': post.to_dict(include_content=True),
            'author': author_info
        }
        
        # 缓存文章详情
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    current_app.config['CACHE_POSTS_TIMEOUT'],
                    json.dumps(post_data, default=str)
                )
            except Exception as e:
                current_app.logger.error(f'缓存写入失败: {e}')
        
        return jsonify(post_data)
    
    except Exception as e:
        current_app.logger.error(f'获取文章详情失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/posts', methods=['POST'])
@token_required
def create_post():
    """创建文章"""
    data = request.get_json() or {}
    
    # 验证必需字段
    if 'title' not in data or 'content' not in data:
        return bad_request('Title and content are required')
    
    try:
        # 获取当前用户信息
        user_info = g.current_user
        
        # 创建文章
        post = Post()
        post.from_dict(data, new_post=True)
        post.user_id = user_info['id']
        post.author_name = user_info.get('username', 'Unknown')
        
        # 处理分类
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return bad_request('Category not found')
        
        # 处理标签
        if 'tags' in data:
            tag_names = data['tags']
            if isinstance(tag_names, list):
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)
        
        db.session.add(post)
        db.session.commit()
        
        # 更新分类文章数
        if post.category:
            post.category.update_post_count()
        
        # 更新标签文章数
        for tag in post.tags:
            tag.update_post_count()
        
        # 清除相关缓存
        invalidate_posts_cache(post_id=post.id, user_id=post.user_id, category_id=post.category_id)
        
        current_app.logger.info(f'文章创建成功: {post.title} by {user_info["username"]}')
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'文章创建失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_post(post_id):
    """更新文章"""
    post = Post.query.get(post_id)
    if not post:
        return not_found('Post not found')
    
    # 检查权限
    user_info = g.current_user
    if post.user_id != user_info['id'] and not user_info.get('is_admin'):
        return forbidden('You can only edit your own posts')
    
    data = request.get_json() or {}
    
    try:
        old_category_id = post.category_id
        
        # 更新文章
        post.from_dict(data)
        
        # 处理分类变更
        if 'category_id' in data and data['category_id'] != old_category_id:
            if data['category_id']:
                category = Category.query.get(data['category_id'])
                if not category:
                    return bad_request('Category not found')
        
        # 处理标签更新
        if 'tags' in data:
            # 清除现有标签
            post.tags.clear()
            
            # 添加新标签
            tag_names = data['tags']
            if isinstance(tag_names, list):
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 更新分类文章数
        if old_category_id:
            old_category = Category.query.get(old_category_id)
            if old_category:
                old_category.update_post_count()
        
        if post.category:
            post.category.update_post_count()
        
        # 更新标签文章数
        for tag in post.tags:
            tag.update_post_count()
        
        # 清除相关缓存
        invalidate_posts_cache(post_id=post.id, user_id=post.user_id, category_id=post.category_id)
        if old_category_id != post.category_id:
            invalidate_posts_cache(category_id=old_category_id)
        
        current_app.logger.info(f'文章更新成功: {post.title}')
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': post.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'文章更新失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(post_id):
    """删除文章"""
    post = Post.query.get(post_id)
    if not post:
        return not_found('Post not found')
    
    # 检查权限
    user_info = g.current_user
    if post.user_id != user_info['id'] and not user_info.get('is_admin'):
        return forbidden('You can only delete your own posts')
    
    try:
        category_id = post.category_id
        user_id = post.user_id
        
        # 删除文章（级联删除评论）
        db.session.delete(post)
        db.session.commit()
        
        # 更新分类文章数
        if category_id:
            category = Category.query.get(category_id)
            if category:
                category.update_post_count()
        
        # 更新标签文章数
        for tag in Tag.query.all():
            tag.update_post_count()
        
        # 清除相关缓存
        invalidate_posts_cache(post_id=post_id, user_id=user_id, category_id=category_id)
        
        current_app.logger.info(f'文章删除成功: {post_id}')
        
        return jsonify({'message': 'Post deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'文章删除失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/posts/<int:post_id>/like', methods=['POST'])
@token_required
def like_post(post_id):
    """点赞文章"""
    post = Post.query.get(post_id)
    if not post:
        return not_found('Post not found')
    
    try:
        # 检查是否已点赞（使用Redis记录）
        user_id = g.current_user['id']
        redis_client = get_redis_client()
        
        if redis_client:
            like_key = f'post_like_{post_id}_{user_id}'
            if redis_client.exists(like_key):
                return jsonify({'message': 'Already liked'}), 400
            
            # 记录点赞
            redis_client.setex(like_key, 86400, '1')  # 24小时过期
        
        # 增加点赞数
        post.increment_like()
        
        # 清除文章缓存
        invalidate_posts_cache(post_id=post_id)
        
        return jsonify({
            'message': 'Post liked successfully',
            'like_count': post.like_count
        })
    
    except Exception as e:
        current_app.logger.error(f'文章点赞失败: {e}')
        return jsonify({'error': str(e)}), 500