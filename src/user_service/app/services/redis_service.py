import json
import redis
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from app.core.config import get_settings

settings = get_settings()

class RedisService:
    """Redis服务层"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
    
    def set_cache(self, key: str, value: Any, expire: int = None) -> bool:
        """设置缓存"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                return self.redis_client.setex(key, expire, value)
            else:
                return self.redis_client.set(key, value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def set_user_session(self, user_id: int, session_data: Dict[str, Any], expire: int = None) -> bool:
        """设置用户会话"""
        key = f"user_session:{user_id}"
        if not expire:
            expire = settings.session_expire_seconds
        return self.set_cache(key, session_data, expire)
    
    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户会话"""
        key = f"user_session:{user_id}"
        return self.get_cache(key)
    
    def delete_user_session(self, user_id: int) -> bool:
        """删除用户会话"""
        key = f"user_session:{user_id}"
        return self.delete_cache(key)
    
    def set_verification_code(self, email: str, code: str, expire: int = 300) -> bool:
        """设置验证码（默认5分钟过期）"""
        key = f"verification_code:{email}"
        return self.set_cache(key, code, expire)
    
    def get_verification_code(self, email: str) -> Optional[str]:
        """获取验证码"""
        key = f"verification_code:{email}"
        return self.get_cache(key)
    
    def delete_verification_code(self, email: str) -> bool:
        """删除验证码"""
        key = f"verification_code:{email}"
        return self.delete_cache(key)
    
    def set_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """设置速率限制"""
        key = f"rate_limit:{identifier}"
        try:
            current = self.redis_client.get(key)
            if current is None:
                self.redis_client.setex(key, window, 1)
                return True
            
            current_count = int(current)
            if current_count >= limit:
                return False
            
            self.redis_client.incr(key)
            return True
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            return True  # 如果Redis出错，允许请求通过
    
    def get_rate_limit_count(self, identifier: str) -> int:
        """获取速率限制计数"""
        key = f"rate_limit:{identifier}"
        try:
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            print(f"Redis get rate limit count error: {e}")
            return 0
    
    def blacklist_token(self, token: str, expire: int = None) -> bool:
        """将令牌加入黑名单"""
        key = f"blacklist_token:{token}"
        if not expire:
            expire = settings.access_token_expire_minutes * 60
        return self.set_cache(key, "blacklisted", expire)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        key = f"blacklist_token:{token}"
        return self.exists(key)
    
    def set_user_cache(self, user_id: int, user_data: Dict[str, Any], expire: int = None) -> bool:
        """缓存用户信息"""
        key = f"user_cache:{user_id}"
        if not expire:
            expire = settings.cache_expire_seconds
        return self.set_cache(key, user_data, expire)
    
    def get_user_cache(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取缓存的用户信息"""
        key = f"user_cache:{user_id}"
        return self.get_cache(key)
    
    def delete_user_cache(self, user_id: int) -> bool:
        """删除用户缓存"""
        key = f"user_cache:{user_id}"
        return self.delete_cache(key)
    
    def increment_counter(self, key: str, expire: int = None) -> int:
        """递增计数器"""
        try:
            count = self.redis_client.incr(key)
            if expire and count == 1:  # 第一次设置时添加过期时间
                self.redis_client.expire(key, expire)
            return count
        except Exception as e:
            print(f"Redis increment error: {e}")
            return 0
    
    def get_counter(self, key: str) -> int:
        """获取计数器值"""
        try:
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            print(f"Redis get counter error: {e}")
            return 0
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False

# 全局Redis服务实例
redis_service = RedisService()