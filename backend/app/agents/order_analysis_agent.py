"""订单分析 Agent：采用“规则评分 + LLM解释”两阶段分析。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.prompts.agent_prompts import AgentPrompts
from app.schemas.agent import OrderAnalysisOutput
from app.schemas.ai_chat import AIChatRequest
from app.services.llm_service import LLMService
from app.services.order_risk_scoring_service import OrderRiskScoringService
from app.tools.agent_query_tools import AgentQueryTools


class OrderAnalysisAgent(BaseAgent):
    """order_analysis_agent 实现。"""

    name = 'order_analysis_agent'
    description = '基于订单详情执行规则评分，并用 LLM 补充风险解释和处理建议。'
    supported_scenes = ['order_detail']
    dependencies: list[str] = []

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """执行订单分析：规则评分优先，LLM 负责解释。"""
        _ = previous_outputs
        order_id = int(request.context.get('order_id') or 0)
        if order_id <= 0:
            output = OrderAnalysisOutput(
                risk_score=0,
                risk_level='low',
                risk_factors=[{'name': '缺少订单编号', 'score': 0}],
                order_status='缺少 order_id，无法完成订单风险分析',
                recommendations=['请在 context 中传入 order_id 后重试'],
                need_manual_intervention=False,
                analysis_summary='缺少订单编号，返回兜底结果。'
            ).model_dump()
            return self.attach_execution_meta(
                output,
                status='partial_failed',
                confidence=0.25,
                next_recommendation='请补充 order_id 后重新执行订单分析。',
                message='缺少订单编号，已返回兜底订单分析。'
            )

        order_detail = AgentQueryTools.get_order_analysis_context(db=db, order_id=order_id)

        # 阶段1：规则评分（确定性计算）。
        scoring = OrderRiskScoringService.score(order_detail=order_detail)

        # 阶段2：LLM 解释（不参与评分，仅补充解释与建议）。
        prompt = AgentPrompts.build_order_analysis_prompt(
            order_detail=order_detail,
            rule_scoring=scoring,
            user_message=request.user_message
        )
        llm_fallback = {
            'order_status': self._default_order_status(scoring['risk_level']),
            'recommendations': self._default_recommendations(scoring['risk_level']),
            'analysis_summary': self._default_analysis_summary(scoring['risk_level'], scoring['risk_score'])
        }
        llm_data = LLMService.chat_json(
            system_prompt=AgentPrompts.AGENT_JSON_SYSTEM_PROMPT,
            user_prompt=prompt,
            fallback_data=llm_fallback
        )

        normalized = self._normalize(scoring=scoring, llm_data=llm_data)
        output = normalized.model_dump()
        next_recommendation = '按标准订单流程继续推进。'
        if output.get('risk_level') == 'high' or bool(output.get('need_manual_intervention')):
            next_recommendation = '建议人工复核订单风险，并结合知识库规则校验处理口径。'
        return self.attach_execution_meta(
            output,
            status='success',
            confidence=0.86,
            next_recommendation=next_recommendation,
            message='订单风险分析完成。'
        )

    @staticmethod
    def _normalize(scoring: dict[str, Any], llm_data: dict[str, Any]) -> OrderAnalysisOutput:
        """整合规则评分与 LLM 解释输出。"""
        risk_level = str(scoring.get('risk_level', 'low')).strip().lower()
        if risk_level not in {'low', 'medium', 'high'}:
            risk_level = 'low'

        risk_score = int(scoring.get('risk_score') or 0)
        factors = scoring.get('risk_factors', [])
        if not isinstance(factors, list):
            factors = []
        normalized_factors: list[dict[str, int | str]] = []
        for item in factors:
            if not isinstance(item, dict):
                continue
            name = str(item.get('name', '')).strip()
            score = int(item.get('score') or 0)
            if not name:
                continue
            normalized_factors.append({'name': name, 'score': score})

        recommendations = OrderAnalysisAgent._ensure_str_list(llm_data.get('recommendations'))
        if not recommendations:
            recommendations = OrderAnalysisAgent._default_recommendations(risk_level)

        order_status = str(llm_data.get('order_status', '')).strip() or OrderAnalysisAgent._default_order_status(risk_level)
        analysis_summary = str(llm_data.get('analysis_summary', '')).strip() or OrderAnalysisAgent._default_analysis_summary(risk_level, risk_score)
        need_manual = bool(scoring.get('need_manual_intervention', False))

        return OrderAnalysisOutput(
            risk_score=max(risk_score, 0),
            risk_level=risk_level,
            risk_factors=normalized_factors,
            order_status=order_status,
            recommendations=recommendations,
            need_manual_intervention=need_manual,
            analysis_summary=analysis_summary
        )

    @staticmethod
    def _default_order_status(risk_level: str) -> str:
        """默认订单状态描述。"""
        if risk_level == 'high':
            return '当前订单存在较高履约风险'
        if risk_level == 'medium':
            return '当前订单存在中等风险，建议重点跟进'
        return '当前订单风险较低，可按标准流程推进'

    @staticmethod
    def _default_recommendations(risk_level: str) -> list[str]:
        """默认建议列表。"""
        if risk_level == 'high':
            return ['立即核对付款与发货节点，明确责任人', '组织销售、交付、客服联合评审并每日跟踪']
        if risk_level == 'medium':
            return ['本周内完成订单状态复核并更新客户沟通记录', '提前确认交付资源与客户验收计划']
        return ['按既定流程持续推进订单履约', '保持与客户的常规进度同步']

    @staticmethod
    def _default_analysis_summary(risk_level: str, risk_score: int) -> str:
        """默认一句话总结。"""
        return f'规则评分结果为 {risk_score} 分，风险等级 {risk_level}。'

    @staticmethod
    def _ensure_str_list(value: Any) -> list[str]:
        """确保字段为字符串列表。"""
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
