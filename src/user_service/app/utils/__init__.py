# -*- coding: utf-8 -*-
"""
工具函数包
"""

from .validators import (
    validate_email,
    validate_password,
    validate_username,
    validate_phone,
    sanitize_input
)

from .decorators import (
    token_required,
    admin_required,
    permission_required,
    role_required,
    rate_limit,
    cache_result,
    validate_json
)

from .helpers import (
    get_client_ip,
    parse_user_agent,
    generate_random_string,
    generate_verification_code,
    hash_string,
    mask_email,
    mask_phone,
    calculate_age,
    format_file_size,
    time_ago,
    is_safe_url,
    clean_filename,
    paginate_query,
    detect_suspicious_activity
)

from .cache import (
    cache_manager,
    cache_set,
    cache_get,
    cache_delete,
    cache_exists,
    cache_clear_user,
    cache_user_profile,
    get_cached_user_profile,
    cache_user_permissions,
    get_cached_user_permissions,
    cache_verification_code,
    get_cached_verification_code,
    delete_verification_code,
    cache_rate_limit,
    get_rate_limit_remaining,
    cache_blacklist_token,
    is_token_blacklisted
)

__all__ = [
    # 验证器
    'validate_email',
    'validate_password', 
    'validate_username',
    'validate_phone',
    'sanitize_input',
    
    # 装饰器
    'token_required',
    'admin_required',
    'permission_required',
    'role_required',
    'rate_limit',
    'cache_result',
    'validate_json',
    
    # 辅助函数
    'get_client_ip',
    'parse_user_agent',
    'generate_random_string',
    'generate_verification_code',
    'hash_string',
    'mask_email',
    'mask_phone',
    'calculate_age',
    'format_file_size',
    'time_ago',
    'is_safe_url',
    'clean_filename',
    'paginate_query',
    'detect_suspicious_activity',
    
    # 缓存工具
    'cache_manager',
    'cache_set',
    'cache_get',
    'cache_delete',
    'cache_exists',
    'cache_clear_user',
    'cache_user_profile',
    'get_cached_user_profile',
    'cache_user_permissions',
    'get_cached_user_permissions',
    'cache_verification_code',
    'get_cached_verification_code',
    'delete_verification_code',
    'cache_rate_limit',
    'get_rate_limit_remaining',
    'cache_blacklist_token',
    'is_token_blacklisted'
]