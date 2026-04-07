from datetime import datetime, timedelta, timezone
from typing import Any
import base64
import hashlib
import hmac
import secrets

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_HOURS = 8
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    payload = base64.b64encode(salt + digest).decode('ascii')
    return f'pbkdf2_sha256${PBKDF2_ITERATIONS}${payload}'


def verify_password(plain_password: str, hashed_password: str) -> bool:
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


def build_access_token(payload: dict[str, Any], expires_hours: int = ACCESS_TOKEN_EXPIRE_HOURS) -> str:
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        return None
