"""AI 调用追踪服务：负责 AI 调用过程结构化落库。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_record import AIRecord
from app.schemas.ai_chat import AIChatRequest, AIExecutionPlan


class AITraceService:
    """AI 调用追踪服务。"""

    @staticmethod
    def start_record(db: Session, request: AIChatRequest) -> AIRecord:
        """创建一条初始调用记录。"""
        record = AIRecord(
            scene=(request.scene or '').strip(),
            user_message=(request.user_message or '').strip(),
            context_json=AITraceService._json_dumps(request.context),
            task_type='',
            plan_json='{}',
            agent_outputs_json='{}',
            agent_details_json='[]',
            final_summary='',
            total_duration_ms=0,
            status='running',
            error_message=''
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def finish_record(
        db: Session,
        record: AIRecord,
        task_type: str,
        plan: AIExecutionPlan,
        agent_outputs: dict[str, Any],
        agent_details: list[dict[str, Any]],
        final_summary: str,
        total_duration_ms: int,
        status: str,
        error_message: str = ''
    ) -> None:
        """更新调用记录为最终状态。"""
        record.task_type = (task_type or '').strip()
        record.plan_json = AITraceService._json_dumps(plan.model_dump())
        record.agent_outputs_json = AITraceService._json_dumps(agent_outputs)
        record.agent_details_json = AITraceService._json_dumps(agent_details)
        record.final_summary = final_summary or ''
        record.total_duration_ms = max(int(total_duration_ms or 0), 0)
        record.status = (status or 'success').strip()
        record.error_message = (error_message or '').strip()
        db.add(record)
        db.commit()

    @staticmethod
    def build_input_preview(
        request: AIChatRequest,
        previous_outputs: dict[str, Any],
        agent_name: str
    ) -> dict[str, Any]:
        """构建 Agent 输入摘要，便于后续回溯。"""
        preview: dict[str, Any] = {
            'scene': request.scene,
            'user_message': request.user_message[:200],
            'context_keys': sorted(list(request.context.keys()))
        }

        # 按 Agent 类型补充关键上游输入摘要，避免存整段冗余数据。
        if agent_name == 'followup_strategy_agent':
            insight = previous_outputs.get('customer_insight_agent', {})
            knowledge = previous_outputs.get('knowledge_rag_agent', {})
            preview['customer_stage'] = str(insight.get('customer_stage', '')) if isinstance(insight, dict) else ''
            preview['knowledge_refs'] = len(knowledge.get('references', [])) if isinstance(knowledge, dict) else 0
        elif agent_name == 'knowledge_rag_agent':
            preview['top_k'] = int(request.context.get('top_k') or 4)
        elif agent_name == 'order_analysis_agent':
            preview['order_id'] = request.context.get('order_id')
        elif agent_name == 'customer_insight_agent':
            preview['customer_id'] = request.context.get('customer_id')
        elif agent_name == 'task_execution_agent':
            followup = previous_outputs.get('followup_strategy_agent', {})
            preview['customer_id'] = request.context.get('customer_id')
            preview['has_followup_strategy'] = isinstance(followup, dict) and bool(followup)
            preview['followup_priority'] = str(followup.get('priority', '')) if isinstance(followup, dict) else ''

        return preview

    @staticmethod
    def detect_fallback(agent_output: dict[str, Any]) -> bool:
        """检测 Agent 输出是否触发了 fallback。"""
        if not isinstance(agent_output, dict):
            return False

        # 常见标记字段：source / ai_source。
        source = str(agent_output.get('source', '')).lower().strip()
        ai_source = str(agent_output.get('ai_source', '')).lower().strip()
        if 'fallback' in source or 'fallback' in ai_source:
            return True

        # error 输出也视为降级执行。
        if 'error' in agent_output:
            return True
        return False

    @staticmethod
    def has_error(agent_outputs: dict[str, Any]) -> bool:
        """判断是否存在 Agent 级错误输出。"""
        for output in agent_outputs.values():
            if isinstance(output, dict) and output.get('error'):
                return True
        return False

    @staticmethod
    def _json_dumps(data: Any) -> str:
        """将对象安全序列化为 JSON 字符串。"""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return json.dumps({'serialize_error': True}, ensure_ascii=False)
