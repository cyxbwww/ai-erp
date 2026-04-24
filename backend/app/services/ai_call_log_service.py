"""AI 调用日志服务文件：封装 ai_call_logs 表的写入与查询逻辑。"""

from datetime import datetime, timedelta

from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ai_call_log import AiCallLog
from app.models.customer_follow_record import CustomerFollowRecord


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
        latency_ms: int | None,
        prompt_template_key: str | None = None,
        prompt_version: str | None = None
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
                    latency_ms=latency_ms,
                    prompt_template_key=prompt_template_key,
                    prompt_version=prompt_version
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
    def get_summary(db: Session) -> dict:
        """汇总 AI 效果统计：统计调用成功率、耗时与客户 AI 采纳转化。"""
        total_calls = db.query(func.count(AiCallLog.id)).scalar() or 0
        success_calls = db.query(func.count(AiCallLog.id)).filter(AiCallLog.status == 'success').scalar() or 0
        failed_calls = db.query(func.count(AiCallLog.id)).filter(AiCallLog.status == 'failed').scalar() or 0
        avg_latency = (
            db.query(func.avg(AiCallLog.latency_ms))
            .filter(AiCallLog.latency_ms.is_not(None))
            .scalar()
        )
        customer_follow_advice_calls = (
            db.query(func.count(AiCallLog.id))
            .filter(
                AiCallLog.module == 'customer',
                AiCallLog.task_type == 'follow_advice',
                AiCallLog.status == 'success'
            )
            .scalar()
            or 0
        )
        customer_ai_adopted_count = (
            db.query(func.count(CustomerFollowRecord.id))
            .filter(CustomerFollowRecord.source_type == 'ai_adopted')
            .scalar()
            or 0
        )

        # 百分比口径统一保留 1 位小数，分母为 0 时按 0 返回。
        success_rate = round(success_calls / total_calls * 100, 1) if total_calls else 0
        adoption_rate = round(customer_ai_adopted_count / customer_follow_advice_calls * 100, 1) if customer_follow_advice_calls else 0

        return {
            'total_calls': total_calls,
            'success_calls': success_calls,
            'failed_calls': failed_calls,
            'success_rate': success_rate,
            'avg_latency_ms': round(float(avg_latency), 1) if avg_latency is not None else 0,
            'customer_follow_advice_calls': customer_follow_advice_calls,
            'customer_ai_adopted_count': customer_ai_adopted_count,
            'customer_ai_adoption_rate': adoption_rate
        }

    @staticmethod
    def get_prompt_summary(db: Session) -> list[dict]:
        """按 Prompt 模板维度统计调用效果。"""
        rows = (
            db.query(
                AiCallLog.prompt_template_key.label('prompt_template_key'),
                AiCallLog.prompt_version.label('prompt_version'),
                AiCallLog.module.label('module'),
                AiCallLog.task_type.label('task_type'),
                func.count(AiCallLog.id).label('total_calls'),
                func.sum(case((AiCallLog.status == 'success', 1), else_=0)).label('success_calls'),
                func.sum(case((AiCallLog.status == 'failed', 1), else_=0)).label('failed_calls'),
                func.avg(AiCallLog.latency_ms).label('avg_latency_ms')
            )
            .filter(AiCallLog.prompt_template_key.is_not(None), AiCallLog.prompt_template_key != '')
            .group_by(
                AiCallLog.prompt_template_key,
                AiCallLog.prompt_version,
                AiCallLog.module,
                AiCallLog.task_type
            )
            .order_by(desc('total_calls'))
            .all()
        )

        results: list[dict] = []
        for row in rows:
            total_calls = int(row.total_calls or 0)
            success_calls = int(row.success_calls or 0)
            failed_calls = int(row.failed_calls or 0)
            success_rate = round(success_calls / total_calls * 100, 1) if total_calls else 0
            results.append({
                'prompt_template_key': row.prompt_template_key,
                'prompt_version': row.prompt_version,
                'module': row.module,
                'task_type': row.task_type,
                'total_calls': total_calls,
                'success_calls': success_calls,
                'failed_calls': failed_calls,
                'success_rate': success_rate,
                'avg_latency_ms': round(float(row.avg_latency_ms)) if row.avg_latency_ms is not None else 0
            })
        return results

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
            'prompt_template_key': record.prompt_template_key,
            'prompt_version': record.prompt_version,
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
