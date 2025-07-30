from flask import jsonify, current_app
from app import db
from app.main import bp
from app.models import Post, Category, Tag, Comment
from app.extensions import get_redis_client

@bp.route('/')
def index():
    """博客服务根路径"""
    return jsonify({
        'service': 'blog-service',
        'version': '1.0.0',
        'description': '博客文章管理服务',
        'endpoints': {
            'health': '/healthz',
            'metrics': '/metrics',
            'posts': '/api/posts',
            'categories': '/api/categories',
            'tags': '/api/tags',
            'comments': '/api/comments'
        },
        'status': 'running'
    })

@bp.route('/health')
@bp.route('/healthz')
def health_check():
    """健康检查"""
    health_status = {
        'service': 'blog-service',
        'status': 'healthy',
        'timestamp': current_app.config.get('STARTUP_TIME', 'unknown'),
        'checks': {}
    }
    
    # 检查数据库连接
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # 检查Redis连接
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            health_status['checks']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        else:
            health_status['checks']['redis'] = {
                'status': 'warning',
                'message': 'Redis client not initialized'
            }
    except Exception as e:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
    

    
    # 根据检查结果确定总体状态
    if any(check['status'] == 'unhealthy' for check in health_status['checks'].values()):
        health_status['status'] = 'unhealthy'
        status_code = 503
    elif any(check['status'] == 'warning' for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
        status_code = 200
    else:
        status_code = 200
    
    return jsonify(health_status), status_code

@bp.route('/metrics')
def metrics():
    """服务指标"""
    try:
        # 统计文章数据
        total_posts = Post.query.count()
        published_posts = Post.query.filter_by(status='published').count()
        draft_posts = Post.query.filter_by(status='draft').count()
        
        # 统计分类和标签
        total_categories = Category.query.count()
        total_tags = Tag.query.count()
        
        # 统计评论
        total_comments = Comment.query.count()
        published_comments = Comment.query.filter_by(status='published').count()
        
        # 获取热门文章（按浏览量排序）
        popular_posts = Post.query.filter_by(status='published')\
            .order_by(Post.view_count.desc())\
            .limit(5)\
            .all()
        
        # 获取最新文章
        recent_posts = Post.query.filter_by(status='published')\
            .order_by(Post.published_at.desc())\
            .limit(5)\
            .all()
        
        metrics_data = {
            'service': 'blog-service',
            'statistics': {
                'posts': {
                    'total': total_posts,
                    'published': published_posts,
                    'draft': draft_posts
                },
                'categories': {
                    'total': total_categories
                },
                'tags': {
                    'total': total_tags
                },
                'comments': {
                    'total': total_comments,
                    'published': published_comments
                }
            },
            'popular_posts': [
                {
                    'id': post.id,
                    'title': post.title,
                    'view_count': post.view_count,
                    'like_count': post.like_count
                }
                for post in popular_posts
            ],
            'recent_posts': [
                {
                    'id': post.id,
                    'title': post.title,
                    'published_at': post.published_at.isoformat() if post.published_at else None
                }
                for post in recent_posts
            ]
        }
        
        return jsonify(metrics_data)
    
    except Exception as e:
        current_app.logger.error(f'获取服务指标失败: {e}')
        return jsonify({
            'error': 'Failed to retrieve metrics',
            'message': str(e)
        }), 500

@bp.route('/ready')
def readiness_check():
    """就绪检查"""
    try:
        # 检查数据库是否可用
        db.session.execute('SELECT 1')
        
        return jsonify({
            'service': 'blog-service',
            'status': 'ready',
            'message': 'Service is ready to accept requests'
        })
    
    except Exception as e:
        return jsonify({
            'service': 'blog-service',
            'status': 'not ready',
            'message': f'Service is not ready: {str(e)}'
        }), 503

@bp.route('/live')
def liveness_check():
    """存活检查"""
    return jsonify({
        'service': 'blog-service',
        'status': 'alive',
        'message': 'Service is alive'
    })