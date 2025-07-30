from datetime import datetime
from ..extensions import db


class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # 状态字段
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # 系统角色不可删除
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    user_roles = db.relationship('UserRole', back_populates='role', cascade='all, delete-orphan')
    role_permissions = db.relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission_name):
        """检查角色是否有指定权限"""
        for role_permission in self.role_permissions:
            if role_permission.permission.name == permission_name:
                return True
        return False
    
    def get_permissions(self):
        """获取角色的所有权限"""
        return [rp.permission for rp in self.role_permissions]
    
    def get_users(self):
        """获取拥有此角色的所有用户"""
        return [ur.user for ur in self.user_roles]
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'permissions': [p.name for p in self.get_permissions()],
            'user_count': len(self.user_roles)
        }
    
    @classmethod
    def create_role(cls, name, display_name, description=None, is_system=False):
        """创建角色"""
        # 检查角色名是否已存在
        if cls.query.filter_by(name=name).first():
            raise ValueError('Role name already exists')
        
        role = cls(
            name=name,
            display_name=display_name,
            description=description,
            is_system=is_system
        )
        
        return role
    
    @classmethod
    def get_system_roles(cls):
        """获取系统角色"""
        return cls.query.filter_by(is_system=True).all()
    
    @classmethod
    def get_active_roles(cls):
        """获取活跃角色"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def init_default_roles(cls):
        """初始化默认角色"""
        default_roles = [
            {
                'name': 'admin',
                'display_name': '管理员',
                'description': '系统管理员，拥有所有权限',
                'is_system': True
            },
            {
                'name': 'user',
                'display_name': '普通用户',
                'description': '普通用户，拥有基本权限',
                'is_system': True
            },
            {
                'name': 'moderator',
                'display_name': '版主',
                'description': '内容管理员，可以管理用户内容',
                'is_system': True
            }
        ]
        
        created_roles = []
        for role_data in default_roles:
            existing_role = cls.query.filter_by(name=role_data['name']).first()
            if not existing_role:
                role = cls(**role_data)
                db.session.add(role)
                created_roles.append(role)
        
        return created_roles