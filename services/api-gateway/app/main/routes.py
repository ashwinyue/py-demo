from flask import jsonify, current_app
from app.main import bp
from app.extensions import (
    get_redis_client, get_nacos_client, get_service_stats,
    get_service_health, health_check_service, discover_service
)
from datetime import datetime
import psutil
import os

@bp.route('/')
def index():
    """API网关根路径"""
    return jsonify({
        'service': 'API Gateway',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat(),
        'description': 'Microservices API Gateway with service discovery, load balancing, and circuit breaker'
    })

@bp.route('/healthz')
def health_check():
    """健康检查"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # 检查Redis连接
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.ping()
            health_status['checks']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'message': f'Redis connection failed: {e}'
            }
            health_status['status'] = 'unhealthy'
    else:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'message': 'Redis client not initialized'
        }
        health_status['status'] = 'unhealthy'
    
    # 检查Nacos连接
    nacos_client = get_nacos_client()
    if nacos_client:
        try:
            # 尝试获取服务列表来测试连接
            services = nacos_client.list_naming_instance('api-gateway')
            health_status['checks']['nacos'] = {
                'status': 'healthy',
                'message': 'Nacos connection successful'
            }
        except Exception as e:
            health_status['checks']['nacos'] = {
                'status': 'unhealthy',
                'message': f'Nacos connection failed: {e}'
            }
            health_status['status'] = 'unhealthy'
    else:
        health_status['checks']['nacos'] = {
            'status': 'unhealthy',
            'message': 'Nacos client not initialized'
        }
        health_status['status'] = 'unhealthy'
    
    # 检查后端服务健康状态
    backend_services = current_app.config['BACKEND_SERVICES']
    for service_name in backend_services.keys():
        try:
            is_healthy = health_check_service(service_name)
            health_status['checks'][service_name] = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'message': f'{service_name} health check {"passed" if is_healthy else "failed"}'
            }
            if not is_healthy:
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks'][service_name] = {
                'status': 'unhealthy',
                'message': f'{service_name} health check error: {e}'
            }
            health_status['status'] = 'degraded'
    
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'degraded':
        status_code = 200  # 部分服务不可用但网关仍可用
    
    return jsonify(health_status), status_code

@bp.route('/ready')
def readiness_check():
    """就绪检查"""
    ready_status = {
        'status': 'ready',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'API Gateway is ready to serve requests'
    }
    
    # 检查关键组件是否就绪
    redis_client = get_redis_client()
    nacos_client = get_nacos_client()
    
    if not redis_client or not nacos_client:
        ready_status['status'] = 'not_ready'
        ready_status['message'] = 'Critical components not initialized'
        return jsonify(ready_status), 503
    
    return jsonify(ready_status)

@bp.route('/live')
def liveness_check():
    """存活检查"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': datetime.utcnow().isoformat(),
        'message': 'API Gateway is alive'
    })

@bp.route('/metrics')
def metrics():
    """服务指标"""
    try:
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 服务统计
        service_stats = get_service_stats()
        service_health = get_service_health()
        
        # 服务发现统计
        discovery_stats = {}
        backend_services = current_app.config['BACKEND_SERVICES']
        for service_name in backend_services.keys():
            try:
                instances = discover_service(service_name)
                discovery_stats[service_name] = {
                    'instance_count': len(instances),
                    'instances': instances
                }
            except Exception as e:
                discovery_stats[service_name] = {
                    'instance_count': 0,
                    'error': str(e)
                }
        
        # Redis统计
        redis_stats = {}
        redis_client = get_redis_client()
        if redis_client:
            try:
                info = redis_client.info()
                redis_stats = {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except Exception as e:
                redis_stats = {'error': str(e)}
        
        metrics_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'process': {
                    'pid': os.getpid(),
                    'threads': psutil.Process().num_threads()
                }
            },
            'services': {
                'stats': service_stats,
                'health': service_health,
                'discovery': discovery_stats
            },
            'redis': redis_stats,
            'gateway': {
                'version': '1.0.0',
                'config': {
                    'rate_limit_default': current_app.config['RATE_LIMIT_DEFAULT'],
                    'request_timeout': current_app.config['REQUEST_TIMEOUT'],
                    'circuit_breaker_threshold': current_app.config['CIRCUIT_BREAKER_FAILURE_THRESHOLD']
                }
            }
        }
        
        return jsonify(metrics_data)
    
    except Exception as e:
        current_app.logger.error(f'获取指标失败: {e}')
        return jsonify({
            'error': 'Failed to collect metrics',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@bp.route('/services')
def list_services():
    """列出所有服务"""
    try:
        services_info = {}
        backend_services = current_app.config['BACKEND_SERVICES']
        
        for service_name, config in backend_services.items():
            try:
                # 服务发现
                instances = discover_service(service_name)
                
                # 服务统计
                stats = get_service_stats(service_name)
                
                # 健康状态
                health = get_service_health(service_name)
                
                services_info[service_name] = {
                    'config': config,
                    'instances': {
                        'count': len(instances),
                        'details': instances
                    },
                    'stats': stats,
                    'health': health
                }
            except Exception as e:
                services_info[service_name] = {
                    'config': config,
                    'error': str(e)
                }
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'services': services_info
        })
    
    except Exception as e:
        current_app.logger.error(f'获取服务列表失败: {e}')
        return jsonify({
            'error': 'Failed to list services',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@bp.route('/config')
def get_config():
    """获取网关配置信息"""
    try:
        config_info = {
            'service_name': current_app.config['SERVICE_NAME'],
            'service_host': current_app.config['SERVICE_HOST'],
            'service_port': current_app.config['SERVICE_PORT'],
            'rate_limit': {
                'default': current_app.config['RATE_LIMIT_DEFAULT'],
                'per_method': current_app.config['RATE_LIMIT_PER_METHOD']
            },
            'timeouts': {
                'request_timeout': current_app.config['REQUEST_TIMEOUT'],
                'connect_timeout': current_app.config['CONNECT_TIMEOUT']
            },
            'circuit_breaker': {
                'failure_threshold': current_app.config['CIRCUIT_BREAKER_FAILURE_THRESHOLD'],
                'recovery_timeout': current_app.config['CIRCUIT_BREAKER_RECOVERY_TIMEOUT']
            },
            'load_balancer': {
                'strategy': current_app.config['LOAD_BALANCER_STRATEGY']
            },
            'backend_services': current_app.config['BACKEND_SERVICES'],
            'cors': {
                'origins': current_app.config['CORS_ORIGINS'],
                'methods': current_app.config['CORS_METHODS']
            }
        }
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'config': config_info
        })
    
    except Exception as e:
        current_app.logger.error(f'获取配置失败: {e}')
        return jsonify({
            'error': 'Failed to get configuration',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500