from datetime import datetime
from app import db

class Post(db.Model):
    """博客文章模型"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))  # 文章摘要
    
    # 用户关联（通过用户服务获取）
    user_id = db.Column(db.Integer, nullable=False, index=True)
    author_name = db.Column(db.String(80))  # 冗余存储作者名称，提高查询性能
    
    # 文章状态
    status = db.Column(db.String(20), default='draft', index=True)  # draft, published, archived
    is_featured = db.Column(db.Boolean, default=False, index=True)  # 是否精选
    
    # 统计信息
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # 分类和标签
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    tags = db.relationship('Tag', secondary='post_tags', backref='posts', lazy='dynamic')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)  # 发布时间
    
    # 关联关系
    category = db.relationship('Category', backref='posts')
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    def to_dict(self, include_content=True, include_author=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'title': self.title,
            'summary': self.summary or (self.content[:200] + '...' if len(self.content) > 200 else self.content),
            'user_id': self.user_id,
            'status': self.status,
            'is_featured': self.is_featured,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
        
        if include_content:
            data['content'] = self.content
        
        if include_author:
            data['author_name'] = self.author_name
        
        if self.category:
            data['category'] = self.category.to_dict()
        
        # 添加标签
        data['tags'] = [tag.to_dict() for tag in self.tags]
        
        return data
    
    def from_dict(self, data, new_post=False):
        """从字典更新"""
        for field in ['title', 'content', 'summary', 'status', 'is_featured', 'category_id']:
            if field in data:
                setattr(self, field, data[field])
        
        if new_post and 'user_id' in data:
            self.user_id = data['user_id']
        
        if 'author_name' in data:
            self.author_name = data['author_name']
        
        # 处理发布状态
        if data.get('status') == 'published' and not self.published_at:
            self.published_at = datetime.utcnow()
        elif data.get('status') != 'published':
            self.published_at = None
    
    def increment_view(self):
        """增加浏览量"""
        self.view_count += 1
        db.session.commit()
    
    def increment_like(self):
        """增加点赞数"""
        self.like_count += 1
        db.session.commit()
    
    def update_comment_count(self):
        """更新评论数"""
        self.comment_count = self.comments.count()
        db.session.commit()

class Category(db.Model):
    """文章分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    description = db.Column(db.String(200))
    slug = db.Column(db.String(50), unique=True, index=True)  # URL友好的标识符
    
    # 层级关系
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    
    # 统计信息
    post_count = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self, include_posts=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'slug': self.slug,
            'parent_id': self.parent_id,
            'post_count': self.post_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_posts:
            data['posts'] = [post.to_dict(include_content=False) for post in self.posts]
        
        return data
    
    def update_post_count(self):
        """更新文章数量"""
        self.post_count = self.posts.filter_by(status='published').count()
        db.session.commit()

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True, index=True)
    color = db.Column(db.String(7), default='#007bff')  # 标签颜色
    
    # 统计信息
    post_count = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'post_count': self.post_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_post_count(self):
        """更新文章数量"""
        self.post_count = self.posts.filter_by(status='published').count()
        db.session.commit()

# 文章标签关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # 关联关系
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # 评论者ID
    author_name = db.Column(db.String(80))  # 冗余存储评论者名称
    
    # 回复关系
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    # 状态
    status = db.Column(db.String(20), default='published', index=True)  # published, hidden, deleted
    
    # 统计信息
    like_count = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    
    def to_dict(self, include_replies=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'content': self.content,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'author_name': self.author_name,
            'parent_id': self.parent_id,
            'status': self.status,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_replies and self.parent_id is None:
            data['replies'] = [reply.to_dict(include_replies=False) for reply in self.replies.filter_by(status='published')]
        
        return data