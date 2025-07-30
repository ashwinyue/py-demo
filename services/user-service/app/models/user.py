from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from ..extensions import db
import re


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # 状态字段
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    
    # 安全字段
    login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 统计字段
    login_count = db.Column(db.Integer, default=0, nullable=False)
    
    # 关联关系
    user_roles = db.relationship('UserRole', back_populates='user', cascade='all, delete-orphan')
    login_logs = db.relationship('LoginLog', back_populates='user', cascade='all, delete-orphan')
    verification_codes = db.relationship('VerificationCode', back_populates='user', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.nickname:
            self.nickname = self.username
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def password(self):
        """密码属性不可读"""
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """设置密码哈希"""
        if not self.validate_password_strength(password):
            raise ValueError('Password does not meet strength requirements')
        
        rounds = current_app.config.get('PASSWORD_HASH_ROUNDS', 12)
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        self.password_changed_at = datetime.utcnow()
    
    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_password_strength(password):
        """验证密码强度"""
        if len(password) < 8:
            return False
        
        # 至少包含一个数字、一个小写字母、一个大写字母
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[A-Z]', password):
            return False
        
        return True
    
    @staticmethod
    def validate_email(email):
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username):
        """验证用户名格式"""
        if len(username) < 3 or len(username) > 80:
            return False
        
        # 只允许字母、数字、下划线和连字符
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, username) is not None
    
    def is_locked(self):
        """检查账户是否被锁定"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self):
        """锁定账户"""
        timeout = current_app.config.get('LOGIN_ATTEMPT_TIMEOUT', 900)  # 15分钟
        self.locked_until = datetime.utcnow() + datetime.timedelta(seconds=timeout)
        self.login_attempts = 0
    
    def unlock_account(self):
        """解锁账户"""
        self.locked_until = None
        self.login_attempts = 0
    
    def increment_login_attempts(self):
        """增加登录尝试次数"""
        self.login_attempts += 1
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
        
        if self.login_attempts >= max_attempts:
            self.lock_account()
    
    def reset_login_attempts(self):
        """重置登录尝试次数"""
        self.login_attempts = 0
        self.locked_until = None
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
        self.reset_login_attempts()
    
    def verify_email(self):
        """验证邮箱"""
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()
    
    def has_role(self, role_name):
        """检查用户是否有指定角色"""
        for user_role in self.user_roles:
            if user_role.role.name == role_name:
                return True
        return False
    
    def has_permission(self, permission_name):
        """检查用户是否有指定权限"""
        for user_role in self.user_roles:
            for role_permission in user_role.role.role_permissions:
                if role_permission.permission.name == permission_name:
                    return True
        return False
    
    def get_roles(self):
        """获取用户所有角色"""
        return [user_role.role for user_role in self.user_roles]
    
    def get_permissions(self):
        """获取用户所有权限"""
        permissions = set()
        for user_role in self.user_roles:
            for role_permission in user_role.role.role_permissions:
                permissions.add(role_permission.permission)
        return list(permissions)
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'bio': self.bio,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'login_count': self.login_count,
        }
        
        if include_sensitive:
            data.update({
                'login_attempts': self.login_attempts,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None,
                'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None,
            })
        
        return data
    
    @classmethod
    def create_user(cls, username, email, password, **kwargs):
        """创建用户"""
        # 验证输入
        if not cls.validate_username(username):
            raise ValueError('Invalid username format')
        
        if not cls.validate_email(email):
            raise ValueError('Invalid email format')
        
        if not cls.validate_password_strength(password):
            raise ValueError('Password does not meet strength requirements')
        
        # 检查用户名和邮箱是否已存在
        if cls.query.filter_by(username=username).first():
            raise ValueError('Username already exists')
        
        if cls.query.filter_by(email=email).first():
            raise ValueError('Email already exists')
        
        # 创建用户
        user = cls(
            username=username,
            email=email,
            **kwargs
        )
        user.password = password
        
        return user
    
    @classmethod
    def find_by_username_or_email(cls, identifier):
        """通过用户名或邮箱查找用户"""
        return cls.query.filter(
            db.or_(cls.username == identifier, cls.email == identifier)
        ).first()
    
    @classmethod
    def get_active_users(cls, page=1, per_page=20):
        """获取活跃用户列表"""
        return cls.query.filter_by(is_active=True).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @classmethod
    def search_users(cls, query, page=1, per_page=20):
        """搜索用户"""
        search_filter = db.or_(
            cls.username.contains(query),
            cls.email.contains(query),
            cls.nickname.contains(query)
        )
        
        return cls.query.filter(search_filter).paginate(
            page=page, per_page=per_page, error_out=False
        )