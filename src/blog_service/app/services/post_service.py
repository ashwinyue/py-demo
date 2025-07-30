"""Post service for business logic."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from datetime import datetime

from app.models import Post
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostSummary
from app.services.redis_service import (
    cache_post_data,
    get_cached_post_data,
    invalidate_posts_cache,
    increment_post_view_count,
    increment_post_like_count,
    get_post_like_count
)


class PostService:
    """文章服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_posts(
        self,
        page: int = 1,
        per_page: int = 10,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[PostSummary], int]:
        """获取文章列表"""
        query = self.db.query(Post)
        
        # 过滤条件
        if user_id:
            query = query.filter(Post.user_id == user_id)
        if status:
            query = query.filter(Post.status == status)
        if search:
            query = query.filter(
                or_(
                    Post.title.contains(search),
                    Post.content.contains(search),
                    Post.summary.contains(search)
                )
            )
        
        # 排序
        sort_column = getattr(Post, sort_by, Post.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        total = query.count()
        posts = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return posts, total
    
    def get_post_by_id(self, post_id: int) -> Optional[Post]:
        """根据ID获取文章"""
        # 尝试从缓存获取
        cached_post = get_cached_post_data(post_id)
        if cached_post:
            return cached_post
        
        # 从数据库获取
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if post:
            # 缓存文章数据
            cache_post_data(post_id, post)
            # 增加浏览次数
            increment_post_view_count(post_id)
        
        return post
    
    def create_post(self, post_data: PostCreate) -> Post:
        """创建文章"""
        db_post = Post(
            title=post_data.title,
            content=post_data.content,
            summary=post_data.summary,
            status=post_data.status,
            is_featured=post_data.is_featured,
            user_id=post_data.user_id,
            author_name=post_data.author_name,
            published_at=datetime.utcnow() if post_data.status == "published" else None
        )
        
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        
        # 清除缓存
        invalidate_posts_cache()
        
        return db_post
    
    def update_post(self, post_id: int, post_data: PostUpdate) -> Optional[Post]:
        """更新文章"""
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return None
        
        # 更新字段
        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)
        
        # 如果状态改为已发布，设置发布时间
        if post_data.status == "published" and not post.published_at:
            post.published_at = datetime.utcnow()
        
        post.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(post)
        
        # 清除缓存
        invalidate_posts_cache()
        cache_post_data(post_id, post)  # 更新缓存
        
        return post
    
    def delete_post(self, post_id: int) -> bool:
        """删除文章"""
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False
        
        self.db.delete(post)
        self.db.commit()
        
        # 清除缓存
        invalidate_posts_cache()
        
        return True
    
    def like_post(self, post_id: int) -> tuple[bool, int]:
        """点赞文章"""
        # 检查文章是否存在
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False, 0
        
        # 增加点赞次数（Redis计数）
        new_like_count = increment_post_like_count(post_id)
        
        # 更新数据库中的点赞次数
        post.like_count = new_like_count
        self.db.commit()
        
        # 清除相关缓存
        invalidate_posts_cache()
        
        return True, new_like_count