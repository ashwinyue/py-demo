"""CORS中间件"""

from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..config.base import get_config


def add_cors_middleware(
    app: FastAPI,
    allow_origins: Optional[List[str]] = None,
    allow_credentials: bool = True,
    allow_methods: Optional[List[str]] = None,
    allow_headers: Optional[List[str]] = None
):
    """添加CORS中间件"""
    config = get_config()
    
    # 默认配置
    if allow_origins is None:
        allow_origins = config.CORS_ORIGINS if hasattr(config, 'CORS_ORIGINS') else ["*"]
    
    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    
    if allow_headers is None:
        allow_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url.path} "
            f"- 客户端: {request.client.host if request.client else 'unknown'}"
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"- 状态码: {response.status_code} "
            f"- 处理时间: {process_time:.3f}s"
        )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def add_common_middleware(app: FastAPI):
    """添加通用中间件"""
    # 添加CORS中间件
    add_cors_middleware(app)
    
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 添加安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)