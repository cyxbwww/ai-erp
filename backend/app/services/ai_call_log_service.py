"""AI 调用日志服务文件：封装 ai_call_logs 表的写入与查询逻辑。"""

from datetime import datetime, timedelta

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ai_call_log import AiCallLog


class AiCallLogService:
    """AI 调用日志服务：提供独立写入、筛选查询和详情序列化能力。"""

    @staticmethod
    def write_log(
        *,
        module: str | None,
        task_type: str | None,
        prompt: str,
        response: str | None,
        status: str,
        error_message: str | None,
        model_name: str,
        latency_ms: int | None
    ) -> None:
        """写入 AI 调用日志：日志失败不影响原业务结果。"""
        db = SessionLocal()
        try:
            # 使用独立数据库会话，避免 AI 调用日志与业务事务互相影响。
            db.add(
                AiCallLog(
                    module=module,
                    task_type=task_type,
                    prompt=prompt,
                    response=response,
                    status=status,
                    error_message=error_message,
                    model_name=model_name,
                    latency_ms=latency_ms
                )
            )
            db.commit()
        except Exception:
            # 日志属于审计辅助能力，写入失败不能改变 AI 原有成功或失败语义。
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def list_logs(
        db: Session,
        module: str,
        task_type: str,
        status: str,
        keyword: str,
        start_time: str,
        end_time: str,
        page: int,
        page_size: int
    ) -> dict:
        """分页查询 AI 调用日志：支持业务来源、状态、关键词和创建时间筛选。"""
        query = db.query(AiCallLog)

        if module:
            query = query.filter(AiCallLog.module == module)
        if task_type:
            query = query.filter(AiCallLog.task_type == task_type)
        if status:
            query = query.filter(AiCallLog.status == status)
        if keyword:
            like_keyword = f'%{keyword}%'
            # 关键词覆盖提示词、模型响应和错误信息，便于排查具体调用问题。
            query = query.filter(
                or_(
                    AiCallLog.prompt.like(like_keyword),
                    AiCallLog.response.like(like_keyword),
                    AiCallLog.error_message.like(like_keyword)
                )
            )

        start_dt = AiCallLogService._parse_time_start(start_time)
        end_dt = AiCallLogService._parse_time_end(end_time)
        if start_dt:
            query = query.filter(AiCallLog.created_at >= start_dt)
        if end_dt:
            query = query.filter(AiCallLog.created_at <= end_dt)

        total = query.with_entities(func.count(AiCallLog.id)).scalar() or 0
        items = (
            query.order_by(desc(AiCallLog.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': [AiCallLogService.serialize(item, truncate=True) for item in items]
        }

    @staticmethod
    def get_log_detail(db: Session, log_id: int) -> dict | None:
        """查询单条 AI 调用日志详情，未找到时返回 None。"""
        record = db.query(AiCallLog).filter(AiCallLog.id == log_id).first()
        if not record:
            return None
        return AiCallLogService.serialize(record, truncate=False)

    @staticmethod
    def serialize(record: AiCallLog, truncate: bool = False) -> dict:
        """数据库对象转接口返回结构，列表场景会截断长文本。"""
        prompt = record.prompt or ''
        response = record.response
        error_message = record.error_message
        if truncate:
            prompt = AiCallLogService._truncate_text(prompt)
            response = AiCallLogService._truncate_text(response)
            error_message = AiCallLogService._truncate_text(error_message)

        return {
            'id': record.id,
            'module': record.module,
            'task_type': record.task_type,
            'prompt': prompt,
            'response': response,
            'status': record.status,
            'error_message': error_message,
            'model_name': record.model_name,
            'latency_ms': record.latency_ms,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
        }

    @staticmethod
    def _truncate_text(value: str | None, max_length: int = 300) -> str | None:
        """截断长文本：列表接口只展示摘要，详情接口保留完整内容。"""
        if value is None:
            return None
        text = str(value)
        if len(text) <= max_length:
            return text
        return f'{text[:max_length]}...'

    @staticmethod
    def _parse_time_start(value: str) -> datetime | None:
        """解析开始时间，兼容日期和完整日期时间。"""
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
    def _parse_time_end(value: str) -> datetime | None:
        """解析结束时间，日期格式会自动扩展到当天 23:59:59。"""
        if not value:
            return None
        value = value.strip()
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        try:
            return datetime.strptime(value, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            return None
