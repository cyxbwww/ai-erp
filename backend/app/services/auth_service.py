"""认证服务文件：封装登录鉴权、刷新令牌与管理员初始化逻辑。"""

from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_HOURS,
    build_access_token,
    build_refresh_token,
    hash_password,
    verify_password
)
from app.models.user import User


class AuthService:
    """认证业务服务：处理管理员初始化、用户登录与令牌刷新。"""

    @staticmethod
    def ensure_seed_admin(db: Session) -> None:
        """确保系统存在默认管理员账号。"""
        admin = db.query(User).filter(User.username == 'admin').first()
        if admin:
            # 兼容旧密码格式，统一迁移到当前密码算法。
            if not (admin.password or '').startswith('pbkdf2_sha256$'):
                admin.password = hash_password('123456')
                admin.role = admin.role or 'admin'
                admin.is_active = True
                db.commit()
            return

        admin = User(
            username='admin',
            password=hash_password('123456'),
            role='admin',
            is_active=True
        )
        db.add(admin)
        db.commit()

    @staticmethod
    def _build_token_bundle(user: User, permissions: list[str]) -> dict:
        """统一构造登录和刷新接口返回的令牌载荷。"""
        token_payload = {'user_id': user.id, 'username': user.username, 'role': user.role}
        access_token = build_access_token(token_payload)
        refresh_token = build_refresh_token(token_payload)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            # 兼容历史前端字段，避免影响既有业务代码。
            'token': access_token,
            'username': user.username,
            'role': user.role,
            'permissions': permissions
        }

    @staticmethod
    def login(db: Session, username: str, password: str) -> dict:
        """账号登录并返回访问令牌、刷新令牌及权限集合。"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError('用户名或密码错误')
        if not user.is_active:
            raise ValueError('账号已禁用')
        if not verify_password(password, user.password):
            raise ValueError('用户名或密码错误')

        # 基于角色的权限扩展点：后续可从角色、菜单、按钮权限表动态组装权限点。
        permissions = ['dashboard:view']
        if user.role == 'admin':
            permissions.extend(['customer:*', 'product:*', 'order:*'])

        return AuthService._build_token_bundle(user, permissions)

    @staticmethod
    def refresh_token(db: Session, user_id: int) -> dict:
        """根据 refresh_token 中的用户标识签发新的访问令牌与刷新令牌。"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError('用户不存在或已禁用，请重新登录')

        permissions = ['dashboard:view']
        if user.role == 'admin':
            permissions.extend(['customer:*', 'product:*', 'order:*'])

        return AuthService._build_token_bundle(user, permissions)
