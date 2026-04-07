"""订单明细模型文件：定义 order_items 表结构，用于存储订单商品明细。"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OrderItem(Base):
    """订单明细表：保存订单中的商品、数量、单价与小计信息。"""

    __tablename__ = 'order_items'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='订单明细主键编号')
    # 关联订单编号
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey('orders.id'), index=True, comment='订单编号')
    # 关联商品编号
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), index=True, comment='商品编号')
    # 冗余商品名称（便于历史追溯）
    product_name: Mapped[str] = mapped_column(String(120), comment='下单时商品名称快照')
    # 冗余商品编码
    product_code: Mapped[str] = mapped_column(String(60), comment='下单时商品编码快照')
    # 冗余商品单位
    unit: Mapped[str] = mapped_column(String(30), default='set', comment='下单时商品单位英文枚举值')
    # 下单单价
    unit_price: Mapped[float] = mapped_column(Float, default=0, comment='下单单价')
    # 下单数量
    quantity: Mapped[int] = mapped_column(Integer, default=1, comment='下单数量')
    # 明细小计
    subtotal: Mapped[float] = mapped_column(Float, default=0, comment='明细小计金额')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='创建时间')

