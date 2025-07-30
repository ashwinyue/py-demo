from flask import request, jsonify, current_app, g
from app import db
from app.models import Category, Post
from app.api import bp
from app.api.errors import bad_request, not_found, forbidden, conflict
from app.extensions import (
    get_redis_client, token_required, admin_required,
    invalidate_posts_cache
)
from datetime import datetime
import json
import re

def generate_slug(name):
    """生成URL友好的slug"""
    # 转换为小写，替换空格和特殊字符为连字符
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

@bp.route('/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    try:
        # 获取查询参数
        include_posts = request.args.get('include_posts', 'false').lower() == 'true'
        parent_id = request.args.get('parent_id', type=int)
        
        # 尝试从缓存获取
        cache_key = f'categories:include_posts_{include_posts}:parent_{parent_id}'
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    current_app.logger.info(f'从缓存获取分类列表: {cache_key}')
                    return jsonify(json.loads(cached_result))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 构建查询
        query = Category.query
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        
        categories = query.order_by(Category.name).all()
        
        # 构建响应数据
        categories_data = []
        for category in categories:
            category_dict = category.to_dict(include_posts=include_posts)
            
            # 添加子分类
            if not parent_id:  # 只在获取顶级分类时包含子分类
                children = Category.query.filter_by(parent_id=category.id).all()
                category_dict['children'] = [child.to_dict() for child in children]
            
            categories_data.append(category_dict)
        
        result = {
            'categories': categories_data,
            'total': len(categories_data)
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
        current_app.logger.error(f'获取分类列表失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """获取分类详情"""
    try:
        # 尝试从缓存获取
        cache_key = f'category_{category_id}'
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                cached_category = redis_client.get(cache_key)
                if cached_category:
                    current_app.logger.info(f'从缓存获取分类详情: {category_id}')
                    return jsonify(json.loads(cached_category))
            except Exception as e:
                current_app.logger.error(f'缓存读取失败: {e}')
        
        # 从数据库获取
        category = Category.query.get(category_id)
        if not category:
            return not_found('Category not found')
        
        # 获取子分类
        children = Category.query.filter_by(parent_id=category.id).all()
        
        # 获取最新文章
        recent_posts = Post.query.filter_by(
            category_id=category.id,
            status='published'
        ).order_by(Post.published_at.desc()).limit(5).all()
        
        # 构建响应数据
        category_data = {
            'category': category.to_dict(),
            'children': [child.to_dict() for child in children],
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
        
        # 缓存分类详情
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    current_app.config['CACHE_DEFAULT_TIMEOUT'],
                    json.dumps(category_data, default=str)
                )
            except Exception as e:
                current_app.logger.error(f'缓存写入失败: {e}')
        
        return jsonify(category_data)
    
    except Exception as e:
        current_app.logger.error(f'获取分类详情失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/categories', methods=['POST'])
@token_required
@admin_required
def create_category():
    """创建分类"""
    data = request.get_json() or {}
    
    # 验证必需字段
    if 'name' not in data:
        return bad_request('Category name is required')
    
    try:
        # 检查分类名是否已存在
        existing_category = Category.query.filter_by(name=data['name']).first()
        if existing_category:
            return conflict('Category name already exists')
        
        # 生成slug
        slug = data.get('slug') or generate_slug(data['name'])
        
        # 检查slug是否已存在
        existing_slug = Category.query.filter_by(slug=slug).first()
        if existing_slug:
            return conflict('Category slug already exists')
        
        # 验证父分类
        parent_id = data.get('parent_id')
        if parent_id:
            parent_category = Category.query.get(parent_id)
            if not parent_category:
                return bad_request('Parent category not found')
        
        # 创建分类
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            slug=slug,
            parent_id=parent_id
        )
        
        db.session.add(category)
        db.session.commit()
        
        # 清除分类缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除分类列表缓存
                keys = redis_client.keys('categories:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'分类创建成功: {category.name}')
        
        return jsonify({
            'message': 'Category created successfully',
            'category': category.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'分类创建失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/categories/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_category(category_id):
    """更新分类"""
    category = Category.query.get(category_id)
    if not category:
        return not_found('Category not found')
    
    data = request.get_json() or {}
    
    try:
        # 检查分类名是否已被其他分类使用
        if 'name' in data and data['name'] != category.name:
            existing_category = Category.query.filter_by(name=data['name']).first()
            if existing_category:
                return conflict('Category name already exists')
        
        # 检查slug是否已被其他分类使用
        if 'slug' in data and data['slug'] != category.slug:
            existing_slug = Category.query.filter_by(slug=data['slug']).first()
            if existing_slug:
                return conflict('Category slug already exists')
        
        # 验证父分类
        if 'parent_id' in data:
            parent_id = data['parent_id']
            if parent_id:
                # 检查是否会形成循环引用
                if parent_id == category.id:
                    return bad_request('Category cannot be its own parent')
                
                parent_category = Category.query.get(parent_id)
                if not parent_category:
                    return bad_request('Parent category not found')
                
                # 检查是否会形成循环引用（深度检查）
                current_parent = parent_category
                while current_parent:
                    if current_parent.id == category.id:
                        return bad_request('Circular reference detected')
                    current_parent = current_parent.parent
        
        # 更新分类
        for field in ['name', 'description', 'slug', 'parent_id']:
            if field in data:
                setattr(category, field, data[field])
        
        # 如果没有提供slug但更新了name，重新生成slug
        if 'name' in data and 'slug' not in data:
            new_slug = generate_slug(data['name'])
            if new_slug != category.slug:
                existing_slug = Category.query.filter_by(slug=new_slug).first()
                if not existing_slug:
                    category.slug = new_slug
        
        category.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除分类缓存
                redis_client.delete(f'category_{category_id}')
                # 清除分类列表缓存
                keys = redis_client.keys('categories:*')
                if keys:
                    redis_client.delete(*keys)
                # 清除相关文章缓存
                invalidate_posts_cache(category_id=category_id)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'分类更新成功: {category.name}')
        
        return jsonify({
            'message': 'Category updated successfully',
            'category': category.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'分类更新失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_category(category_id):
    """删除分类"""
    category = Category.query.get(category_id)
    if not category:
        return not_found('Category not found')
    
    try:
        # 检查是否有文章使用此分类
        posts_count = Post.query.filter_by(category_id=category_id).count()
        if posts_count > 0:
            return bad_request(f'Cannot delete category with {posts_count} posts. Please move or delete the posts first.')
        
        # 检查是否有子分类
        children_count = Category.query.filter_by(parent_id=category_id).count()
        if children_count > 0:
            return bad_request(f'Cannot delete category with {children_count} subcategories. Please move or delete the subcategories first.')
        
        # 删除分类
        db.session.delete(category)
        db.session.commit()
        
        # 清除相关缓存
        redis_client = get_redis_client()
        if redis_client:
            try:
                # 清除分类缓存
                redis_client.delete(f'category_{category_id}')
                # 清除分类列表缓存
                keys = redis_client.keys('categories:*')
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                current_app.logger.error(f'缓存清除失败: {e}')
        
        current_app.logger.info(f'分类删除成功: {category_id}')
        
        return jsonify({'message': 'Category deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'分类删除失败: {e}')
        return jsonify({'error': str(e)}), 500

@bp.route('/categories/<int:category_id>/posts', methods=['GET'])
def get_category_posts(category_id):
    """获取分类下的文章"""
    category = Category.query.get(category_id)
    if not category:
        return not_found('Category not found')
    
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', current_app.config['POSTS_PER_PAGE'], type=int),
                      current_app.config['MAX_POSTS_PER_PAGE'])
        
        # 查询分类下的文章
        posts_pagination = Post.query.filter_by(
            category_id=category_id,
            status='published'
        ).order_by(Post.published_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        posts = posts_pagination.items
        
        # 构建响应数据
        posts_data = [post.to_dict(include_content=False) for post in posts]
        
        return jsonify({
            'category': category.to_dict(),
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
        current_app.logger.error(f'获取分类文章失败: {e}')
        return jsonify({'error': str(e)}), 500