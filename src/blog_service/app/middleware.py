from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import time
import logging

from app.services.redis_service import verify_user_token, verify_token
from app.core.config import get_settings

# 设置日志
logger = logging.getLogger(__name__)

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = None) -> Optional[dict]:
    """获取当前用户信息"""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # 首先尝试本地JWT验证
    user_info = verify_token(token)
    if user_info:
        return user_info
    
    # 如果本地验证失败，尝试用户服务验证
    user_info = verify_user_token(token)
    if user_info:
        return user_info
    
    return None

async def require_auth(credentials: HTTPAuthorizationCredentials = security) -> dict:
    """要求认证的依赖项"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌缺失",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = await get_current_user(credentials)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info

async def require_admin(user_info: dict = require_auth) -> dict:
    """要求管理员权限的依赖项"""
    if not user_info.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return user_info

def setup_cors_middleware(app):
    """设置CORS中间件"""
    settings = get_settings()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

class LoggingMiddleware:
    """请求日志中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # 创建请求对象
        request = Request(scope, receive)
        
        # 记录请求开始
        logger.info(
            f"请求开始: {request.method} {request.url.path} "
            f"来源IP: {request.client.host if request.client else 'unknown'}"
        )
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # 计算处理时间
                process_time = time.time() - start_time
                
                # 记录响应
                status_code = message["status"]
                logger.info(
                    f"请求完成: {request.method} {request.url.path} "
                    f"状态码: {status_code} 处理时间: {process_time:.3f}s"
                )
                
                # 添加处理时间头
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", str(process_time).encode()))
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class SecurityHeadersMiddleware:
    """安全头中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # 添加安全头
                security_headers = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                ]
                
                headers.extend(security_headers)
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class RateLimitMiddleware:
    """简单的速率限制中间件"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # 简单的内存存储，生产环境应使用Redis
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 获取客户端IP
        client_ip = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-forwarded-for":
                client_ip = header_value.decode().split(",")[0].strip()
                break
        
        if not client_ip:
            client_ip = scope.get("client", ["unknown"])[0]
        
        # 检查速率限制
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            # 返回429错误
            response = {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(self.window_seconds).encode()),
                ],
            }
            await send(response)
            
            body = {
                "type": "http.response.body",
                "body": b'{"error": "Rate limit exceeded"}',
            }
            await send(body)
            return
        
        # 记录请求
        self.requests[client_ip].append(current_time)
        
        await self.app(scope, receive, send)

def setup_middleware(app):
    """设置所有中间件"""
    # CORS中间件
    setup_cors_middleware(app)
    
    # 自定义中间件
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # 速率限制中间件（可选）
    settings = get_settings()
    if hasattr(settings, 'rate_limit_enabled') and settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=getattr(settings, 'rate_limit_requests', 100),
            window_seconds=getattr(settings, 'rate_limit_window', 60)
        )