import redis
import nacos
import requests
import json
import time
import random
from functools import wraps
from flask import current_app, request, jsonify, g
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import threading
import logging

# 全局变量
redis_client = None
nacos_client = None
service_registry = {}
service_health_status = {}
service_stats = {}
circuit_breakers = {}

def init_redis(app):
    """初始化Redis客户端"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            password=app.config['REDIS_PASSWORD'],
            db=app.config['REDIS_DB'],
            decode_responses=app.config['REDIS_DECODE_RESPONSES'],
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        # 测试连接
        redis_client.ping()
        app.logger.info('Redis连接成功')
    except Exception as e:
        app.logger.error(f'Redis连接失败: {e}')
        redis_client = None

def get_redis_client():
    """获取Redis客户端"""
    return redis_client

def init_nacos(app):
    """初始化Nacos客户端"""
    global nacos_client
    try:
        nacos_client = nacos.NacosClient(
            server_addresses=app.config['NACOS_SERVER'],
            namespace=app.config['NACOS_NAMESPACE'],
            username=app.config['NACOS_USERNAME'],
            password=app.config['NACOS_PASSWORD']
        )
        app.logger.info('Nacos客户端初始化成功')
    except Exception as e:
        app.logger.error(f'Nacos客户端初始化失败: {e}')
        nacos_client = None

def get_nacos_client():
    """获取Nacos客户端"""
    return nacos_client

def register_service():
    """注册服务到Nacos"""
    if not nacos_client:
        return False
    
    try:
        nacos_client.add_naming_instance(
            service_name=current_app.config['SERVICE_NAME'],
            ip=current_app.config['SERVICE_HOST'],
            port=current_app.config['SERVICE_PORT'],
            metadata={
                'version': '1.0.0',
                'service_type': 'api-gateway',
                'startup_time': datetime.utcnow().isoformat()
            }
        )
        current_app.logger.info(f'服务注册成功: {current_app.config["SERVICE_NAME"]}')
        return True
    except Exception as e:
        current_app.logger.error(f'服务注册失败: {e}')
        return False

def discover_service(service_name: str) -> List[Dict]:
    """服务发现"""
    if not nacos_client:
        return []
    
    try:
        # 先从缓存获取
        cache_key = f'service_discovery_{service_name}'
        if redis_client:
            cached_services = redis_client.get(cache_key)
            if cached_services:
                return json.loads(cached_services)
        
        # 从Nacos获取服务实例
        instances = nacos_client.list_naming_instance(service_name)
        
        # 过滤健康的实例
        healthy_instances = [
            {
                'ip': instance['ip'],
                'port': instance['port'],
                'weight': instance.get('weight', 1.0),
                'metadata': instance.get('metadata', {})
            }
            for instance in instances
            if instance.get('healthy', True) and instance.get('enabled', True)
        ]
        
        # 缓存结果
        if redis_client and healthy_instances:
            redis_client.setex(
                cache_key,
                current_app.config['SERVICE_DISCOVERY_CACHE_TTL'],
                json.dumps(healthy_instances)
            )
        
        return healthy_instances
    
    except Exception as e:
        current_app.logger.error(f'服务发现失败 {service_name}: {e}')
        return []

class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy='round_robin'):
        self.strategy = strategy
        self.counters = {}
    
    def select_instance(self, service_name: str, instances: List[Dict]) -> Optional[Dict]:
        """选择服务实例"""
        if not instances:
            return None
        
        if self.strategy == 'round_robin':
            return self._round_robin(service_name, instances)
        elif self.strategy == 'random':
            return self._random(instances)
        elif self.strategy == 'weighted':
            return self._weighted(instances)
        else:
            return instances[0]
    
    def _round_robin(self, service_name: str, instances: List[Dict]) -> Dict:
        """轮询策略"""
        if service_name not in self.counters:
            self.counters[service_name] = 0
        
        instance = instances[self.counters[service_name] % len(instances)]
        self.counters[service_name] += 1
        return instance
    
    def _random(self, instances: List[Dict]) -> Dict:
        """随机策略"""
        return random.choice(instances)
    
    def _weighted(self, instances: List[Dict]) -> Dict:
        """加权策略"""
        total_weight = sum(instance.get('weight', 1.0) for instance in instances)
        if total_weight == 0:
            return instances[0]
        
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for instance in instances:
            current_weight += instance.get('weight', 1.0)
            if r <= current_weight:
                return instance
        
        return instances[-1]

class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """执行函数调用"""
        with self.lock:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception('Circuit breaker is OPEN')
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self):
        """是否应该尝试重置"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def _on_success(self):
        """成功时的处理"""
        with self.lock:
            self.failure_count = 0
            self.state = 'CLOSED'
    
    def _on_failure(self):
        """失败时的处理"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'

def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """获取熔断器"""
    if service_name not in circuit_breakers:
        circuit_breakers[service_name] = CircuitBreaker(
            failure_threshold=current_app.config['CIRCUIT_BREAKER_FAILURE_THRESHOLD'],
            recovery_timeout=current_app.config['CIRCUIT_BREAKER_RECOVERY_TIMEOUT']
        )
    return circuit_breakers[service_name]

# 初始化负载均衡器
load_balancer = LoadBalancer()

def make_service_request(service_name: str, path: str, method='GET', 
                        data=None, headers=None, params=None) -> requests.Response:
    """向后端服务发送请求"""
    # 服务发现
    instances = discover_service(service_name)
    if not instances:
        # 尝试使用备用地址
        fallback_url = current_app.config['BACKEND_SERVICES'].get(
            service_name, {}
        ).get('fallback_url')
        
        if fallback_url:
            url = f"{fallback_url}{path}"
            current_app.logger.warning(f'使用备用地址: {url}')
        else:
            raise Exception(f'Service {service_name} not available')
    else:
        # 负载均衡选择实例
        instance = load_balancer.select_instance(service_name, instances)
        if not instance:
            raise Exception(f'No healthy instance for service {service_name}')
        
        url = f"http://{instance['ip']}:{instance['port']}{path}"
    
    # 获取熔断器
    circuit_breaker = get_circuit_breaker(service_name)
    
    # 准备请求参数
    request_kwargs = {
        'timeout': (
            current_app.config['CONNECT_TIMEOUT'],
            current_app.config['REQUEST_TIMEOUT']
        ),
        'headers': headers or {},
        'params': params
    }
    
    if data:
        if isinstance(data, dict):
            request_kwargs['json'] = data
        else:
            request_kwargs['data'] = data
    
    # 通过熔断器发送请求
    def _make_request():
        return requests.request(method, url, **request_kwargs)
    
    try:
        response = circuit_breaker.call(_make_request)
        
        # 记录成功统计
        _record_service_stats(service_name, 'success')
        
        return response
    
    except Exception as e:
        # 记录失败统计
        _record_service_stats(service_name, 'failure')
        
        current_app.logger.error(f'请求服务失败 {service_name}{path}: {e}')
        raise e

def _record_service_stats(service_name: str, status: str):
    """记录服务统计信息"""
    if service_name not in service_stats:
        service_stats[service_name] = {
            'success_count': 0,
            'failure_count': 0,
            'last_request_time': None
        }
    
    service_stats[service_name][f'{status}_count'] += 1
    service_stats[service_name]['last_request_time'] = datetime.utcnow().isoformat()
    
    # 记录到Redis
    if redis_client:
        try:
            redis_client.hincrby(f'service_stats_{service_name}', f'{status}_count', 1)
            redis_client.hset(
                f'service_stats_{service_name}',
                'last_request_time',
                service_stats[service_name]['last_request_time']
            )
        except Exception as e:
            current_app.logger.error(f'记录服务统计失败: {e}')

def get_service_stats(service_name: str = None) -> Dict:
    """获取服务统计信息"""
    if service_name:
        return service_stats.get(service_name, {})
    return service_stats

def health_check_service(service_name: str) -> bool:
    """健康检查"""
    try:
        service_config = current_app.config['BACKEND_SERVICES'].get(service_name)
        if not service_config:
            return False
        
        health_path = service_config.get('health_check', '/healthz')
        response = make_service_request(service_name, health_path, timeout=5)
        
        is_healthy = response.status_code == 200
        service_health_status[service_name] = {
            'healthy': is_healthy,
            'last_check': datetime.utcnow().isoformat(),
            'status_code': response.status_code
        }
        
        return is_healthy
    
    except Exception as e:
        current_app.logger.error(f'健康检查失败 {service_name}: {e}')
        service_health_status[service_name] = {
            'healthy': False,
            'last_check': datetime.utcnow().isoformat(),
            'error': str(e)
        }
        return False

def get_service_health(service_name: str = None) -> Dict:
    """获取服务健康状态"""
    if service_name:
        return service_health_status.get(service_name, {})
    return service_health_status

def rate_limit_key(identifier: str, window: str = 'hour') -> str:
    """生成限流键"""
    timestamp = int(time.time())
    if window == 'minute':
        window_start = timestamp // 60
    elif window == 'hour':
        window_start = timestamp // 3600
    elif window == 'day':
        window_start = timestamp // 86400
    else:
        window_start = timestamp // 3600
    
    return f'rate_limit_{identifier}_{window}_{window_start}'

def check_rate_limit(identifier: str, limit: int, window: str = 'hour') -> bool:
    """检查限流"""
    if not redis_client:
        return True
    
    try:
        key = rate_limit_key(identifier, window)
        current_count = redis_client.incr(key)
        
        if current_count == 1:
            # 设置过期时间
            if window == 'minute':
                redis_client.expire(key, 60)
            elif window == 'hour':
                redis_client.expire(key, 3600)
            elif window == 'day':
                redis_client.expire(key, 86400)
        
        return current_count <= limit
    
    except Exception as e:
        current_app.logger.error(f'限流检查失败: {e}')
        return True

def rate_limit(limit: str = None):
    """限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 解析限流配置
            rate_limit_config = limit or current_app.config['RATE_LIMIT_DEFAULT']
            parts = rate_limit_config.split(' per ')
            if len(parts) != 2:
                return f(*args, **kwargs)
            
            limit_count = int(parts[0])
            window = parts[1]
            
            # 获取标识符（IP地址或用户ID）
            identifier = request.remote_addr
            if hasattr(g, 'current_user') and g.current_user:
                identifier = f"user_{g.current_user.get('id', identifier)}"
            
            # 检查限流
            if not check_rate_limit(identifier, limit_count, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {rate_limit_config}'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator