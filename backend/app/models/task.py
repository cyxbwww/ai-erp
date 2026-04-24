"""任务模型文件：定义 tasks 表结构，用于承接 AI 确认后的真实业务任务。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Task(Base):
    """任务表：保存用户确认后的销售待办任务。"""

    __tablename__ = 'tasks'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='任务主键编号')
    # 任务标题
    title: Mapped[str] = mapped_column(String(120), index=True, comment='任务标题')
    # 任务描述
    description: Mapped[str] = mapped_column(Text, default='', comment='任务描述')
    # 优先级：高/中/低
    priority: Mapped[str] = mapped_column(String(20), default='中', index=True, comment='任务优先级中文值')
    # 任务状态：pending/processing/completed/cancelled
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True, comment='任务状态英文枚举值')
    # 任务负责人展示名
    owner: Mapped[str] = mapped_column(String(60), default='', index=True, comment='任务负责人展示名')
    # 截止时间
    due_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True, comment='任务截止时间')
    # 关联客户编号
    customer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('customers.id'), nullable=True, index=True, comment='关联客户编号')
    # 来源标记：ai_agent_confirmed/manual 等
    source: Mapped[str] = mapped_column(String(40), default='manual', index=True, comment='任务来源标记')
    # 创建人编号
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id'), nullable=True, index=True, comment='创建人编号')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, comment='创建时间')
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
