"""Post related Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PostBase(BaseModel):
    """文章基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    content: str = Field(..., min_length=1, description="文章内容")
    summary: Optional[str] = Field(None, max_length=500, description="文章摘要")
    status: str = Field(default="draft", pattern="^(draft|published|archived)$", description="文章状态")
    is_featured: bool = Field(default=False, description="是否精选")


class PostCreate(PostBase):
    """创建文章模型"""
    user_id: int = Field(..., gt=0, description="作者用户ID")
    author_name: Optional[str] = Field(None, max_length=80, description="作者名称")


class PostUpdate(BaseModel):
    """更新文章模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="文章标题")
    content: Optional[str] = Field(None, min_length=1, description="文章内容")
    summary: Optional[str] = Field(None, max_length=500, description="文章摘要")
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$", description="文章状态")
    is_featured: Optional[bool] = Field(None, description="是否精选")


class PostResponse(PostBase):
    """文章响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="文章ID")
    user_id: int = Field(..., description="作者用户ID")
    author_name: Optional[str] = Field(None, description="作者名称")
    view_count: int = Field(default=0, description="浏览次数")
    like_count: int = Field(default=0, description="点赞次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")


class PostSummary(BaseModel):
    """文章摘要模型（用于列表显示）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="文章ID")
    title: str = Field(..., description="文章标题")
    summary: Optional[str] = Field(None, description="文章摘要")
    user_id: int = Field(..., description="作者用户ID")
    author_name: Optional[str] = Field(None, description="作者名称")
    status: str = Field(..., description="文章状态")
    is_featured: bool = Field(..., description="是否精选")
    view_count: int = Field(..., description="浏览次数")
    like_count: int = Field(..., description="点赞次数")
    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")


class PostListResponse(BaseModel):
    """文章列表响应模型"""
    posts: list[PostSummary] = Field(..., description="文章列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")
    has_prev: bool = Field(..., description="是否有上一页")
    has_next: bool = Field(..., description="是否有下一页")


class LikeResponse(BaseModel):
    """点赞响应模型"""
    success: bool = Field(..., description="操作是否成功")
    like_count: int = Field(..., description="当前点赞数")
    message: str = Field(..., description="响应消息")