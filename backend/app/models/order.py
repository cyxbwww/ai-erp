"""订单主表模型文件：定义 orders 表结构，用于存储订单基础信息。"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    """订单主表：保存订单编号、客户、状态、总金额等信息。"""

    __tablename__ = 'orders'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='订单主键编号')
    # 订单编号
    order_no: Mapped[str] = mapped_column(String(40), unique=True, index=True, comment='订单编号')
    # 关联客户编号
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), index=True, comment='客户编号')
    # 订单状态：draft/confirmed/completed/cancelled
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True, comment='订单状态英文枚举值')
    # 订单总金额
    total_amount: Mapped[float] = mapped_column(Float, default=0, comment='订单总金额')
    # 订单备注
    remark: Mapped[str] = mapped_column(Text, default='', comment='订单备注')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='创建时间')
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

