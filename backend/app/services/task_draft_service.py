"""任务草稿服务：为 AI 任务建议预留真实落地扩展点。"""

from __future__ import annotations

from typing import Any


class TaskDraftService:
    """任务草稿服务：当前只生成结构化草稿，不做数据库落库。"""

    @staticmethod
    def build_customer_followup_draft(
        task_output: dict[str, Any],
        request_context: dict[str, Any]
    ) -> dict[str, Any]:
        """将客户跟进任务建议转换为统一任务草稿结构。"""
        related_customer_id = int(
            task_output.get('related_customer_id')
            or request_context.get('customer_id')
            or 0
        )
        return {
            # 草稿类型使用英文枚举，便于后续对接真实任务表。
            'draft_type': 'customer_followup_task',
            # 以下字段直接来自任务建议，保证前端可以稳定展示。
            'title': str(task_output.get('title', '')).strip() or '客户跟进任务',
            'description': str(task_output.get('description', '')).strip(),
            'priority': str(task_output.get('priority', '中')).strip() or '中',
            'owner': str(task_output.get('suggested_owner', '销售负责人')).strip() or '销售负责人',
            'due_time': str(task_output.get('suggested_due_time', '')).strip(),
            'reminder_text': str(task_output.get('reminder_text', '')).strip(),
            'related_customer_id': max(related_customer_id, 0),
            # source 标识该草稿来自 AI Agent，后续可用于审计和筛选。
            'source': 'ai_agent_draft',
            # 当前仓库暂无真实任务表，因此本阶段只声明不可直接持久化。
            'can_persist': False,
            'persist_service': 'TaskDraftService',
            'persist_note': '当前仓库暂无真实任务表，后续可在 TaskDraftService 内接入真实落库逻辑。'
        }

    @staticmethod
    def build_task_payload(task_draft: dict[str, Any]) -> dict[str, Any]:
        """构建未来真实落库可复用的结构化参数。"""
        return {
            # payload 字段尽量贴近未来 tasks 表可能需要的最小参数。
            'task_type': str(task_draft.get('draft_type', '')).strip(),
            'title': str(task_draft.get('title', '')).strip(),
            'description': str(task_draft.get('description', '')).strip(),
            'priority': str(task_draft.get('priority', '')).strip(),
            'owner': str(task_draft.get('owner', '')).strip(),
            'due_time': str(task_draft.get('due_time', '')).strip(),
            'reminder_text': str(task_draft.get('reminder_text', '')).strip(),
            'related_customer_id': int(task_draft.get('related_customer_id') or 0),
            'source': str(task_draft.get('source', 'ai_agent_draft')).strip() or 'ai_agent_draft'
        }
