from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.config import get_settings

settings = get_settings()

class UserService:
    """用户服务层"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        existing_user = db.query(User).filter(
            or_(User.username == user_data.username, User.email == user_data.email)
        ).first()
        
        if existing_user:
            if existing_user.username == user_data.username:
                raise ValueError("用户名已存在")
            if existing_user.email == user_data.email:
                raise ValueError("邮箱已存在")
        
        # 创建新用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            nickname=user_data.nickname,
            phone=user_data.phone
        )
        user.password = user_data.password
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100, 
                  search: Optional[str] = None, is_active: Optional[bool] = None) -> List[User]:
        """获取用户列表"""
        query = db.query(User)
        
        if search:
            query = query.filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.nickname.contains(search)
                )
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        
        # 检查用户名和邮箱唯一性
        if 'username' in update_data:
            existing = db.query(User).filter(
                and_(User.username == update_data['username'], User.id != user_id)
            ).first()
            if existing:
                raise ValueError("用户名已存在")
        
        if 'email' in update_data:
            existing = db.query(User).filter(
                and_(User.email == update_data['email'], User.id != user_id)
            ).first()
            if existing:
                raise ValueError("邮箱已存在")
        
        # 更新字段
        for field, value in update_data.items():
            if field == 'password':
                user.password = value
            else:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户（软删除）"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def verify_user_email(db: Session, user_id: int) -> bool:
        """验证用户邮箱"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def update_last_login(db: Session, user_id: int) -> bool:
        """更新最后登录时间"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        user.login_attempts = 0  # 重置登录尝试次数
        db.commit()
        return True
    
    @staticmethod
    def increment_login_attempts(db: Session, user_id: int) -> bool:
        """增加登录尝试次数"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.login_attempts += 1
        
        # 如果登录尝试次数超过限制，锁定账户
        if user.login_attempts >= settings.max_login_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.account_lock_duration)
        
        db.commit()
        return True
    
    @staticmethod
    def is_account_locked(user: User) -> bool:
        """检查账户是否被锁定"""
        if not user.locked_until:
            return False
        
        return datetime.utcnow() < user.locked_until
    
    @staticmethod
    def unlock_account(db: Session, user_id: int) -> bool:
        """解锁账户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.locked_until = None
        user.login_attempts = 0
        db.commit()
        return True