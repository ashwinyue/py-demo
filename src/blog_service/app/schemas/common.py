"""Common Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    database: str = Field(..., description="数据库状态")
    redis: str = Field(..., description="Redis状态")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")