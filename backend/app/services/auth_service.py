"""认证服务文件：封装登录鉴权与管理员初始化逻辑。"""

from sqlalchemy.orm import Session

from app.core.security import build_access_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    """认证业务服务：处理管理员初始化与用户登录。"""

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
    def login(db: Session, username: str, password: str) -> dict:
        """账号登录并返回访问令牌及权限集合。"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError('用户名或密码错误')
        if not user.is_active:
            raise ValueError('账号已禁用')
        if not verify_password(password, user.password):
            raise ValueError('用户名或密码错误')

        token = build_access_token({'user_id': user.id, 'username': user.username, 'role': user.role})

        # 基于角色的权限扩展点：后续可从角色、菜单、按钮权限表动态组装权限点。
        permissions = ['dashboard:view']
        if user.role == 'admin':
            permissions.extend(['customer:*', 'product:*', 'order:*'])

        return {
            'token': token,
            'username': user.username,
            'role': user.role,
            'permissions': permissions
        }
