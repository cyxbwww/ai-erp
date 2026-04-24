"""任务服务文件：封装 AI 草稿确认后的任务创建逻辑。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskFromAIDraftCreate


class TaskService:
    """任务服务：当前只实现 AI 草稿确认创建的最小闭环。"""

    VALID_PRIORITIES = {'高', '中', '低'}

    @staticmethod
    def create_from_ai_draft(db: Session, payload: TaskFromAIDraftCreate, current_user: User) -> dict:
        """根据 AI task_payload 创建真实任务，必须由用户确认后调用。"""
        customer_id = int(payload.related_customer_id or 0)
        if customer_id > 0:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError('关联客户不存在')

        description = (payload.description or '').strip()
        reminder_text = (payload.reminder_text or '').strip()
        if reminder_text and reminder_text not in description:
            # 当前任务表不单独存提醒文案，先合并到描述中，避免信息丢失。
            description = f'{description}\n提醒：{reminder_text}'.strip()

        task = Task(
            title=(payload.title or '').strip(),
            description=description,
            priority=TaskService._normalize_priority(payload.priority),
            status='pending',
            owner=(payload.owner or current_user.username or '销售负责人').strip(),
            due_time=TaskService._parse_datetime(payload.due_time),
            customer_id=customer_id or None,
            source='ai_agent_confirmed',
            created_by=current_user.id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return TaskService.serialize(task)

    @staticmethod
    def list_by_customer(db: Session, customer_id: int, status: str = '') -> list[dict]:
        """按客户查询关联任务列表，当前仅提供最小展示所需字段。"""
        query = db.query(Task).filter(Task.customer_id == customer_id)
        clean_status = (status or '').strip()
        if clean_status:
            query = query.filter(Task.status == clean_status)

        rows = query.order_by(desc(Task.created_at), desc(Task.id)).all()
        return [TaskService.serialize(row) for row in rows]

    @staticmethod
    def serialize(task: Task) -> dict:
        """将任务模型转换为接口返回结构。"""
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'owner': task.owner,
            'due_time': task.due_time.strftime('%Y-%m-%d %H:%M:%S') if task.due_time else '',
            'customer_id': task.customer_id,
            'source': task.source,
            'created_by': task.created_by,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else '',
            'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else ''
        }

    @staticmethod
    def _normalize_priority(value: str) -> str:
        """标准化优先级，防止 AI 或前端传入异常值。"""
        priority = (value or '中').strip()
        return priority if priority in TaskService.VALID_PRIORITIES else '中'

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """解析前端传入的截止时间字符串。"""
        if not value:
            return None
        clean_value = value.strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(clean_value, fmt)
            except ValueError:
                continue
        return None
