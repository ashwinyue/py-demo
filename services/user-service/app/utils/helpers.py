# -*- coding: utf-8 -*-
"""
辅助工具函数
"""

import re
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import request
from user_agents import parse


def get_client_ip() -> str:
    """
    获取客户端真实IP地址
    
    Returns:
        str: 客户端IP地址
    """
    # 检查代理头
    if request.headers.get('X-Forwarded-For'):
        # 取第一个IP（客户端真实IP）
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    elif request.headers.get('X-Forwarded-Host'):
        ip = request.headers.get('X-Forwarded-Host')
    else:
        ip = request.remote_addr or 'unknown'
    
    return ip


def parse_user_agent(user_agent_string: str = None) -> Dict[str, Any]:
    """
    解析用户代理字符串
    
    Args:
        user_agent_string: 用户代理字符串，默认从请求头获取
        
    Returns:
        Dict: 解析后的用户代理信息
    """
    if not user_agent_string:
        user_agent_string = request.headers.get('User-Agent', '')
    
    if not user_agent_string:
        return {
            'browser': 'Unknown',
            'browser_version': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'device': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_pc': True
        }
    
    try:
        user_agent = parse(user_agent_string)
        
        return {
            'browser': user_agent.browser.family,
            'browser_version': user_agent.browser.version_string,
            'os': user_agent.os.family,
            'os_version': user_agent.os.version_string,
            'device': user_agent.device.family,
            'is_mobile': user_agent.is_mobile,
            'is_tablet': user_agent.is_tablet,
            'is_pc': user_agent.is_pc
        }
    except Exception:
        return {
            'browser': 'Unknown',
            'browser_version': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'device': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_pc': True
        }


def generate_random_string(length: int = 32, include_digits: bool = True, 
                          include_uppercase: bool = True, include_lowercase: bool = True,
                          include_symbols: bool = False) -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        include_digits: 是否包含数字
        include_uppercase: 是否包含大写字母
        include_lowercase: 是否包含小写字母
        include_symbols: 是否包含符号
        
    Returns:
        str: 随机字符串
    """
    characters = ''
    
    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_digits:
        characters += string.digits
    if include_symbols:
        characters += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    if not characters:
        characters = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_verification_code(length: int = 6) -> str:
    """
    生成验证码
    
    Args:
        length: 验证码长度
        
    Returns:
        str: 验证码
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def hash_string(text: str, salt: str = None) -> str:
    """
    对字符串进行哈希
    
    Args:
        text: 要哈希的文本
        salt: 盐值
        
    Returns:
        str: 哈希值
    """
    if salt:
        text = text + salt
    
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def mask_email(email: str) -> str:
    """
    遮蔽邮箱地址
    
    Args:
        email: 邮箱地址
        
    Returns:
        str: 遮蔽后的邮箱地址
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = local[0] + '*' * (len(local) - 1)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    遮蔽手机号
    
    Args:
        phone: 手机号
        
    Returns:
        str: 遮蔽后的手机号
    """
    if not phone or len(phone) < 7:
        return phone
    
    return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]


def calculate_age(birth_date: datetime) -> int:
    """
    计算年龄
    
    Args:
        birth_date: 出生日期
        
    Returns:
        int: 年龄
    """
    today = datetime.now().date()
    birth_date = birth_date.date() if isinstance(birth_date, datetime) else birth_date
    
    age = today.year - birth_date.year
    
    # 检查是否还没过生日
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
    """
    if size_bytes == 0:
        return '0 B'
    
    size_names = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def time_ago(dt: datetime) -> str:
    """
    计算时间差并返回友好的时间描述
    
    Args:
        dt: 时间
        
    Returns:
        str: 时间描述
    """
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return '1 day ago'
        elif diff.days < 30:
            return f'{diff.days} days ago'
        elif diff.days < 365:
            months = diff.days // 30
            return f'{months} month{"s" if months > 1 else ""} ago'
        else:
            years = diff.days // 365
            return f'{years} year{"s" if years > 1 else ""} ago'
    
    seconds = diff.seconds
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = seconds // 60
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    else:
        hours = seconds // 3600
        return f'{hours} hour{"s" if hours > 1 else ""} ago'


def is_safe_url(target: str) -> bool:
    """
    检查URL是否安全（防止开放重定向攻击）
    
    Args:
        target: 目标URL
        
    Returns:
        bool: 是否安全
    """
    if not target:
        return False
    
    # 检查是否为相对URL
    if target.startswith('/'):
        return True
    
    # 检查是否为同域URL
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(target)
        # 只允许http和https协议
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # 检查域名（这里需要根据实际情况配置允许的域名）
        allowed_hosts = ['localhost', '127.0.0.1']  # 可以从配置文件读取
        
        return parsed.netloc in allowed_hosts
    except Exception:
        return False


def clean_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    if not filename:
        return 'unnamed'
    
    # 移除路径分隔符和其他危险字符
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # 移除开头的点（隐藏文件）
    filename = filename.lstrip('.')
    
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename or 'unnamed'


def paginate_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100) -> Dict[str, Any]:
    """
    分页查询辅助函数
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码
        per_page: 每页数量
        max_per_page: 最大每页数量
        
    Returns:
        Dict: 分页结果
    """
    # 限制每页数量
    per_page = min(per_page, max_per_page)
    
    # 执行分页查询
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': pagination.items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'per_page': pagination.per_page,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num
    }


def detect_suspicious_activity(ip: str, user_agent: str, user_id: int = None) -> Dict[str, Any]:
    """
    检测可疑活动
    
    Args:
        ip: IP地址
        user_agent: 用户代理
        user_id: 用户ID
        
    Returns:
        Dict: 检测结果
    """
    risk_score = 0
    reasons = []
    
    # IP地址检查
    if ip in ['127.0.0.1', 'localhost']:
        risk_score += 10
        reasons.append('Local IP address')
    
    # 用户代理检查
    if not user_agent or len(user_agent) < 10:
        risk_score += 20
        reasons.append('Suspicious user agent')
    
    # 检查是否为已知的爬虫或机器人
    bot_patterns = ['bot', 'crawler', 'spider', 'scraper']
    if any(pattern in user_agent.lower() for pattern in bot_patterns):
        risk_score += 30
        reasons.append('Bot or crawler detected')
    
    # 确定风险等级
    if risk_score >= 50:
        risk_level = 'high'
    elif risk_score >= 20:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'reasons': reasons,
        'is_suspicious': risk_score >= 20
    }