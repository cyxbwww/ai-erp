"""客户服务文件：封装客户列表、详情与增删改业务逻辑。"""

from datetime import datetime, timedelta

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    """客户模块业务服务：封装查询、增删改、序列化等核心逻辑。"""

    @staticmethod
    def list_customers(
        db: Session,
        keyword: str,
        level: str,
        status: str,
        source: str,
        owner_name: str,
        created_start: str,
        created_end: str,
        follow_start: str,
        follow_end: str,
        page: int,
        page_size: int
    ) -> dict:
        """客户列表查询：支持关键词、枚举筛选、时间范围与分页。"""
        query = db.query(Customer)

        # 关键词在客户名称、联系人、手机号、邮箱、公司五个字段中做模糊匹配。
        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(
                or_(
                    Customer.name.like(like_keyword),
                    Customer.contact_name.like(like_keyword),
                    Customer.phone.like(like_keyword),
                    Customer.email.like(like_keyword),
                    Customer.company.like(like_keyword)
                )
            )

        if level:
            query = query.filter(Customer.level == level)
        if status:
            query = query.filter(Customer.status == status)
        if source:
            query = query.filter(Customer.source == source)
        if owner_name:
            query = query.filter(Customer.owner_name.like(f'%{owner_name}%'))

        created_start_dt = CustomerService._parse_date_start(created_start)
        created_end_dt = CustomerService._parse_date_end(created_end)
        if created_start_dt:
            query = query.filter(Customer.created_at >= created_start_dt)
        if created_end_dt:
            query = query.filter(Customer.created_at <= created_end_dt)

        follow_start_dt = CustomerService._parse_date_start(follow_start)
        follow_end_dt = CustomerService._parse_date_end(follow_end)
        if follow_start_dt:
            query = query.filter(Customer.last_follow_at.is_not(None), Customer.last_follow_at >= follow_start_dt)
        if follow_end_dt:
            query = query.filter(Customer.last_follow_at.is_not(None), Customer.last_follow_at <= follow_end_dt)

        total = query.with_entities(func.count(Customer.id)).scalar() or 0
        items = (
            query.order_by(desc(Customer.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            'list': [CustomerService.serialize(item) for item in items],
            'total': total,
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Customer | None:
        """按编号获取客户详情。"""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def create_customer(db: Session, payload: CustomerCreate) -> dict:
        """创建客户。"""
        customer = Customer(
            name=payload.name,
            contact_name=payload.contact_name,
            phone=payload.phone,
            email=payload.email or '',
            company=payload.company,
            level=payload.level,
            status=payload.status,
            source=payload.source,
            owner_name=payload.owner_name,
            last_follow_at=CustomerService._parse_datetime(payload.last_follow_at),
            remark=payload.remark
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return CustomerService.serialize(customer)

    @staticmethod
    def update_customer(db: Session, payload: CustomerUpdate) -> dict | None:
        """更新客户，未找到返回 None。"""
        customer = CustomerService.get_customer(db, payload.id)
        if not customer:
            return None

        customer.name = payload.name
        customer.contact_name = payload.contact_name
        customer.phone = payload.phone
        customer.email = payload.email or ''
        customer.company = payload.company
        customer.level = payload.level
        customer.status = payload.status
        customer.source = payload.source
        customer.owner_name = payload.owner_name
        customer.last_follow_at = CustomerService._parse_datetime(payload.last_follow_at)
        customer.remark = payload.remark

        db.commit()
        db.refresh(customer)
        return CustomerService.serialize(customer)

    @staticmethod
    def delete_customer(db: Session, customer_id: int) -> bool:
        """删除客户，删除成功返回 True。"""
        customer = CustomerService.get_customer(db, customer_id)
        if not customer:
            return False

        db.delete(customer)
        db.commit()
        return True

    @staticmethod
    def serialize(customer: Customer) -> dict:
        """数据库对象转接口返回结构。"""
        return {
            'id': customer.id,
            'name': customer.name,
            'contact_name': customer.contact_name,
            'phone': customer.phone,
            'email': customer.email,
            'company': customer.company,
            'level': customer.level,
            'status': customer.status,
            'source': customer.source,
            'owner_name': customer.owner_name,
            'last_follow_at': customer.last_follow_at.strftime('%Y-%m-%d %H:%M:%S') if customer.last_follow_at else '',
            'remark': customer.remark,
            'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else '',
            'updated_at': customer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if customer.updated_at else ''
        }

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """解析字符串日期时间为 datetime。"""
        if not value:
            return None
        value = value.strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_date_start(value: str) -> datetime | None:
        """解析日期起始时间（当天 00:00:00）。"""
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return None

    @staticmethod
    def _parse_date_end(value: str) -> datetime | None:
        """解析日期结束时间（当天 23:59:59）。"""
        start = CustomerService._parse_date_start(value)
        if not start:
            return None
        return start + timedelta(days=1) - timedelta(seconds=1)
