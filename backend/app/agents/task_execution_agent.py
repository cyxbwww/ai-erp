"""任务执行 Agent：将跟进策略转换为结构化业务任务。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.prompts.agent_prompts import AgentPrompts
from app.schemas.agent import TaskExecutionOutput
from app.schemas.ai_chat import AIChatRequest
from app.services.llm_service import LLMService
from app.services.task_draft_service import TaskDraftService


class TaskExecutionAgent(BaseAgent):
    """task_execution_agent 实现。"""

    name = 'task_execution_agent'
    description = '将跟进策略转换为可执行的销售任务建议。'
    supported_scenes = ['customer_detail']
    dependencies = ['followup_strategy_agent']

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """根据上游策略输出生成可执行任务。"""
        _ = db
        customer_id = int(request.context.get('customer_id') or 0)
        followup_strategy = previous_outputs.get('followup_strategy_agent', {})
        if not isinstance(followup_strategy, dict):
            followup_strategy = {}
        has_followup_strategy = bool(followup_strategy) and not bool(followup_strategy.get('error'))
        customer_insight = previous_outputs.get('customer_insight_agent', {})
        if not isinstance(customer_insight, dict):
            customer_insight = {}

        fallback = self._build_fallback(customer_id=customer_id, followup_strategy=followup_strategy)
        prompt = AgentPrompts.build_task_execution_prompt(
            user_message=request.user_message,
            customer_id=customer_id,
            followup_strategy=followup_strategy,
            customer_insight=customer_insight
        )
        llm_data = LLMService.chat_json(
            system_prompt=AgentPrompts.AGENT_JSON_SYSTEM_PROMPT,
            user_prompt=prompt,
            fallback_data=fallback,
            # 任务建议由客户跟进策略派生，日志按客户跟进任务建议归类。
            module='customer',
            task_type='follow_task'
        )
        normalized = self._normalize(llm_data, fallback_customer_id=customer_id)
        output = normalized.model_dump()
        # 第二阶段新增任务草稿扩展点：保留原顶层任务字段，同时补充未来任务中心可复用结构。
        task_draft = TaskDraftService.build_customer_followup_draft(
            task_output=output,
            request_context=request.context
        )
        output['task_draft'] = task_draft
        output['task_payload'] = TaskDraftService.build_task_payload(task_draft)
        if has_followup_strategy:
            return self.attach_execution_meta(
                output,
                status='success',
                confidence=0.8,
                next_recommendation='请销售负责人确认任务内容后进入待办流程。',
                message='任务建议生成完成。'
            )
        return self.attach_execution_meta(
            output,
            status='partial_failed',
            confidence=0.5,
            next_recommendation='建议先生成跟进策略，再确认任务内容。',
            message='缺少有效跟进策略，已生成兜底任务建议。'
        )

    @staticmethod
    def _build_fallback(customer_id: int, followup_strategy: dict[str, Any]) -> dict[str, Any]:
        """构建任务兜底结果。"""
        next_actions = followup_strategy.get('next_action', [])
        if not isinstance(next_actions, list):
            next_actions = []
        description = '；'.join([str(item).strip() for item in next_actions if str(item).strip()][:3])
        due_time = str(followup_strategy.get('recommended_follow_up_time', '')).strip()
        if not due_time:
            due_time = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        priority = str(followup_strategy.get('priority', '中')).strip() or '中'

        return {
            'task_type': 'customer_followup_task',
            'title': '客户跟进任务',
            'description': description or '请根据客户当前状态执行下一步跟进动作。',
            'priority': priority,
            'suggested_owner': '销售负责人',
            'suggested_due_time': due_time,
            'reminder_text': '请在截止前完成客户跟进并同步结果。',
            'related_customer_id': customer_id
        }

    @staticmethod
    def _normalize(data: dict[str, Any], fallback_customer_id: int) -> TaskExecutionOutput:
        """标准化任务输出结构。"""
        related_customer_id = int(data.get('related_customer_id') or fallback_customer_id or 0)
        return TaskExecutionOutput(
            task_type=str(data.get('task_type', 'customer_followup_task')).strip() or 'customer_followup_task',
            title=str(data.get('title', '')).strip() or '客户跟进任务',
            description=str(data.get('description', '')).strip(),
            priority=str(data.get('priority', '中')).strip() or '中',
            suggested_owner=str(data.get('suggested_owner', '销售负责人')).strip() or '销售负责人',
            suggested_due_time=str(data.get('suggested_due_time', '')).strip(),
            reminder_text=str(data.get('reminder_text', '')).strip(),
            related_customer_id=max(related_customer_id, 0)
        )
