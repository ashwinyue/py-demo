from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.models import Post
from app.schemas import (
    PostCreate, PostUpdate, PostResponse, PostSummary, 
    PostListResponse, LikeResponse, ErrorResponse
)
from app.core.database import get_db
from app.services.post_service import PostService
from app.services.redis_service import get_user_info, verify_user_token
from app.core.config import get_settings

router = APIRouter(prefix="/api/posts", tags=["posts"])

@router.get("/", response_model=PostListResponse)
async def get_posts(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    status: Optional[str] = Query(None, pattern="^(draft|published|archived)$", description="状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    settings = get_settings()
    
    # 限制每页数量
    per_page = min(per_page, settings.max_posts_per_page)
    
    # 使用服务层
    post_service = PostService(db)
    posts, total = post_service.get_posts(
        page=page,
        per_page=per_page,
        user_id=user_id,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # 计算分页信息
    pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < pages
    
    return PostListResponse(
        posts=[PostSummary.model_validate(post) for post in posts],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_prev=has_prev,
        has_next=has_next
    )

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """获取单个文章详情"""
    post_service = PostService(db)
    post = post_service.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    return PostResponse.model_validate(post)

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db)
):
    """创建新文章"""
    post_service = PostService(db)
    post = post_service.create_post(post_data)
    
    return PostResponse.model_validate(post)

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: Session = Depends(get_db)
):
    """更新文章"""
    post_service = PostService(db)
    post = post_service.update_post(post_id, post_data)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    return PostResponse.model_validate(post)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """删除文章"""
    post_service = PostService(db)
    success = post_service.delete_post(post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    return None

@router.post("/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: int = Path(..., description="文章ID"),
    db: Session = Depends(get_db)
):
    """点赞文章"""
    post_service = PostService(db)
    success, like_count = post_service.like_post(post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    
    return LikeResponse(
        success=True,
        like_count=like_count,
        message="点赞成功"
    )