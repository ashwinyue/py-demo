from datetime import datetime
from ..extensions import db


class UserRole(db.Model):
    """用户角色关联模型"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    # 分配信息
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 分配者
    assigned_reason = db.Column(db.String(255), nullable=True)  # 分配原因
    
    # 有效期
    expires_at = db.Column(db.DateTime, nullable=True)  # 角色过期时间
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], back_populates='user_roles')
    role = db.relationship('Role', back_populates='user_roles')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by])
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='uk_user_role'),)
    
    def __repr__(self):
        return f'<UserRole user_id={self.user_id} role_id={self.role_id}>'
    
    def is_expired(self):
        """检查角色是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """检查角色分配是否有效"""
        return self.is_active and not self.is_expired()
    
    def deactivate(self):
        """停用角色分配"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """激活角色分配"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def extend_expiry(self, days=30):
        """延长角色有效期"""
        from datetime import timedelta
        if self.expires_at:
            self.expires_at = max(self.expires_at, datetime.utcnow()) + timedelta(days=days)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'user_username': self.user.username if self.user else None,
            'role_name': self.role.name if self.role else None,
            'role_display_name': self.role.display_name if self.role else None,
            'assigned_by': self.assigned_by,
            'assigned_by_username': self.assigned_by_user.username if self.assigned_by_user else None,
            'assigned_reason': self.assigned_reason,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def assign_role_to_user(cls, user_id, role_id, assigned_by=None, assigned_reason=None, expires_at=None):
        """为用户分配角色"""
        # 检查是否已存在有效的角色分配
        existing = cls.query.filter_by(
            user_id=user_id, 
            role_id=role_id, 
            is_active=True
        ).first()
        
        if existing and existing.is_valid():
            return existing
        
        # 如果存在但已过期或停用，则重新激活
        if existing:
            existing.activate()
            if expires_at:
                existing.expires_at = expires_at
            if assigned_reason:
                existing.assigned_reason = assigned_reason
            return existing
        
        # 创建新的角色分配
        user_role = cls(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_reason=assigned_reason,
            expires_at=expires_at
        )
        
        return user_role
    
    @classmethod
    def remove_role_from_user(cls, user_id, role_id):
        """从用户移除角色"""
        user_role = cls.query.filter_by(
            user_id=user_id, 
            role_id=role_id, 
            is_active=True
        ).first()
        
        if user_role:
            user_role.deactivate()
            return True
        return False
    
    @classmethod
    def get_user_roles(cls, user_id, active_only=True):
        """获取用户的所有角色"""
        query = cls.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def get_role_users(cls, role_id, active_only=True):
        """获取拥有指定角色的所有用户"""
        query = cls.query.filter_by(role_id=role_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def get_expired_assignments(cls):
        """获取已过期的角色分配"""
        return cls.query.filter(
            cls.expires_at.isnot(None),
            cls.expires_at < datetime.utcnow(),
            cls.is_active == True
        ).all()
    
    @classmethod
    def cleanup_expired_assignments(cls):
        """清理过期的角色分配"""
        expired_assignments = cls.get_expired_assignments()
        count = 0
        for assignment in expired_assignments:
            assignment.deactivate()
            count += 1
        return count
    
    @classmethod
    def get_user_valid_roles(cls, user_id):
        """获取用户的有效角色"""
        user_roles = cls.query.filter_by(user_id=user_id, is_active=True).all()
        return [ur.role for ur in user_roles if ur.is_valid()]
    
    @classmethod
    def user_has_role(cls, user_id, role_name):
        """检查用户是否拥有指定角色"""
        from .role import Role
        
        user_role = cls.query.join(Role).filter(
            cls.user_id == user_id,
            Role.name == role_name,
            cls.is_active == True
        ).first()
        
        return user_role and user_role.is_valid()
    
    @classmethod
    def get_assignments_by_assigner(cls, assigned_by):
        """获取指定用户分配的所有角色"""
        return cls.query.filter_by(assigned_by=assigned_by).all()