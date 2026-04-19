"""记忆记录模型：用于保存客户相关的短期分析记忆。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MemoryRecord(Base):
    """记忆表：按客户沉淀最近几次 AI 分析与策略摘要。"""

    __tablename__ = 'memory_records'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='记忆主键编号')
    # 客户编号
    customer_id: Mapped[int] = mapped_column(Integer, index=True, comment='客户编号')
    # 场景
    scene: Mapped[str] = mapped_column(String(60), default='customer_detail', index=True, comment='场景')
    # 记忆类型：customer_analysis / followup_strategy
    memory_type: Mapped[str] = mapped_column(String(60), index=True, comment='记忆类型')
    # 摘要
    summary: Mapped[str] = mapped_column(Text, default='', comment='记忆摘要')
    # 关键点 JSON
    key_points_json: Mapped[str] = mapped_column(Text, default='[]', comment='关键点 JSON 字符串')
    # 来源调用记录编号（关联 ai_records.id）
    source_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment='来源 AI 调用记录编号')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, comment='创建时间')

