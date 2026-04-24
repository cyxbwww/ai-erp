"""安全工具文件：提供密码哈希、访问令牌与刷新令牌的生成和解析能力。"""

from datetime import datetime, timedelta, timezone
from typing import Any
import base64
import hashlib
import hmac
import secrets

from jose import JWTError, jwt

from app.core.config import settings

# JWT 配置统一来自 settings，避免安全参数散落在多个文件里。
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
ACCESS_TOKEN_EXPIRE_HOURS = max(1, ACCESS_TOKEN_EXPIRE_MINUTES // 60)
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """对明文密码进行 PBKDF2 加盐哈希。"""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    payload = base64.b64encode(salt + digest).decode('ascii')
    return f'pbkdf2_sha256${PBKDF2_ITERATIONS}${payload}'


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。"""
    try:
        scheme, iterations_str, payload = hashed_password.split('$', 2)
        if scheme != 'pbkdf2_sha256':
            return False
        iterations = int(iterations_str)
        raw = base64.b64decode(payload.encode('ascii'))
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def build_access_token(payload: dict[str, Any], expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """生成访问令牌，默认有效期由 ACCESS_TOKEN_EXPIRE_MINUTES 控制。"""
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({'exp': expire, 'token_type': 'access'})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """解析访问令牌，失败时返回 None。"""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def build_refresh_token(payload: dict[str, Any], expires_days: int = REFRESH_TOKEN_EXPIRE_DAYS) -> str:
    """生成刷新令牌，默认有效期 7 天。"""
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    to_encode.update({'exp': expire, 'token_type': 'refresh'})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    """解析刷新令牌，失败时返回 None。"""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
