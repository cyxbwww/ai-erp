"""客户洞察 Agent：负责客户资料、跟进记录、订单历史的综合分析。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.prompts.agent_prompts import AgentPrompts
from app.schemas.agent import CustomerInsightOutput
from app.schemas.ai_chat import AIChatRequest
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.tools.agent_query_tools import AgentQueryTools


class CustomerInsightAgent(BaseAgent):
    """customer_insight_agent 实现：支持短期记忆增强。"""

    name = 'customer_insight_agent'
    description = '基于客户档案、跟进记录、订单历史和短期记忆生成客户洞察。'
    supported_scenes = ['customer_detail']
    dependencies: list[str] = []

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """执行客户洞察分析并返回结构化 JSON。"""
        _ = previous_outputs
        customer_id = int(request.context.get('customer_id') or 0)
        if customer_id <= 0:
            output = CustomerInsightOutput(
                customer_stage='线索阶段',
                intent_level='低',
                main_concerns=['缺少 customer_id，无法定位客户档案。'],
                risks=['上下文信息不足，分析结果可信度低。'],
                suggestions=['请在 context 传入 customer_id 后重试。'],
                analysis_summary='缺少客户编号，返回兜底结果。'
            ).model_dump()
            return self.attach_execution_meta(
                output,
                status='partial_failed',
                confidence=0.25,
                next_recommendation='请补充 customer_id 后重新执行客户洞察。',
                message='缺少客户编号，已返回兜底客户洞察。'
            )

        context = AgentQueryTools.get_customer_insight_context(db=db, customer_id=customer_id, follow_limit=8)

        # 读取最近客户分析记忆，增强“状态变化”理解能力。
        memories = MemoryService.list_recent_memories(
            db=db,
            customer_id=customer_id,
            scene='customer_detail',
            memory_types=['customer_analysis', 'followup_strategy'],
            limit=5
        )
        memory_context = MemoryService.format_memories_for_prompt(memories)

        prompt = AgentPrompts.build_customer_insight_prompt(
            context=context,
            user_message=request.user_message,
            memory_context=memory_context
        )
        fallback = self._build_fallback(context=context)

        llm_data = LLMService.chat_json(
            system_prompt=AgentPrompts.AGENT_JSON_SYSTEM_PROMPT,
            user_prompt=prompt,
            fallback_data=fallback,
            # 客户洞察用于沉淀客户跟进总结，日志按客户模块归类。
            module='customer',
            task_type='follow_summary'
        )
        normalized = self._normalize(llm_data)
        output = normalized.model_dump()

        # 分析完成后写入短期记忆，失败不影响主流程。
        try:
            source_record_id = int(request.context.get('source_record_id') or 0) or None
            MemoryService.save_memory(
                db=db,
                customer_id=customer_id,
                scene='customer_detail',
                memory_type='customer_analysis',
                summary=output.get('analysis_summary', ''),
                key_points={
                    'customer_stage': output.get('customer_stage', ''),
                    'intent_level': output.get('intent_level', ''),
                    'main_concerns': output.get('main_concerns', []),
                    'risks': output.get('risks', []),
                    'suggestions': output.get('suggestions', [])
                },
                source_record_id=source_record_id
            )
        except Exception:
            pass

        return self.attach_execution_meta(
            output,
            status='success',
            confidence=0.85,
            next_recommendation='可继续生成跟进策略或结合知识库校验业务规则。',
            message='客户洞察分析完成。'
        )

    @staticmethod
    def _build_fallback(context: dict[str, Any]) -> dict[str, Any]:
        """构建客户洞察兜底结果。"""
        customer = context.get('customer', {})
        follow_records = context.get('follow_records', [])
        order_summary = context.get('order_summary', {})
        stage = '线索阶段'
        if int(order_summary.get('order_count') or 0) > 0:
            stage = '商机推进'
        if str(customer.get('status') or '') == 'lost':
            stage = '流失风险'

        concerns = ['当前需求优先级待确认', '预算与决策链路信息不完整']
        if follow_records:
            concerns = ['客户历史沟通信息已存在，需提炼真实采购意图', '需确认下一次沟通目标与决策节点']

        risks = ['跟进节奏不稳定可能导致商机降温', '关键决策人信息缺失']
        suggestions = ['尽快确认预算窗口与决策人', '安排一次聚焦业务痛点的方案沟通']
        return {
            'customer_stage': stage,
            'intent_level': '中',
            'main_concerns': concerns,
            'risks': risks,
            'suggestions': suggestions,
            'analysis_summary': '已基于客户档案、跟进与订单信息生成规则兜底洞察。'
        }

    @staticmethod
    def _normalize(data: dict[str, Any]) -> CustomerInsightOutput:
        """标准化 LLM 输出。"""
        return CustomerInsightOutput(
            customer_stage=str(data.get('customer_stage', '线索阶段')).strip() or '线索阶段',
            intent_level=str(data.get('intent_level', '中')).strip() or '中',
            main_concerns=CustomerInsightAgent._ensure_str_list(data.get('main_concerns')),
            risks=CustomerInsightAgent._ensure_str_list(data.get('risks')),
            suggestions=CustomerInsightAgent._ensure_str_list(data.get('suggestions')),
            analysis_summary=str(data.get('analysis_summary', '')).strip()
        )

    @staticmethod
    def _ensure_str_list(value: Any) -> list[str]:
        """确保字段为字符串数组。"""
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
