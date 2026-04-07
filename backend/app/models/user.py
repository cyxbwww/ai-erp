"""用户模型文件：定义 users 表结构，用于登录鉴权与权限识别。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """系统用户表：保存账号、角色与启用状态。"""

    __tablename__ = 'users'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='用户主键编号')
    # 登录用户名
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment='登录用户名')
    # 密码哈希
    password: Mapped[str] = mapped_column(String(255), comment='密码哈希值')
    # 用户角色
    role: Mapped[str] = mapped_column(String(50), default='user', index=True, comment='用户角色标识')
    # 是否启用
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用账号')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='创建时间')
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
