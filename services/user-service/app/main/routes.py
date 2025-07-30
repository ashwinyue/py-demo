from flask import jsonify, current_app
from app.main import main as bp
from app.extensions import get_redis_client, get_nacos_client
from datetime import datetime

@bp.route('/')
def index():
    """服务信息"""
    return jsonify({
        'service': 'User Service',
        'version': '1.0.0',
        'description': '用户中心微服务',
        'endpoints': {
            'health': '/healthz',
            'users': '/api/users',
            'auth': '/api/auth'
        },
        'timestamp': datetime.utcnow().isoformat()
    })

@bp.route('/health')
@bp.route('/healthz')
def health_check():
    """健康检查"""
    redis_client = get_redis_client()
    nacos_client = get_nacos_client()
    
    # 检查数据库连接
    db_status = 'connected'
    try:
        from app import db
        db.session.execute('SELECT 1')
    except Exception as e:
        db_status = f'disconnected: {str(e)}'
    
    # 检查Redis连接
    redis_status = 'connected'
    if redis_client:
        try:
            redis_client.ping()
        except Exception as e:
            redis_status = f'disconnected: {str(e)}'
    else:
        redis_status = 'not configured'
    
    # 检查Nacos连接
    nacos_status = 'connected' if nacos_client else 'not configured'
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': {
            'name': current_app.config.get('SERVICE_NAME', 'user-service'),
            'version': '1.0.0'
        },
        'dependencies': {
            'database': db_status,
            'redis': redis_status,
            'nacos': nacos_status
        }
    }
    
    # 如果任何依赖项失败，返回503状态码
    if 'disconnected' in [db_status, redis_status] or nacos_status == 'not configured':
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 503
    
    return jsonify(health_status)

@bp.route('/metrics')
def metrics():
    """服务指标"""
    from app.models import User
    
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        return jsonify({
            'service': 'user-service',
            'metrics': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch metrics',
            'message': str(e)
        }), 500