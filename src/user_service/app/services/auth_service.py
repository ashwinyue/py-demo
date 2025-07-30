from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.user_service import UserService
from app.core.config import get_settings

settings = get_settings()

class AuthService:
    """认证服务层"""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        # 支持用户名或邮箱登录
        user = UserService.get_user_by_username(db, username)
        if not user:
            user = UserService.get_user_by_email(db, username)
        
        if not user:
            return None
        
        # 检查账户状态
        if not user.is_active:
            raise ValueError("账户已被禁用")
        
        # 检查账户是否被锁定
        if UserService.is_account_locked(user):
            raise ValueError("账户已被锁定，请稍后再试")
        
        # 验证密码
        if not user.verify_password(password):
            # 增加登录尝试次数
            UserService.increment_login_attempts(db, user.id)
            return None
        
        # 更新最后登录时间
        UserService.update_last_login(db, user.id)
        
        return user
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """根据令牌获取当前用户"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            user_id = int(user_id)
        except ValueError:
            return None
        
        user = UserService.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """刷新访问令牌"""
        payload = AuthService.verify_token(refresh_token)
        if not payload:
            return None
        
        # 检查是否为刷新令牌
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # 创建新的访问令牌
        access_token = AuthService.create_access_token(
            data={"sub": str(user_id)}
        )
        
        return access_token
    
    @staticmethod
    def create_password_reset_token(user_id: int) -> str:
        """创建密码重置令牌"""
        expire = datetime.utcnow() + timedelta(hours=1)  # 1小时有效期
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "password_reset"
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[int]:
        """验证密码重置令牌"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        # 检查是否为密码重置令牌
        if payload.get("type") != "password_reset":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            return int(user_id)
        except ValueError:
            return None
    
    @staticmethod
    def create_email_verification_token(user_id: int) -> str:
        """创建邮箱验证令牌"""
        expire = datetime.utcnow() + timedelta(hours=24)  # 24小时有效期
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "email_verification"
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_email_verification_token(token: str) -> Optional[int]:
        """验证邮箱验证令牌"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        # 检查是否为邮箱验证令牌
        if payload.get("type") != "email_verification":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            return int(user_id)
        except ValueError:
            return None