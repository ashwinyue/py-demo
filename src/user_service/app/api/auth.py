# -*- coding: utf-8 -*-
"""
用户认证相关API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.redis_service import redis_service
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm, VerifyEmailRequest
)
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import MessageResponse
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()
router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        user = UserService.create_user(db, user_data)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            bio=user.bio,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        user = AuthService.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 创建访问令牌和刷新令牌
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # 缓存用户会话
        session_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        redis_service.set_user_session(user.id, session_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_data: RefreshTokenRequest):
    """刷新访问令牌"""
    access_token = AuthService.refresh_access_token(refresh_data.refresh_token)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_data.refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """用户登出"""
    token = credentials.credentials
    
    # 获取当前用户
    user = AuthService.get_current_user(db, token)
    if user:
        # 删除用户会话
        redis_service.delete_user_session(user.id)
    
    # 将令牌加入黑名单
    redis_service.blacklist_token(token)
    
    return MessageResponse(message="登出成功")

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    token = credentials.credentials
    
    # 检查令牌是否在黑名单中
    if redis_service.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效"
        )
    
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        bio=user.bio,
        phone=user.phone,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at
    )