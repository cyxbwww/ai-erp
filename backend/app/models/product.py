"""商品模型文件：定义 products 表结构，用于维护订单前置的商品主数据。"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    """商品主数据表：存储商品基础信息、销售信息与库存信息。"""

    __tablename__ = 'products'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='商品主键编号')
    # 商品名称
    name: Mapped[str] = mapped_column(String(120), index=True, comment='商品名称')
    # 商品编码（建议业务唯一）
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True, comment='商品编码')
    # 商品分类：software/service/hardware/other
    category: Mapped[str] = mapped_column(String(30), default='software', index=True, comment='商品分类英文枚举值')
    # 规格型号
    spec_model: Mapped[str] = mapped_column(String(120), default='', comment='规格型号')
    # 销售单价
    sale_price: Mapped[float] = mapped_column(Float, default=0, comment='销售单价')
    # 单位：set/year/month/license/item
    unit: Mapped[str] = mapped_column(String(30), default='set', comment='销售单位英文枚举值')
    # 库存数量
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, comment='库存数量')
    # 状态：enabled/disabled
    status: Mapped[str] = mapped_column(String(20), default='enabled', index=True, comment='商品状态英文枚举值')
    # 备注
    remark: Mapped[str] = mapped_column(Text, default='', comment='商品备注信息')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='创建时间')
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

