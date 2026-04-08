"""鉴权依赖文件：提供登录态解析与角色校验能力。"""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


class AuthError(Exception):
    """认证异常：用于统一抛出鉴权失败信息。"""



def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    """解析请求头中的 access token 并返回当前用户。"""
    if not authorization or not authorization.startswith('Bearer '):
        raise AuthError('未登录或 token 缺失')

    token = authorization.replace('Bearer ', '', 1)
    payload = decode_access_token(token)
    if not payload:
        raise AuthError('token 无效或已过期')

    # 显式限制仅 access token 可访问业务接口，避免 refresh token 越权使用。
    if payload.get('token_type') != 'access':
        raise AuthError('token 类型不正确')

    user_id = payload.get('user_id')
    if not user_id:
        raise AuthError('token 数据不完整')

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise AuthError('用户不存在或已禁用')

    return user



def require_roles(*allowed_roles: str):
    """角色鉴权依赖：用于需要角色限制的接口。"""

    # 基于角色的权限扩展点：后续可在这里增加菜单与按钮级权限校验。
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not allowed_roles:
            return user
        if user.role not in allowed_roles:
            raise AuthError('无权限访问该资源')
        return user

    return dependency
