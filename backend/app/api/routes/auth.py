"""认证路由文件：提供登录、刷新令牌与当前用户信息接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.core.security import decode_refresh_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """登录接口：校验用户名密码并返回 access/refresh 双令牌。"""
    try:
        data = AuthService.login(db, payload.username, payload.password)
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.post('/refresh')
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """刷新接口：使用 refresh token 换取新的 access token。"""
    try:
        token_payload = decode_refresh_token(payload.refresh_token)
        if not token_payload:
            return api_error('refresh token 无效或已过期，请重新登录', code=401)

        # 明确校验 token 类型，防止 access token 误用于刷新接口。
        if token_payload.get('token_type') != 'refresh':
            return api_error('refresh token 类型错误，请重新登录', code=401)

        user_id = token_payload.get('user_id')
        if not user_id:
            return api_error('refresh token 数据不完整，请重新登录', code=401)

        data = AuthService.refresh_token(db, int(user_id))
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc), code=401)


@router.get('/me')
def me(current_user: User = Depends(get_current_user)):
    """当前用户信息接口：返回登录用户基础信息与权限点。"""
    return api_success({
        'id': current_user.id,
        'username': current_user.username,
        'role': current_user.role,
        'permissions': ['dashboard:view']
    })
