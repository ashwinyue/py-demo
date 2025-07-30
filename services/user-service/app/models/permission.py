from datetime import datetime
from ..extensions import db


class Permission(db.Model):
    """权限模型"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource = db.Column(db.String(50), nullable=False)  # 资源类型，如 user, post, comment
    action = db.Column(db.String(50), nullable=False)    # 操作类型，如 create, read, update, delete
    
    # 状态字段
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # 系统权限不可删除
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    role_permissions = db.relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def get_roles(self):
        """获取拥有此权限的所有角色"""
        return [rp.role for rp in self.role_permissions]
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'role_count': len(self.role_permissions)
        }
    
    @classmethod
    def create_permission(cls, name, display_name, resource, action, description=None, is_system=False):
        """创建权限"""
        # 检查权限名是否已存在
        if cls.query.filter_by(name=name).first():
            raise ValueError('Permission name already exists')
        
        permission = cls(
            name=name,
            display_name=display_name,
            description=description,
            resource=resource,
            action=action,
            is_system=is_system
        )
        
        return permission
    
    @classmethod
    def get_system_permissions(cls):
        """获取系统权限"""
        return cls.query.filter_by(is_system=True).all()
    
    @classmethod
    def get_active_permissions(cls):
        """获取活跃权限"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_permissions_by_resource(cls, resource):
        """根据资源获取权限"""
        return cls.query.filter_by(resource=resource, is_active=True).all()
    
    @classmethod
    def init_default_permissions(cls):
        """初始化默认权限"""
        default_permissions = [
            # 用户管理权限
            {
                'name': 'user.create',
                'display_name': '创建用户',
                'description': '创建新用户账户',
                'resource': 'user',
                'action': 'create',
                'is_system': True
            },
            {
                'name': 'user.read',
                'display_name': '查看用户',
                'description': '查看用户信息',
                'resource': 'user',
                'action': 'read',
                'is_system': True
            },
            {
                'name': 'user.update',
                'display_name': '更新用户',
                'description': '更新用户信息',
                'resource': 'user',
                'action': 'update',
                'is_system': True
            },
            {
                'name': 'user.delete',
                'display_name': '删除用户',
                'description': '删除用户账户',
                'resource': 'user',
                'action': 'delete',
                'is_system': True
            },
            {
                'name': 'user.manage',
                'display_name': '管理用户',
                'description': '管理所有用户',
                'resource': 'user',
                'action': 'manage',
                'is_system': True
            },
            
            # 角色管理权限
            {
                'name': 'role.create',
                'display_name': '创建角色',
                'description': '创建新角色',
                'resource': 'role',
                'action': 'create',
                'is_system': True
            },
            {
                'name': 'role.read',
                'display_name': '查看角色',
                'description': '查看角色信息',
                'resource': 'role',
                'action': 'read',
                'is_system': True
            },
            {
                'name': 'role.update',
                'display_name': '更新角色',
                'description': '更新角色信息',
                'resource': 'role',
                'action': 'update',
                'is_system': True
            },
            {
                'name': 'role.delete',
                'display_name': '删除角色',
                'description': '删除角色',
                'resource': 'role',
                'action': 'delete',
                'is_system': True
            },
            
            # 权限管理权限
            {
                'name': 'permission.read',
                'display_name': '查看权限',
                'description': '查看权限信息',
                'resource': 'permission',
                'action': 'read',
                'is_system': True
            },
            {
                'name': 'permission.manage',
                'display_name': '管理权限',
                'description': '管理系统权限',
                'resource': 'permission',
                'action': 'manage',
                'is_system': True
            },
            
            # 系统管理权限
            {
                'name': 'system.admin',
                'display_name': '系统管理',
                'description': '系统管理员权限',
                'resource': 'system',
                'action': 'admin',
                'is_system': True
            },
            {
                'name': 'system.monitor',
                'display_name': '系统监控',
                'description': '系统监控权限',
                'resource': 'system',
                'action': 'monitor',
                'is_system': True
            },
            
            # 个人资料权限
            {
                'name': 'profile.read',
                'display_name': '查看个人资料',
                'description': '查看自己的个人资料',
                'resource': 'profile',
                'action': 'read',
                'is_system': True
            },
            {
                'name': 'profile.update',
                'display_name': '更新个人资料',
                'description': '更新自己的个人资料',
                'resource': 'profile',
                'action': 'update',
                'is_system': True
            }
        ]
        
        created_permissions = []
        for perm_data in default_permissions:
            existing_permission = cls.query.filter_by(name=perm_data['name']).first()
            if not existing_permission:
                permission = cls(**perm_data)
                db.session.add(permission)
                created_permissions.append(permission)
        
        return created_permissions


class RolePermission(db.Model):
    """角色权限关联模型"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联关系
    role = db.relationship('Role', back_populates='role_permissions')
    permission = db.relationship('Permission', back_populates='role_permissions')
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='uk_role_permission'),)
    
    def __repr__(self):
        return f'<RolePermission role_id={self.role_id} permission_id={self.permission_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'role_name': self.role.name if self.role else None,
            'permission_name': self.permission.name if self.permission else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def assign_permission_to_role(cls, role_id, permission_id):
        """为角色分配权限"""
        # 检查是否已存在
        existing = cls.query.filter_by(role_id=role_id, permission_id=permission_id).first()
        if existing:
            return existing
        
        role_permission = cls(role_id=role_id, permission_id=permission_id)
        return role_permission
    
    @classmethod
    def remove_permission_from_role(cls, role_id, permission_id):
        """从角色移除权限"""
        role_permission = cls.query.filter_by(role_id=role_id, permission_id=permission_id).first()
        if role_permission:
            db.session.delete(role_permission)
            return True
        return False