"""基础异常定义"""

from typing import Optional, Dict, Any


class MiniBlogException(Exception):
    """MiniBlog基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(MiniBlogException):
    """数据验证异常"""
    pass


class AuthenticationError(MiniBlogException):
    """认证异常"""
    pass


class AuthorizationError(MiniBlogException):
    """授权异常"""
    pass


class ResourceNotFoundError(MiniBlogException):
    """资源未找到异常"""
    pass


class ResourceConflictError(MiniBlogException):
    """资源冲突异常"""
    pass


class DatabaseError(MiniBlogException):
    """数据库异常"""
    pass


class ExternalServiceError(MiniBlogException):
    """外部服务异常"""
    pass


class RateLimitError(MiniBlogException):
    """限流异常"""
    pass


class ConfigurationError(MiniBlogException):
    """配置异常"""
    pass