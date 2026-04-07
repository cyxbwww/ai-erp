"""认证路由文件：提供登录与当前用户信息接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """登录接口：校验用户名密码并返回令牌。"""
    try:
        data = AuthService.login(db, payload.username, payload.password)
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.get('/me')
def me(current_user: User = Depends(get_current_user)):
    """当前用户信息接口：返回登录用户基础信息与权限点。"""
    return api_success({
        'id': current_user.id,
        'username': current_user.username,
        'role': current_user.role,
        'permissions': ['dashboard:view']
    })
