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


class TaskExecutionAgent(BaseAgent):
    """task_execution_agent 实现。"""

    name = 'task_execution_agent'

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """根据上游策略输出生成可执行任务。"""
        _ = db
        customer_id = int(request.context.get('customer_id') or 0)
        followup_strategy = previous_outputs.get('followup_strategy_agent', {})
        if not isinstance(followup_strategy, dict):
            followup_strategy = {}
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
            fallback_data=fallback
        )
        normalized = self._normalize(llm_data, fallback_customer_id=customer_id)
        return normalized.model_dump()

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

