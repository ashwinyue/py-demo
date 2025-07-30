from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.redis_service import redis_service
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
from app.schemas.common import MessageResponse
from app.models.user import User

security = HTTPBearer()
router = APIRouter(prefix="/users", tags=["用户管理"])

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """获取当前用户依赖"""
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
    
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """需要管理员权限的依赖"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

@router.get("/", response_model=UserListResponse)
def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取用户列表（管理员）"""
    users = UserService.get_users(db, skip=skip, limit=limit, search=search, is_active=is_active)
    
    user_responses = [
        UserResponse(
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
        for user in users
    ]
    
    return UserListResponse(
        users=user_responses,
        total=len(user_responses),
        skip=skip,
        limit=limit
    )

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户信息"""
    # 只能查看自己的信息或管理员可以查看所有用户
    if current_user.id != user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此用户信息"
        )
    
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
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

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    # 只能更新自己的信息或管理员可以更新所有用户
    if current_user.id != user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此用户信息"
        )
    
    # 非管理员不能修改角色
    if current_user.role != 'admin' and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改用户角色"
        )
    
    try:
        user = UserService.update_user(db, user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 清除用户缓存
        redis_service.delete_user_cache(user_id)
        
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

@router.get("/profile/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """获取我的个人资料"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        role=current_user.role,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login_at=current_user.last_login_at
    )