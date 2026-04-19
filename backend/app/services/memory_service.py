"""记忆服务：封装短期记忆读取、格式化与写入能力。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.memory_record import MemoryRecord


class MemoryService:
    """客户短期记忆服务。"""

    @staticmethod
    def list_recent_memories(
        db: Session,
        customer_id: int,
        scene: str = 'customer_detail',
        memory_types: list[str] | None = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """读取客户最近记忆，默认返回最近 5 条。"""
        query = db.query(MemoryRecord).filter(MemoryRecord.customer_id == customer_id)
        if scene:
            query = query.filter(MemoryRecord.scene == scene)
        if memory_types:
            query = query.filter(MemoryRecord.memory_type.in_(memory_types))

        try:
            rows = (
                query.order_by(desc(MemoryRecord.created_at), desc(MemoryRecord.id))
                .limit(max(1, min(limit, 10)))
                .all()
            )
            return [MemoryService.serialize(row) for row in rows]
        except SQLAlchemyError:
            # 表未初始化或数据库异常时返回空记忆，不阻塞主流程。
            return []

    @staticmethod
    def save_memory(
        db: Session,
        customer_id: int,
        scene: str,
        memory_type: str,
        summary: str,
        key_points: list[str] | dict[str, Any] | None = None,
        source_record_id: int | None = None
    ) -> dict[str, Any]:
        """写入一条新记忆。"""
        record = MemoryRecord(
            customer_id=customer_id,
            scene=(scene or 'customer_detail').strip() or 'customer_detail',
            memory_type=(memory_type or '').strip(),
            summary=(summary or '').strip(),
            key_points_json=MemoryService._json_dumps(key_points or []),
            source_record_id=source_record_id
        )
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            return MemoryService.serialize(record)
        except SQLAlchemyError:
            db.rollback()
            return {
                'id': 0,
                'customer_id': customer_id,
                'scene': scene,
                'memory_type': memory_type,
                'summary': summary,
                'key_points': key_points or [],
                'source_record_id': source_record_id,
                'created_at': ''
            }

    @staticmethod
    def format_memories_for_prompt(memories: list[dict[str, Any]]) -> str:
        """将历史记忆转为可直接拼入 Prompt 的文本块。"""
        if not memories:
            return '无历史记忆。'

        lines: list[str] = []
        for idx, item in enumerate(memories, start=1):
            created_at = str(item.get('created_at', ''))
            memory_type = str(item.get('memory_type', ''))
            summary = str(item.get('summary', ''))
            key_points = item.get('key_points', [])
            key_points_text = '无'
            if isinstance(key_points, list):
                key_points_text = '；'.join([str(p).strip() for p in key_points if str(p).strip()][:5]) or '无'
            elif isinstance(key_points, dict):
                pairs: list[str] = []
                for key, value in key_points.items():
                    if isinstance(value, list):
                        value_text = '、'.join([str(v).strip() for v in value if str(v).strip()][:2])
                    else:
                        value_text = str(value).strip()
                    if not value_text:
                        continue
                    pairs.append(f'{key}:{value_text}')
                    if len(pairs) >= 4:
                        break
                key_points_text = '；'.join(pairs) or '无'
            lines.append(f'{idx}. [{memory_type}] 时间:{created_at} 摘要:{summary} 关键点:{key_points_text}')
        return '\n'.join(lines)

    @staticmethod
    def serialize(record: MemoryRecord) -> dict[str, Any]:
        """模型转字典结构。"""
        return {
            'id': record.id,
            'customer_id': record.customer_id,
            'scene': record.scene,
            'memory_type': record.memory_type,
            'summary': record.summary,
            'key_points': MemoryService._json_loads(record.key_points_json, default=[]),
            'source_record_id': record.source_record_id,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
        }

    @staticmethod
    def _json_dumps(data: Any) -> str:
        """对象转 JSON 字符串。"""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return '[]'

    @staticmethod
    def _json_loads(text: str, default: Any) -> Any:
        """JSON 字符串解析。"""
        try:
            return json.loads(text or '')
        except Exception:
            return default
