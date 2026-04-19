"""跟进策略 Agent：基于客户洞察与历史记忆输出跟进策略。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.prompts.agent_prompts import AgentPrompts
from app.schemas.agent import FollowupStrategyOutput
from app.schemas.ai_chat import AIChatRequest
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.tools.agent_query_tools import AgentQueryTools


class FollowupStrategyAgent(BaseAgent):
    """followup_strategy_agent 实现。"""

    name = 'followup_strategy_agent'

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """执行跟进策略生成逻辑。"""
        customer_id = int(request.context.get('customer_id') or 0)
        customer_context: dict[str, Any] = {}
        if customer_id > 0:
            try:
                customer_context = AgentQueryTools.get_customer_insight_context(db=db, customer_id=customer_id, follow_limit=5)
            except Exception:
                customer_context = {}

        customer_insight = previous_outputs.get('customer_insight_agent', {})
        if not isinstance(customer_insight, dict):
            customer_insight = {}
        knowledge_support = previous_outputs.get('knowledge_rag_agent', {})
        if not isinstance(knowledge_support, dict):
            knowledge_support = {}

        memories = []
        if customer_id > 0:
            memories = MemoryService.list_recent_memories(
                db=db,
                customer_id=customer_id,
                scene='customer_detail',
                memory_types=['followup_strategy', 'customer_analysis'],
                limit=5
            )
        memory_context = MemoryService.format_memories_for_prompt(memories)

        fallback = self._build_fallback(customer_insight=customer_insight)
        prompt = AgentPrompts.build_followup_strategy_prompt(
            user_message=request.user_message,
            customer_context=customer_context,
            customer_insight=customer_insight,
            knowledge_support=knowledge_support,
            memory_context=memory_context
        )
        llm_data = LLMService.chat_json(
            system_prompt=AgentPrompts.AGENT_JSON_SYSTEM_PROMPT,
            user_prompt=prompt,
            fallback_data=fallback
        )
        normalized = self._normalize(llm_data)
        output = normalized.model_dump()

        # 生成策略后写入记忆，失败不阻塞主流程。
        if customer_id > 0:
            try:
                source_record_id = int(request.context.get('source_record_id') or 0) or None
                MemoryService.save_memory(
                    db=db,
                    customer_id=customer_id,
                    scene='customer_detail',
                    memory_type='followup_strategy',
                    summary=output.get('strategy_summary', ''),
                    key_points={
                        'priority': output.get('priority', ''),
                        'next_action': output.get('next_action', []),
                        'risk_alert': output.get('risk_alert', []),
                        'recommended_follow_up_time': output.get('recommended_follow_up_time', '')
                    },
                    source_record_id=source_record_id
                )
            except Exception:
                pass

        return output

    @staticmethod
    def _build_fallback(customer_insight: dict[str, Any]) -> dict[str, Any]:
        """构建策略兜底数据。"""
        risks = FollowupStrategyAgent._ensure_str_list(customer_insight.get('risks'))
        suggestions = FollowupStrategyAgent._ensure_str_list(customer_insight.get('suggestions'))
        next_time = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        return {
            'priority': '中',
            'next_action': suggestions[:3] or [
                '确认客户当前采购计划与时间窗口',
                '组织一次需求澄清会议并记录决策要点',
                '在会后发送下一步执行清单'
            ],
            'communication_script': '您好，结合当前沟通情况，我们建议先确认需求优先级和实施时间，再推进方案细节。',
            'recommended_follow_up_time': next_time,
            'risk_alert': risks[:3] or ['客户需求仍存在不确定性，请关注跟进节奏。'],
            'strategy_summary': '已根据客户洞察生成规则兜底跟进策略。'
        }

    @staticmethod
    def _normalize(data: dict[str, Any]) -> FollowupStrategyOutput:
        """标准化 LLM 输出。"""
        return FollowupStrategyOutput(
            priority=str(data.get('priority', '中')).strip() or '中',
            next_action=FollowupStrategyAgent._ensure_str_list(data.get('next_action')),
            communication_script=str(data.get('communication_script', '')).strip(),
            recommended_follow_up_time=str(data.get('recommended_follow_up_time', '')).strip(),
            risk_alert=FollowupStrategyAgent._ensure_str_list(data.get('risk_alert')),
            strategy_summary=str(data.get('strategy_summary', '')).strip()
        )

    @staticmethod
    def _ensure_str_list(value: Any) -> list[str]:
        """确保字段为字符串列表。"""
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

