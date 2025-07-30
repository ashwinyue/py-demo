import redis
import requests
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify, g
from nacos import NacosClient

# 全局变量
redis_client = None
nacos_client = None

def init_redis(app):
    """初始化Redis客户端"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            password=app.config.get('REDIS_PASSWORD'),
            decode_responses=app.config.get('REDIS_DECODE_RESPONSES', True),
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
        nacos_client = NacosClient(
            server_addresses=app.config['NACOS_SERVER_ADDRESSES'],
            namespace=app.config['NACOS_NAMESPACE'],
            username=app.config.get('NACOS_USERNAME'),
            password=app.config.get('NACOS_PASSWORD')
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
        current_app.logger.warning('Nacos客户端未初始化，跳过服务注册')
        return
    
    try:
        nacos_client.add_naming_instance(
            service_name=current_app.config['SERVICE_NAME'],
            ip=current_app.config['SERVICE_IP'],
            port=current_app.config['SERVICE_PORT'],
            group_name=current_app.config['NACOS_GROUP_NAME'],
            metadata={
                'version': '1.0.0',
                'service_type': 'blog-service',
                'health_check_url': f"http://{current_app.config['SERVICE_IP']}:{current_app.config['SERVICE_PORT']}/healthz"
            }
        )
        current_app.logger.info(f'服务注册成功: {current_app.config["SERVICE_NAME"]}')
    except Exception as e:
        current_app.logger.error(f'服务注册失败: {e}')

def discover_service(service_name):
    """发现服务"""
    if not nacos_client:
        current_app.logger.warning('Nacos客户端未初始化')
        return None
    
    try:
        instances = nacos_client.list_naming_instance(
            service_name=service_name,
            group_name=current_app.config['NACOS_GROUP_NAME']
        )
        
        # 过滤健康的实例
        healthy_instances = [inst for inst in instances['hosts'] if inst['healthy']]
        
        if healthy_instances:
            # 简单的负载均衡：返回第一个健康实例
            instance = healthy_instances[0]
            return f"http://{instance['ip']}:{instance['port']}"
        
        current_app.logger.warning(f'未找到健康的服务实例: {service_name}')
        return None
    
    except Exception as e:
        current_app.logger.error(f'服务发现失败: {e}')
        return None

def call_user_service(endpoint, method='GET', data=None, headers=None, token=None):
    """调用用户服务"""
    # 发现用户服务
    user_service_url = discover_service(current_app.config['USER_SERVICE_NAME'])
    if not user_service_url:
        # 降级处理：使用默认地址
        user_service_url = 'http://localhost:5001'
        current_app.logger.warning(f'使用默认用户服务地址: {user_service_url}')
    
    url = f"{user_service_url}{endpoint}"
    
    # 设置请求头
    request_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'blog-service/1.0.0'
    }
    
    if headers:
        request_headers.update(headers)
    
    if token:
        request_headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data,
            headers=request_headers,
            timeout=current_app.config['USER_SERVICE_TIMEOUT']
        )
        
        current_app.logger.info(f'用户服务调用: {method} {url} -> {response.status_code}')
        
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f'用户服务调用失败: {response.status_code} {response.text}')
            return None
    
    except requests.exceptions.Timeout:
        current_app.logger.error(f'用户服务调用超时: {url}')
        return None
    except requests.exceptions.ConnectionError:
        current_app.logger.error(f'用户服务连接失败: {url}')
        return None
    except Exception as e:
        current_app.logger.error(f'用户服务调用异常: {e}')
        return None

def verify_user_token(token):
    """验证用户令牌"""
    # 首先尝试本地验证JWT
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        
        # 检查令牌是否过期
        if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            return None
        
        return payload
    
    except jwt.ExpiredSignatureError:
        current_app.logger.warning('JWT令牌已过期')
        return None
    except jwt.InvalidTokenError:
        current_app.logger.warning('JWT令牌无效')
        # 如果本地验证失败，尝试调用用户服务验证
        pass
    
    # 调用用户服务验证令牌
    result = call_user_service('/api/auth/verify', method='POST', data={'token': token})
    
    if result and result.get('valid'):
        return result.get('user')
    
    return None

def get_user_info(user_id, token=None):
    """获取用户信息"""
    # 先尝试从缓存获取
    cache_key = f'user_info_{user_id}'
    if redis_client:
        try:
            cached_user = redis_client.get(cache_key)
            if cached_user:
                import json
                return json.loads(cached_user)
        except Exception as e:
            current_app.logger.error(f'Redis缓存读取失败: {e}')
    
    # 从用户服务获取
    result = call_user_service(f'/api/users/{user_id}', token=token)
    
    if result and 'user' in result:
        user_info = result['user']
        
        # 缓存用户信息
        if redis_client:
            try:
                import json
                redis_client.setex(
                    cache_key,
                    current_app.config['CACHE_DEFAULT_TIMEOUT'],
                    json.dumps(user_info)
                )
            except Exception as e:
                current_app.logger.error(f'Redis缓存写入失败: {e}')
        
        return user_info
    
    return None

def token_required(f):
    """令牌验证装饰器 - 简化版本，依赖Tyk进行认证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Tyk已经验证了令牌，我们只需要从请求头中提取用户信息
        token = None
        
        # 从请求头获取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # 由于Tyk已经验证了令牌，我们只需要解码获取用户信息
        try:
            # 不验证签名，因为Tyk已经验证过了
            payload = jwt.decode(token, options={"verify_signature": False})
            user_info = {
                'id': payload.get('user_id'),
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'email': payload.get('email'),
                'is_admin': payload.get('is_admin', False)
            }
            
            # 将用户信息添加到请求上下文
            g.current_user = user_info
            request.current_user_id = user_info.get('id') or user_info.get('user_id')
            request.current_user = user_info
            
        except jwt.DecodeError:
            return jsonify({'error': 'Invalid token format'}), 401
        except Exception as e:
            current_app.logger.error(f"Token processing error: {str(e)}")
            return jsonify({'error': 'Token processing failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not request.current_user.get('is_admin'):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def cache_key_for_posts(page=1, per_page=10, category_id=None, tag_id=None, user_id=None, status='published'):
    """生成文章列表缓存键"""
    key_parts = ['posts', f'page_{page}', f'per_page_{per_page}', f'status_{status}']
    
    if category_id:
        key_parts.append(f'category_{category_id}')
    if tag_id:
        key_parts.append(f'tag_{tag_id}')
    if user_id:
        key_parts.append(f'user_{user_id}')
    
    return ':'.join(key_parts)

def invalidate_posts_cache(post_id=None, user_id=None, category_id=None):
    """清除文章相关缓存"""
    if not redis_client:
        return
    
    try:
        # 清除文章详情缓存
        if post_id:
            redis_client.delete(f'post_{post_id}')
        
        # 清除文章列表缓存（使用模式匹配）
        patterns = ['posts:*']
        
        if user_id:
            patterns.append(f'posts:*user_{user_id}*')
        if category_id:
            patterns.append(f'posts:*category_{category_id}*')
        
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        
        current_app.logger.info('文章缓存清除成功')
    
    except Exception as e:
        current_app.logger.error(f'缓存清除失败: {e}')