from pydantic import BaseModel, Field
from typing import Optional, Any

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="服务版本")
    timestamp: str = Field(..., description="检查时间")
    database: str = Field(..., description="数据库状态")
    redis: str = Field(..., description="Redis状态")

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
    code: Optional[int] = Field(None, description="错误代码")

class MessageResponse(BaseModel):
    """消息响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="附加数据")