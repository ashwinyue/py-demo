# -*- coding: utf-8 -*-
"""
缓存工具函数
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app
from app.extensions import redis_client


class CacheManager:
    """
    缓存管理器
    """
    
    def __init__(self, redis_client=None, default_timeout=3600):
        self.redis_client = redis_client or redis_client
        self.default_timeout = default_timeout
    
    def _make_key(self, key: str, prefix: str = None) -> str:
        """
        生成缓存键
        
        Args:
            key: 原始键
            prefix: 前缀
            
        Returns:
            str: 完整的缓存键
        """
        if prefix:
            return f"{prefix}:{key}"
        return key
    
    def set(self, key: str, value: Any, timeout: int = None, prefix: str = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒）
            prefix: 键前缀
            
        Returns:
            bool: 是否成功
        """
        try:
            cache_key = self._make_key(key, prefix)
            timeout = timeout or self.default_timeout
            
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (int, float, str, bool)):
                serialized_value = str(value)
            else:
                # 使用pickle序列化复杂对象
                serialized_value = pickle.dumps(value)
            
            return self.redis_client.setex(cache_key, timeout, serialized_value)
        except Exception as e:
            current_app.logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, key: str, prefix: str = None, default: Any = None) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            prefix: 键前缀
            default: 默认值
            
        Returns:
            Any: 缓存值
        """
        try:
            cache_key = self._make_key(key, prefix)
            value = self.redis_client.get(cache_key)
            
            if value is None:
                return default
            
            # 尝试反序列化
            try:
                # 先尝试JSON反序列化
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    # 再尝试pickle反序列化
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # 最后返回字符串
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            current_app.logger.error(f"Cache get error: {e}")
            return default
    
    def delete(self, key: str, prefix: str = None) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            bool: 是否成功
        """
        try:
            cache_key = self._make_key(key, prefix)
            return bool(self.redis_client.delete(cache_key))
        except Exception as e:
            current_app.logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str, prefix: str = None) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            bool: 是否存在
        """
        try:
            cache_key = self._make_key(key, prefix)
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            current_app.logger.error(f"Cache exists error: {e}")
            return False
    
    def expire(self, key: str, timeout: int, prefix: str = None) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            timeout: 过期时间（秒）
            prefix: 键前缀
            
        Returns:
            bool: 是否成功
        """
        try:
            cache_key = self._make_key(key, prefix)
            return bool(self.redis_client.expire(cache_key, timeout))
        except Exception as e:
            current_app.logger.error(f"Cache expire error: {e}")
            return False
    
    def ttl(self, key: str, prefix: str = None) -> int:
        """
        获取缓存剩余过期时间
        
        Args:
            key: 缓存键
            prefix: 键前缀
            
        Returns:
            int: 剩余时间（秒），-1表示永不过期，-2表示不存在
        """
        try:
            cache_key = self._make_key(key, prefix)
            return self.redis_client.ttl(cache_key)
        except Exception as e:
            current_app.logger.error(f"Cache ttl error: {e}")
            return -2
    
    def increment(self, key: str, amount: int = 1, prefix: str = None) -> int:
        """
        递增缓存值
        
        Args:
            key: 缓存键
            amount: 递增量
            prefix: 键前缀
            
        Returns:
            int: 递增后的值
        """
        try:
            cache_key = self._make_key(key, prefix)
            return self.redis_client.incrby(cache_key, amount)
        except Exception as e:
            current_app.logger.error(f"Cache increment error: {e}")
            return 0
    
    def decrement(self, key: str, amount: int = 1, prefix: str = None) -> int:
        """
        递减缓存值
        
        Args:
            key: 缓存键
            amount: 递减量
            prefix: 键前缀
            
        Returns:
            int: 递减后的值
        """
        try:
            cache_key = self._make_key(key, prefix)
            return self.redis_client.decrby(cache_key, amount)
        except Exception as e:
            current_app.logger.error(f"Cache decrement error: {e}")
            return 0
    
    def get_many(self, keys: List[str], prefix: str = None) -> Dict[str, Any]:
        """
        批量获取缓存
        
        Args:
            keys: 缓存键列表
            prefix: 键前缀
            
        Returns:
            Dict: 键值对字典
        """
        try:
            cache_keys = [self._make_key(key, prefix) for key in keys]
            values = self.redis_client.mget(cache_keys)
            
            result = {}
            for i, key in enumerate(keys):
                value = values[i]
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            result[key] = pickle.loads(value)
                        except (pickle.PickleError, TypeError):
                            result[key] = value.decode('utf-8') if isinstance(value, bytes) else value
            
            return result
        except Exception as e:
            current_app.logger.error(f"Cache get_many error: {e}")
            return {}
    
    def set_many(self, mapping: Dict[str, Any], timeout: int = None, prefix: str = None) -> bool:
        """
        批量设置缓存
        
        Args:
            mapping: 键值对字典
            timeout: 过期时间（秒）
            prefix: 键前缀
            
        Returns:
            bool: 是否成功
        """
        try:
            timeout = timeout or self.default_timeout
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                cache_key = self._make_key(key, prefix)
                
                # 序列化值
                if isinstance(value, (dict, list, tuple)):
                    serialized_value = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, (int, float, str, bool)):
                    serialized_value = str(value)
                else:
                    serialized_value = pickle.dumps(value)
                
                pipe.setex(cache_key, timeout, serialized_value)
            
            pipe.execute()
            return True
        except Exception as e:
            current_app.logger.error(f"Cache set_many error: {e}")
            return False
    
    def delete_many(self, keys: List[str], prefix: str = None) -> int:
        """
        批量删除缓存
        
        Args:
            keys: 缓存键列表
            prefix: 键前缀
            
        Returns:
            int: 删除的数量
        """
        try:
            cache_keys = [self._make_key(key, prefix) for key in keys]
            return self.redis_client.delete(*cache_keys)
        except Exception as e:
            current_app.logger.error(f"Cache delete_many error: {e}")
            return 0
    
    def clear_pattern(self, pattern: str, prefix: str = None) -> int:
        """
        根据模式清除缓存
        
        Args:
            pattern: 匹配模式
            prefix: 键前缀
            
        Returns:
            int: 删除的数量
        """
        try:
            search_pattern = self._make_key(pattern, prefix)
            keys = self.redis_client.keys(search_pattern)
            
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            current_app.logger.error(f"Cache clear_pattern error: {e}")
            return 0


# 创建全局缓存管理器实例
cache_manager = CacheManager()


# 便捷函数
def cache_set(key: str, value: Any, timeout: int = None, prefix: str = None) -> bool:
    """设置缓存"""
    return cache_manager.set(key, value, timeout, prefix)


def cache_get(key: str, prefix: str = None, default: Any = None) -> Any:
    """获取缓存"""
    return cache_manager.get(key, prefix, default)


def cache_delete(key: str, prefix: str = None) -> bool:
    """删除缓存"""
    return cache_manager.delete(key, prefix)


def cache_exists(key: str, prefix: str = None) -> bool:
    """检查缓存是否存在"""
    return cache_manager.exists(key, prefix)


def cache_clear_user(user_id: int) -> int:
    """
    清除用户相关的所有缓存
    
    Args:
        user_id: 用户ID
        
    Returns:
        int: 删除的缓存数量
    """
    patterns = [
        f"user:{user_id}:*",
        f"user_profile:{user_id}",
        f"user_permissions:{user_id}",
        f"user_roles:{user_id}",
        f"user_sessions:{user_id}:*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        total_deleted += cache_manager.clear_pattern(pattern)
    
    return total_deleted


def cache_user_profile(user_id: int, profile_data: Dict[str, Any], timeout: int = 1800) -> bool:
    """
    缓存用户资料
    
    Args:
        user_id: 用户ID
        profile_data: 用户资料数据
        timeout: 过期时间（秒）
        
    Returns:
        bool: 是否成功
    """
    return cache_set(f"user_profile:{user_id}", profile_data, timeout)


def get_cached_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    获取缓存的用户资料
    
    Args:
        user_id: 用户ID
        
    Returns:
        Optional[Dict]: 用户资料数据
    """
    return cache_get(f"user_profile:{user_id}")


def cache_user_permissions(user_id: int, permissions: List[str], timeout: int = 3600) -> bool:
    """
    缓存用户权限
    
    Args:
        user_id: 用户ID
        permissions: 权限列表
        timeout: 过期时间（秒）
        
    Returns:
        bool: 是否成功
    """
    return cache_set(f"user_permissions:{user_id}", permissions, timeout)


def get_cached_user_permissions(user_id: int) -> Optional[List[str]]:
    """
    获取缓存的用户权限
    
    Args:
        user_id: 用户ID
        
    Returns:
        Optional[List]: 权限列表
    """
    return cache_get(f"user_permissions:{user_id}")


def cache_verification_code(identifier: str, code: str, timeout: int = 300) -> bool:
    """
    缓存验证码
    
    Args:
        identifier: 标识符（邮箱或手机号）
        code: 验证码
        timeout: 过期时间（秒）
        
    Returns:
        bool: 是否成功
    """
    return cache_set(f"verification_code:{identifier}", code, timeout)


def get_cached_verification_code(identifier: str) -> Optional[str]:
    """
    获取缓存的验证码
    
    Args:
        identifier: 标识符（邮箱或手机号）
        
    Returns:
        Optional[str]: 验证码
    """
    return cache_get(f"verification_code:{identifier}")


def delete_verification_code(identifier: str) -> bool:
    """
    删除验证码缓存
    
    Args:
        identifier: 标识符（邮箱或手机号）
        
    Returns:
        bool: 是否成功
    """
    return cache_delete(f"verification_code:{identifier}")


def cache_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    缓存速率限制
    
    Args:
        key: 限制键
        limit: 限制次数
        window: 时间窗口（秒）
        
    Returns:
        bool: 是否超出限制
    """
    try:
        current_count = cache_manager.increment(f"rate_limit:{key}")
        
        if current_count == 1:
            # 第一次访问，设置过期时间
            cache_manager.expire(f"rate_limit:{key}", window)
        
        return current_count > limit
    except Exception as e:
        current_app.logger.error(f"Rate limit cache error: {e}")
        return False


def get_rate_limit_remaining(key: str, limit: int) -> int:
    """
    获取速率限制剩余次数
    
    Args:
        key: 限制键
        limit: 限制次数
        
    Returns:
        int: 剩余次数
    """
    try:
        current_count = cache_get(f"rate_limit:{key}", default=0)
        return max(0, limit - int(current_count))
    except Exception:
        return limit


def cache_blacklist_token(token: str, timeout: int = None) -> bool:
    """
    将令牌加入黑名单缓存
    
    Args:
        token: JWT令牌
        timeout: 过期时间（秒）
        
    Returns:
        bool: 是否成功
    """
    return cache_set(f"blacklist_token:{token}", "1", timeout)


def is_token_blacklisted(token: str) -> bool:
    """
    检查令牌是否在黑名单中
    
    Args:
        token: JWT令牌
        
    Returns:
        bool: 是否在黑名单中
    """
    return cache_exists(f"blacklist_token:{token}")