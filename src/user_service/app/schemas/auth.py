from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")

class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")

class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")
    verification_code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

class VerificationCodeRequest(BaseModel):
    """验证码请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")
    code_type: str = Field(..., description="验证码类型：register, reset_password, change_email")