"""
认证相关路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Annotated
from pydantic import BaseModel

from eleven_blog_tunner.common.models import get_db
from eleven_blog_tunner.common.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from eleven_blog_tunner.core.config import get_settings
from eleven_blog_tunner.api.routes.common import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    - **username**: 邮箱地址
    - **password**: 密码
    """
    user = authenticate_user(db, request.email, request.password)
    if not user:
        return ErrorResponse.build(
            code="401",
            message="邮箱或密码错误"
        )
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return SuccessResponse.build(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser
            }
        },
        message="登录成功"
    )


@router.post("/register", summary="用户注册")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册
    - **username**: 用户名
    - **email**: 邮箱地址
    - **password**: 密码
    """
    try:
        print(f"Received registration request: username={request.username}, email={request.email}, password_length={len(request.password)}")
        password = request.password[:72]
        print(f"Truncated password length: {len(password)}")
        user = create_user(db, request.username, request.email, password)
        return SuccessResponse.build(
            data={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "created_at": str(user.created_at)
            },
            message="注册成功"
        )
    except ValueError as e:
        print(f"Registration error: {str(e)}")
        return ErrorResponse.bad_request(message=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return ErrorResponse.internal_error(message="注册失败，请稍后重试")


@router.post("/logout", summary="用户注销")
async def logout():
    """
    用户注销
    """
    return SuccessResponse.build(
        data={"message": "注销成功"},
        message="注销成功"
    )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    """
    from jose import JWTError, jwt
    from eleven_blog_tunner.common.auth import SECRET_KEY, ALGORITHM
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    return SuccessResponse.build(
        data={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "last_login_at": str(user.last_login_at) if user.last_login_at else None,
            "created_at": str(user.created_at)
        },
        message="获取用户信息成功"
    )
