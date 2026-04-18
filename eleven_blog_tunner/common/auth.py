"""
认证相关业务逻辑
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from eleven_blog_tunner.common.models import User, get_db
from eleven_blog_tunner.core.config import get_settings

settings = get_settings()

# JWT 配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 手动截断密码，确保不超过 72 字节（bcrypt 限制）
    plain_password = plain_password[:72]
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    print(f"Original password length: {len(password)}")
    # 手动截断密码，确保不超过 72 字节（bcrypt 限制）
    password = password[:72]
    print(f"Truncated password length: {len(password)}")
    print(f"Password: {password}")
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print("Password hashed successfully")
        return hashed
    except Exception as e:
        print(f"Error hashing password: {str(e)}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """验证用户"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    # 手动截断密码，确保不超过 72 字节（bcrypt 限制）
    password = password[:72]
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, username: str, email: str, password: str) -> User:
    """创建用户"""
    # 检查用户是否已存在
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError("该邮箱已被注册")
    
    existing_username = get_user_by_username(db, username)
    if existing_username:
        raise ValueError("该用户名已被使用")
    
    # 创建新用户
    # 手动截断密码，确保不超过 72 字节（bcrypt 限制）
    password = password[:72]
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
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
    return user
