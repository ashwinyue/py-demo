from flask import request, jsonify, current_app, g
from app import db
from app.models import Tag, Post
from app.api import bp
from app.api.errors import bad_request, not_found, forbidden, conflict
from app.extensions import (
    get_redis_client, token_required, admin_required,
    invalidate_posts_cache
)
from datetime import datetime
import json

@bp.route('/tags', methods=['GET'])
def get_tags():
    """获取标签列表"""
    try:
        # 获取查询参数
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'name')  # name, post_count, created_at
        order = request.args.get('order', 'asc')  # asc, desc
        limit = request.args.get('limit', type=int)  # 限制返回数量
        
        # 尝试从缓存获取
        cache_key = f'tags:search_{hash(search)}:sort_{sort_by}_{order}:limit_{limit}'
        redis_client = get_redis_client()
        
        if redis_client and not search:  # 搜索结果不缓存
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    current_app.logger.info(f'从缓存获取标签列表: {cache_key}')
                    return jsonify(json.loads(cached_result))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 构建查询
        query = Tag.query
        
        # 搜索过滤
        if search:
            query = query.filter(Tag.name.contains(search))
        
        # 排序
        if sort_by == 'name':
            sort_column = Tag.name
        elif sort_by == 'post_count':
            sort_column = Tag.post_count
        elif sort_by == 'created_at':
            sort_column = Tag.created_at
        else:
            sort_column = Tag.name
        
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # 限制数量
        if limit:
            query = query.limit(limit)
        
        tags = query.all()
        
        # 构建响应数据
        tags_data = [tag.to_dict() for tag in tags]
        
        result = {
            'tags': tags_data,
            'total': len(tags_data)
        }
        
        # 缓存结果（不缓存搜索结果）
        if redis_client and not search:
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
        current_app.logger.error(f'获取标签列表失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    """获取标签详情"""
    try:
        # 尝试从缓存获取
        cache_key = f'tag_{tag_id}'
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                cached_tag = redis_client.get(cache_key)
                if cached_tag:
                    current_app.logger.info(f'从缓存获取标签详情: {tag_id}')
                    return jsonify(json.loads(cached_tag))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 从数据库获取
        tag = Tag.query.get(tag_id)
        if not tag:
            return not_found('Tag not found')
        
        # 获取最新文章
        recent_posts = tag.posts.filter_by(status='published')\
            .order_by(Post.published_at.desc())\
            .limit(5)\
            .all()
        
        # 构建响应数据
        tag_data = {
            'tag': tag.to_dict(),
            'recent_posts': [
                {
                    'id': post.id,
                    'title': post.title,
                    'summary': post.summary or (post.content[:200] + '...' if len(post.content) > 200 else post.content),
                    'published_at': post.published_at.isoformat() if post.published_at else None
                }
                for post in recent_posts
            ]
        }
        
        # 缓存标签详情
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    current_app.config['CACHE_DEFAULT_TIMEOUT'],
                    json.dumps(tag_data, default=str)
                )
            except Exception as e:
                current_app.logger.error(f'缓存写入失败: {e}')
        
        return jsonify(tag_data)
    
    except Exception as e:
        current_app.logger.error(f'获取标签详情失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags', methods=['POST'])
@token_required
@admin_required
def create_tag():
    """创建标签"""
    data = request.get_json() or {}
    
    # 验证必需字段
    if 'name' not in data:
        return bad_request('Tag name is required')
    
    try:
        # 检查标签名是否已存在
        existing_tag = Tag.query.filter_by(name=data['name']).first()
        if existing_tag:
            return conflict('Tag name already exists')
        
        # 创建标签
        tag = Tag(
            name=data['name'],
            color=data.get('color', '#007bff')
        )
        
        db.session.add(tag)
        db.session.commit()
        
        # 清除标签缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除标签列表缓存
                keys = redis_client.keys('tags:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'标签创建成功: {tag.name}')
        
        return jsonify({
            'message': 'Tag created successfully',
            'tag': tag.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'标签创建失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags/<int:tag_id>', methods=['PUT'])
@token_required
@admin_required
def update_tag(tag_id):
    """更新标签"""
    tag = Tag.query.get(tag_id)
    if not tag:
        return not_found('Tag not found')
    
    data = request.get_json() or {}
    
    try:
        # 检查标签名是否已被其他标签使用
        if 'name' in data and data['name'] != tag.name:
            existing_tag = Tag.query.filter_by(name=data['name']).first()
            if existing_tag:
                return conflict('Tag name already exists')
        
        # 更新标签
        for field in ['name', 'color']:
            if field in data:
                setattr(tag, field, data[field])
        
        db.session.commit()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除标签缓存
                redis_client.delete(f'tag_{tag_id}')
                # 清除标签列表缓存
                keys = redis_client.keys('tags:*')
                if keys:
                    redis_client.delete(*keys)
                # 清除相关文章缓存
                invalidate_posts_cache(tag_id=tag_id)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'标签更新成功: {tag.name}')
        
        return jsonify({
            'message': 'Tag updated successfully',
            'tag': tag.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'标签更新失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_tag(tag_id):
    """删除标签"""
    tag = Tag.query.get(tag_id)
    if not tag:
        return not_found('Tag not found')
    
    try:
        # 检查是否有文章使用此标签
        posts_count = tag.posts.count()
        if posts_count > 0:
            return bad_request(f'Cannot delete tag with {posts_count} posts. Please remove the tag from posts first.')
        
        # 删除标签
        db.session.delete(tag)
        db.session.commit()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除标签缓存
                redis_client.delete(f'tag_{tag_id}')
                # 清除标签列表缓存
                keys = redis_client.keys('tags:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'标签删除成功: {tag_id}')
        
        return jsonify({'message': 'Tag deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'标签删除失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags/<int:tag_id>/posts', methods=['GET'])
def get_tag_posts(tag_id):
    """获取标签下的文章"""
    tag = Tag.query.get(tag_id)
    if not tag:
        return not_found('Tag not found')
    
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', current_app.config['POSTS_PER_PAGE'], type=int),
                      current_app.config['MAX_POSTS_PER_PAGE'])
        
        # 查询标签下的文章
        posts_pagination = tag.posts.filter_by(status='published')\
            .order_by(Post.published_at.desc())\
            .paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
        
        posts = posts_pagination.items
        
        # 构建响应数据
        posts_data = [post.to_dict(include_content=False) for post in posts]
        
        return jsonify({
            'tag': tag.to_dict(),
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
        })
    
    except Exception as e:
        current_app.logger.error(f'获取标签文章失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags/popular', methods=['GET'])
def get_popular_tags():
    """获取热门标签"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # 尝试从缓存获取
        cache_key = f'popular_tags_{limit}'
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    current_app.logger.info(f'从缓存获取热门标签: {cache_key}')
                    return jsonify(json.loads(cached_result))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 查询热门标签（按文章数量排序）
        popular_tags = Tag.query.filter(Tag.post_count > 0)\
            .order_by(Tag.post_count.desc())\
            .limit(limit)\
            .all()
        
        # 构建响应数据
        tags_data = [tag.to_dict() for tag in popular_tags]
        
        result = {
            'tags': tags_data,
            'total': len(tags_data)
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
        current_app.logger.error(f'获取热门标签失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/tags/merge', methods=['POST'])
@token_required
@admin_required
def merge_tags():
    """合并标签"""
    data = request.get_json() or {}
    
    if 'source_tag_id' not in data or 'target_tag_id' not in data:
        return bad_request('Source and target tag IDs are required')
    
    source_tag_id = data['source_tag_id']
    target_tag_id = data['target_tag_id']
    
    if source_tag_id == target_tag_id:
        return bad_request('Source and target tags cannot be the same')
    
    try:
        source_tag = Tag.query.get(source_tag_id)
        target_tag = Tag.query.get(target_tag_id)
        
        if not source_tag:
            return not_found('Source tag not found')
        if not target_tag:
            return not_found('Target tag not found')
        
        # 将源标签的所有文章转移到目标标签
        posts_to_update = source_tag.posts.all()
        
        for post in posts_to_update:
            # 移除源标签
            if source_tag in post.tags:
                post.tags.remove(source_tag)
            
            # 添加目标标签（如果还没有）
            if target_tag not in post.tags:
                post.tags.append(target_tag)
        
        # 删除源标签
        db.session.delete(source_tag)
        
        # 更新目标标签的文章数量
        target_tag.update_post_count()
        
        db.session.commit()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除标签缓存
                redis_client.delete(f'tag_{source_tag_id}')
                redis_client.delete(f'tag_{target_tag_id}')
                # 清除标签列表缓存
                keys = redis_client.keys('tags:*')
                if keys:
                    redis_client.delete(*keys)
                # 清除文章缓存
                invalidate_posts_cache()
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'标签合并成功: {source_tag.name} -> {target_tag.name}')
        
        return jsonify({
            'message': f'Tags merged successfully. {len(posts_to_update)} posts updated.',
            'target_tag': target_tag.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'标签合并失败: {e}')
        return jsonify({'error': str(e)}), 500