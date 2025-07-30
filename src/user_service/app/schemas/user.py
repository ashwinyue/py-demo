from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=80, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")

class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    verification_code: Optional[str] = Field(None, description="验证码")

class UserUpdate(BaseModel):
    """更新用户模型"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")

class UserResponse(UserBase):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    role: str = Field(..., description="用户角色")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    model_config = {"from_attributes": True}

class UserProfile(BaseModel):
    """用户资料模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    created_at: datetime = Field(..., description="创建时间")
    
    model_config = {"from_attributes": True}

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: list[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    per_page: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")