"""客户跟进记录模型文件：定义 customer_follow_records 表结构。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomerFollowRecord(Base):
    """客户跟进记录表：记录客户每次跟进内容、结果与计划时间。"""

    __tablename__ = 'customer_follow_records'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='跟进记录主键编号')
    # 关联客户编号
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), index=True, comment='关联客户编号')
    # 跟进类型：call/wechat/visit/email/demo/other
    follow_type: Mapped[str] = mapped_column(String(20), default='call', index=True, comment='跟进类型英文枚举值')
    # 跟进内容
    content: Mapped[str] = mapped_column(Text, default='', comment='本次跟进的沟通内容')
    # 跟进结果
    result: Mapped[str] = mapped_column(String(255), default='', comment='本次跟进结果摘要')
    # 下次跟进时间
    next_follow_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='下次计划跟进时间')
    # 来源类型：manual/ai_adopted
    source_type: Mapped[str] = mapped_column(String(30), default='manual', index=True, comment='跟进记录来源类型')
    # 来源模块：例如 customer_ai，可为空
    source_module: Mapped[str | None] = mapped_column(String(60), nullable=True, comment='跟进记录来源模块')
    # 来源引用编号：预留关联 AI 任务或 AI 调用日志，可为空
    source_ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment='来源引用编号')
    # 跟进人编号
    follow_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), index=True, comment='执行跟进的用户编号')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, comment='记录创建时间')
