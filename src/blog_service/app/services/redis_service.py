import redis
import requests
from typing import Optional
from functools import lru_cache
import json
import hashlib
from app.core.config import get_settings

# Redis客户端实例
_redis_client: Optional[redis.Redis] = None

def init_redis() -> None:
    """初始化Redis连接"""
    global _redis_client
    settings = get_settings()
    
    try:
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        # 测试连接
        _redis_client.ping()
        print(f"Redis连接成功: {settings.redis_host}:{settings.redis_port}")
    except Exception as e:
        print(f"Redis连接失败: {e}")
        _redis_client = None

def get_redis_client() -> Optional[redis.Redis]:
    """获取Redis客户端"""
    return _redis_client

# 缓存相关函数
def cache_key_for_posts(page: int, per_page: int, user_id: Optional[int] = None, 
                       status: str = 'published', search: Optional[str] = None,
                       sort_by: str = 'created_at', order: str = 'desc') -> str:
    """生成文章列表缓存键"""
    key_parts = [f"posts:page_{page}:per_page_{per_page}:status_{status}"]
    
    if user_id:
        key_parts.append(f"user_{user_id}")
    
    if search:
        search_hash = hashlib.md5(search.encode()).hexdigest()[:8]
        key_parts.append(f"search_{search_hash}")
    
    key_parts.append(f"sort_{sort_by}_{order}")
    
    return ":".join(key_parts)

def invalidate_posts_cache() -> None:
    """清除文章相关缓存"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            # 获取所有文章相关的缓存键
            keys = redis_client.keys("posts:*")
            if keys:
                redis_client.delete(*keys)
                print(f"清除了 {len(keys)} 个文章缓存")
        except Exception as e:
            print(f"清除缓存失败: {e}")

def cache_post_data(key: str, data: dict, timeout: Optional[int] = None) -> None:
    """缓存文章数据"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            settings = get_settings()
            timeout = timeout or settings.cache_timeout
            redis_client.setex(key, timeout, json.dumps(data, default=str))
        except Exception as e:
            print(f"缓存数据失败: {e}")

def get_cached_post_data(key: str) -> Optional[dict]:
    """获取缓存的文章数据"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            cached_data = redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"获取缓存数据失败: {e}")
    return None

# 用户服务相关函数
@lru_cache(maxsize=1000)
def get_user_info(user_id: int) -> Optional[dict]:
    """从用户服务获取用户信息（带缓存）"""
    settings = get_settings()
    
    try:
        response = requests.get(
            f"{settings.user_service_url}/api/users/{user_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"获取用户信息失败: {e}")
    
    return None

def verify_user_token(token: str) -> Optional[dict]:
    """验证用户令牌"""
    settings = get_settings()
    
    try:
        response = requests.post(
            f"{settings.user_service_url}/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"验证用户令牌失败: {e}")
    
    return None

# JWT相关函数（如果需要本地验证）
import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict) -> str:
    """创建访问令牌"""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str) -> Optional[dict]:
    """验证访问令牌"""
    settings = get_settings()
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.PyJWTError:
        return None

# 统计相关函数
def increment_post_view(post_id: int) -> None:
    """增加文章浏览次数（Redis计数）"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.incr(f"post_views:{post_id}")
        except Exception as e:
            print(f"增加浏览次数失败: {e}")

def increment_post_view_count(post_id: int) -> int:
    """增加文章浏览次数并返回新的计数"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            return redis_client.incr(f"post_views:{post_id}")
        except Exception as e:
            print(f"增加浏览次数失败: {e}")
    return 0

def increment_post_like(post_id: int) -> int:
    """增加文章点赞次数（Redis计数）"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            return redis_client.incr(f"post_likes:{post_id}")
        except Exception as e:
            print(f"增加点赞次数失败: {e}")
    return 0

def increment_post_like_count(post_id: int) -> int:
    """增加文章点赞次数并返回新的计数"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            return redis_client.incr(f"post_likes:{post_id}")
        except Exception as e:
            print(f"增加点赞次数失败: {e}")
    return 0

def get_post_view_count(post_id: int) -> int:
    """获取文章浏览次数"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            views = redis_client.get(f"post_views:{post_id}")
            return int(views) if views else 0
        except Exception as e:
            print(f"获取浏览次数失败: {e}")
    return 0

def get_post_like_count(post_id: int) -> int:
    """获取文章点赞次数"""
    redis_client = get_redis_client()
    if redis_client:
        try:
            likes = redis_client.get(f"post_likes:{post_id}")
            return int(likes) if likes else 0
        except Exception as e:
            print(f"获取点赞次数失败: {e}")
    return 0

def get_post_stats(post_id: int) -> dict:
    """获取文章统计信息"""
    redis_client = get_redis_client()
    stats = {"views": 0, "likes": 0}
    
    if redis_client:
        try:
            views = redis_client.get(f"post_views:{post_id}")
            likes = redis_client.get(f"post_likes:{post_id}")
            
            stats["views"] = int(views) if views else 0
            stats["likes"] = int(likes) if likes else 0
        except Exception as e:
            print(f"获取文章统计失败: {e}")
    
    return stats