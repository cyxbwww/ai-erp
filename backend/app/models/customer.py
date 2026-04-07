"""客户模型文件：定义 customers 表结构，用于存储客户主数据。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Customer(Base):
    """客户主数据表：保存客户基础档案与跟进状态信息。"""

    __tablename__ = 'customers'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='客户主键编号')
    # 客户名称
    name: Mapped[str] = mapped_column(String(100), index=True, comment='客户名称')
    # 联系人
    contact_name: Mapped[str] = mapped_column(String(60), default='', index=True, comment='客户联系人姓名')
    # 联系电话
    phone: Mapped[str] = mapped_column(String(30), index=True, comment='客户联系电话')
    # 联系邮箱
    email: Mapped[str] = mapped_column(String(120), default='', comment='客户联系邮箱')
    # 所属公司
    company: Mapped[str] = mapped_column(String(120), default='', comment='客户所属公司名称')
    # 客户等级：normal/vip/strategic
    level: Mapped[str] = mapped_column(String(20), default='normal', comment='客户等级英文枚举值')
    # 客户状态：active/closed/lost
    status: Mapped[str] = mapped_column(String(20), default='active', comment='客户跟进状态英文枚举值')
    # 来源渠道：manual/sales/campaign/import
    source: Mapped[str] = mapped_column(String(30), default='manual', comment='客户来源英文枚举值')
    # 负责人
    owner_name: Mapped[str] = mapped_column(String(60), default='', index=True, comment='客户负责人姓名')
    # 最近跟进时间
    last_follow_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='最近一次跟进时间')
    # 备注信息
    remark: Mapped[str] = mapped_column(Text, default='', comment='客户备注信息')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='创建时间')
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
