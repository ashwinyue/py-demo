from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from app.core.database import Base

# SQLAlchemy模型
class Post(Base):
    """博客文章数据库模型"""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(String(500))
    
    # 用户关联
    user_id = Column(Integer, nullable=False, index=True)
    author_name = Column(String(80))
    
    # 文章状态
    status = Column(String(20), default='draft', index=True)
    is_featured = Column(Boolean, default=False, index=True)
    
    # 统计信息
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, index=True)
    
    # 创建复合索引
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_user_status', 'user_id', 'status'),
    )