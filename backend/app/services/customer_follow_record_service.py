"""客户跟进记录服务文件：封装跟进记录的增删改查与客户最近跟进时间同步逻辑。"""

from datetime import datetime

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_follow_record import CustomerFollowRecord
from app.models.user import User
from app.schemas.customer_follow_record import CustomerFollowRecordCreate, CustomerFollowRecordUpdate


class CustomerFollowRecordService:
    """客户跟进记录服务：处理跟进记录列表、详情、新增、编辑、删除。"""

    @staticmethod
    def list_records(
        db: Session,
        customer_id: int,
        keyword: str,
        follow_type: str,
        page: int,
        page_size: int
    ) -> dict:
        """按客户查询跟进记录列表，支持关键词与类型筛选。"""
        query = db.query(CustomerFollowRecord).filter(CustomerFollowRecord.customer_id == customer_id)

        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(
                or_(
                    CustomerFollowRecord.content.like(like_keyword),
                    CustomerFollowRecord.result.like(like_keyword)
                )
            )

        if follow_type:
            query = query.filter(CustomerFollowRecord.follow_type == follow_type)

        total = query.with_entities(func.count(CustomerFollowRecord.id)).scalar() or 0
        items = (
            query.order_by(desc(CustomerFollowRecord.created_at), desc(CustomerFollowRecord.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            'list': [CustomerFollowRecordService.serialize(db, item) for item in items],
            'total': total,
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_record(db: Session, record_id: int) -> CustomerFollowRecord | None:
        """按记录编号获取单条跟进记录。"""
        return db.query(CustomerFollowRecord).filter(CustomerFollowRecord.id == record_id).first()

    @staticmethod
    def create_record(db: Session, payload: CustomerFollowRecordCreate, current_user: User) -> dict:
        """新增跟进记录，并同步客户最近跟进时间。"""
        record = CustomerFollowRecord(
            customer_id=payload.customer_id,
            follow_type=payload.follow_type,
            content=payload.content,
            result=payload.result,
            next_follow_time=CustomerFollowRecordService._parse_datetime(payload.next_follow_time),
            follow_user_id=current_user.id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        CustomerFollowRecordService.sync_customer_last_follow_at(db, payload.customer_id)
        return CustomerFollowRecordService.serialize(db, record)

    @staticmethod
    def update_record(db: Session, payload: CustomerFollowRecordUpdate, current_user: User) -> dict | None:
        """编辑跟进记录，未找到返回 None。"""
        record = CustomerFollowRecordService.get_record(db, payload.id)
        if not record:
            return None

        record.customer_id = payload.customer_id
        record.follow_type = payload.follow_type
        record.content = payload.content
        record.result = payload.result
        record.next_follow_time = CustomerFollowRecordService._parse_datetime(payload.next_follow_time)
        # 更新时记录操作人，便于后续审计追踪。
        record.follow_user_id = current_user.id

        db.commit()
        db.refresh(record)
        CustomerFollowRecordService.sync_customer_last_follow_at(db, payload.customer_id)
        return CustomerFollowRecordService.serialize(db, record)

    @staticmethod
    def delete_record(db: Session, record_id: int) -> bool:
        """删除跟进记录，成功返回 True。"""
        record = CustomerFollowRecordService.get_record(db, record_id)
        if not record:
            return False
        customer_id = record.customer_id
        db.delete(record)
        db.commit()
        CustomerFollowRecordService.sync_customer_last_follow_at(db, customer_id)
        return True

    @staticmethod
    def serialize(db: Session, record: CustomerFollowRecord) -> dict:
        """将跟进记录模型转换为接口返回结构。"""
        follow_user = db.query(User).filter(User.id == record.follow_user_id).first()
        return {
            'id': record.id,
            'customer_id': record.customer_id,
            'follow_type': record.follow_type,
            'content': record.content,
            'result': record.result,
            'next_follow_time': record.next_follow_time.strftime('%Y-%m-%d %H:%M:%S') if record.next_follow_time else '',
            'follow_user_id': record.follow_user_id,
            'follow_user_name': follow_user.username if follow_user else '',
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
        }

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """解析前端传入的日期时间字符串。"""
        if not value:
            return None
        clean_value = value.strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(clean_value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def sync_customer_last_follow_at(db: Session, customer_id: int) -> None:
        """同步客户最近跟进时间，取最新跟进记录创建时间。"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return

        latest = (
            db.query(CustomerFollowRecord)
            .filter(CustomerFollowRecord.customer_id == customer_id)
            .order_by(desc(CustomerFollowRecord.created_at), desc(CustomerFollowRecord.id))
            .first()
        )
        customer.last_follow_at = latest.created_at if latest else None
        db.commit()
