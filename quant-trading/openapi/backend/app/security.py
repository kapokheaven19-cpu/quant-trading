"""
OpenAPI 平台 - 安全工具（密码、Token、JWT）
"""
import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.models import User, App

# JWT 配置
JWT_SECRET_KEY = secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24小时

# JWT 配置（可选从环境变量读取）
JWT_SECRET_KEY = "openapi-platform-secret-key-change-in-production"


def hash_password(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def generate_app_id() -> str:
    """生成 AppID"""
    return secrets.token_hex(16)  # 32位


def generate_app_secret() -> Tuple[str, str]:
    """生成 AppSecret，返回 (明文, 哈希)"""
    secret = secrets.token_hex(16)  # 32位
    secret_hash = hash_password(secret)
    return secret, secret_hash


def verify_app_secret(plain_secret: str, hashed_secret: str) -> bool:
    """验证 AppSecret"""
    return verify_password(plain_secret, hashed_secret)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT 令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_api_key_signature(app_id: str, app_secret: str, timestamp: str, method: str, path: str) -> str:
    """生成 API 签名
    签名算法: md5(app_id + app_secret + timestamp + method + path)
    """
    sign_str = f"{app_id}{app_secret}{timestamp}{method}{path}"
    return hashlib.md5(sign_str.encode()).hexdigest()


def verify_api_key_signature(
    app_id: str, 
    signature: str, 
    timestamp: str, 
    method: str, 
    path: str,
    app_secret: str
) -> bool:
    """验证 API 签名"""
    expected_signature = create_api_key_signature(app_id, app_secret, timestamp, method, path)
    return secrets.compare_digest(signature, expected_signature)


def get_current_user(db: Session, token: str) -> Optional[User]:
    """从 JWT Token 获取当前用户"""
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    return db.query(User).filter(User.id == user_id).first()


def generate_jwt_token(user_id: int, app_id: str = None) -> str:
    """生成 JWT Token (用于接口认证)"""
    data = {
        "sub": str(user_id),
        "type": "access"
    }
    if app_id:
        data["app_id"] = str(app_id)
    
    return create_access_token(data, expires_delta=timedelta(hours=2))
