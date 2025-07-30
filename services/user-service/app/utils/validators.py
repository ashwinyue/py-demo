# -*- coding: utf-8 -*-
"""
验证器工具函数
"""

import re
from typing import Dict, List, Any


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否为有效邮箱格式
    """
    if not email or not isinstance(email, str):
        return False
    
    # 邮箱正则表达式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(email_pattern, email.strip()))


def validate_password(password: str) -> Dict[str, Any]:
    """
    验证密码强度
    
    Args:
        password: 密码
        
    Returns:
        Dict: 验证结果，包含 valid 和 errors 字段
    """
    errors = []
    
    if not password or not isinstance(password, str):
        return {
            'valid': False,
            'errors': ['Password is required']
        }
    
    # 长度检查
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if len(password) > 128:
        errors.append('Password must be no more than 128 characters long')
    
    # 复杂度检查
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    complexity_count = sum([has_upper, has_lower, has_digit, has_special])
    
    if complexity_count < 3:
        errors.append('Password must contain at least 3 of the following: uppercase letter, lowercase letter, digit, special character')
    
    # 常见弱密码检查
    weak_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password123', '12345678', '111111', '123123', 'admin'
    ]
    
    if password.lower() in weak_passwords:
        errors.append('Password is too common and weak')
    
    # 重复字符检查
    if re.search(r'(.)\1{2,}', password):
        errors.append('Password should not contain more than 2 consecutive identical characters')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'strength': _calculate_password_strength(password, has_upper, has_lower, has_digit, has_special)
    }


def _calculate_password_strength(password: str, has_upper: bool, has_lower: bool, 
                                has_digit: bool, has_special: bool) -> str:
    """
    计算密码强度
    
    Args:
        password: 密码
        has_upper: 是否包含大写字母
        has_lower: 是否包含小写字母
        has_digit: 是否包含数字
        has_special: 是否包含特殊字符
        
    Returns:
        str: 密码强度等级 (weak, medium, strong, very_strong)
    """
    score = 0
    
    # 长度评分
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    # 复杂度评分
    if has_upper:
        score += 1
    if has_lower:
        score += 1
    if has_digit:
        score += 1
    if has_special:
        score += 1
    
    # 多样性评分
    unique_chars = len(set(password))
    if unique_chars >= len(password) * 0.7:
        score += 1
    
    if score <= 3:
        return 'weak'
    elif score <= 5:
        return 'medium'
    elif score <= 7:
        return 'strong'
    else:
        return 'very_strong'


def validate_username(username: str) -> Dict[str, Any]:
    """
    验证用户名格式
    
    Args:
        username: 用户名
        
    Returns:
        Dict: 验证结果
    """
    errors = []
    
    if not username or not isinstance(username, str):
        return {
            'valid': False,
            'errors': ['Username is required']
        }
    
    username = username.strip()
    
    # 长度检查
    if len(username) < 3:
        errors.append('Username must be at least 3 characters long')
    
    if len(username) > 50:
        errors.append('Username must be no more than 50 characters long')
    
    # 格式检查
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        errors.append('Username can only contain letters, numbers, underscores, and hyphens')
    
    # 不能以数字开头
    if username and username[0].isdigit():
        errors.append('Username cannot start with a number')
    
    # 保留用户名检查
    reserved_usernames = [
        'admin', 'administrator', 'root', 'system', 'user', 'guest',
        'api', 'www', 'mail', 'ftp', 'test', 'demo', 'support'
    ]
    
    if username.lower() in reserved_usernames:
        errors.append('This username is reserved and cannot be used')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式（中国大陆）
    
    Args:
        phone: 手机号
        
    Returns:
        bool: 是否为有效手机号
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # 中国大陆手机号正则表达式
    phone_pattern = r'^1[3-9]\d{9}$'
    
    return bool(re.match(phone_pattern, phone.strip()))


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    清理用户输入
    
    Args:
        text: 输入文本
        max_length: 最大长度
        
    Returns:
        str: 清理后的文本
    """
    if not text or not isinstance(text, str):
        return ''
    
    # 去除首尾空格
    text = text.strip()
    
    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]
    
    # 移除危险字符
    dangerous_chars = ['<', '>', '"', "'", '&']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text