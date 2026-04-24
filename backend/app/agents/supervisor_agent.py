"""SupervisorAgent 文件：负责任务识别、路由规划与执行计划生成。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.prompts.agent_prompts import AgentPrompts
from app.schemas.ai_chat import AIChatRequest
from app.services.llm_service import LLMService


class SupervisorAgent(BaseAgent):
    """总控 Agent：规则优先，LLM 兜底。"""

    name = 'supervisor_agent'
    description = '识别业务场景、判断任务类型，并生成多 Agent 执行计划。'
    supported_scenes = ['customer_detail', 'order_detail', 'knowledge_base', 'general']
    dependencies: list[str] = []

    CUSTOMER_RAG_KEYWORDS = ('制度', '报价', '规则', '合同', '参数', '产品说明')
    ORDER_RAG_KEYWORDS = ('规则', '条款', '售后政策', '流程', '合同', '售后条款')
    FOLLOWUP_KEYWORDS = ('跟进', '建议', '话术', '下一步')
    TASK_EXECUTION_KEYWORDS = ('帮我安排下一步', '生成待办', '创建跟进任务', '转成任务', '安排销售动作')

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """生成任务类型与执行计划。"""
        _ = db
        _ = previous_outputs

        rule_plan = self._build_plan_by_rules(request)
        if rule_plan.get('plan', {}).get('agents'):
            return self.attach_execution_meta(
                rule_plan,
                status='success',
                confidence=0.9,
                next_recommendation='按规则计划执行后续专业 Agent。',
                message='规则路由命中。'
            )

        llm_plan = self._build_plan_by_llm(request)
        if llm_plan.get('plan', {}).get('agents'):
            return self.attach_execution_meta(
                llm_plan,
                status='success',
                confidence=0.75,
                next_recommendation='按模型兜底计划执行后续专业 Agent。',
                message='规则未命中，已使用模型兜底规划。'
            )

        fallback_plan = {
            'task_type': 'general_analysis',
            'summary': '未命中明确场景，默认执行客户洞察。',
            'plan': self._make_plan(
                task_type='general_analysis',
                agents=['customer_insight_agent'],
                reason='默认兜底计划'
            )
        }
        return self.attach_execution_meta(
            fallback_plan,
            status='partial_failed',
            confidence=0.55,
            next_recommendation='建议补充明确业务场景或客户上下文。',
            message='未命中明确场景，使用默认兜底计划。'
        )

    def _build_plan_by_rules(self, request: AIChatRequest) -> dict[str, Any]:
        """基于业务规则的路由规划。"""
        scene = (request.scene or '').strip().lower()
        message = (request.user_message or '').strip().lower()
        agents: list[str] = []
        task_type = 'general_analysis'
        reason_parts: list[str] = []

        if scene == 'knowledge_base':
            task_type = 'knowledge_query'
            agents = ['knowledge_rag_agent']
            reason_parts.append('knowledge_base 场景直接走知识检索')
        elif scene == 'customer_detail':
            task_type = 'customer_followup_analysis'
            agents.append('customer_insight_agent')
            reason_parts.append('customer_detail 场景默认做客户洞察')

            need_followup = self._contains_any(message, self.FOLLOWUP_KEYWORDS)
            need_rag = self._contains_any(message, self.CUSTOMER_RAG_KEYWORDS)
            need_task = self._contains_any(message, self.TASK_EXECUTION_KEYWORDS)

            if need_rag:
                agents.append('knowledge_rag_agent')
                reason_parts.append('问题涉及制度/报价/规则/合同/参数/产品说明，追加知识检索')

            if need_followup or need_task:
                agents.append('followup_strategy_agent')
                reason_parts.append('问题涉及跟进建议或任务安排，追加跟进策略 Agent')

            if need_task:
                agents.append('task_execution_agent')
                reason_parts.append('问题涉及待办/任务安排，追加任务执行 Agent')
        elif scene == 'order_detail':
            task_type = 'order_analysis'
            agents.append('order_analysis_agent')
            reason_parts.append('order_detail 场景默认做订单分析')

            if self._contains_any(message, self.ORDER_RAG_KEYWORDS):
                agents.append('knowledge_rag_agent')
                reason_parts.append('问题涉及规则/条款/流程/售后政策，追加知识检索')
        else:
            if self._contains_any(message, self.CUSTOMER_RAG_KEYWORDS + self.ORDER_RAG_KEYWORDS):
                task_type = 'knowledge_query'
                agents = ['knowledge_rag_agent']
                reason_parts.append('通用场景命中知识关键词，优先知识检索')

        agents = self._deduplicate_agents(agents)
        reason = '；'.join(reason_parts) if reason_parts else '规则未命中'
        return {
            'task_type': task_type,
            'summary': f'规则规划完成，计划执行 {len(agents)} 个 Agent。',
            'plan': self._make_plan(task_type=task_type, agents=agents, reason=reason)
        }

    def _build_plan_by_llm(self, request: AIChatRequest) -> dict[str, Any]:
        """模型兜底规划：仅在规则无法覆盖时启用。"""
        prompt = (
            f'{AgentPrompts.SUPERVISOR_ROUTE_PROMPT}\n'
            f'场景：{request.scene}\n'
            f'用户问题：{request.user_message}\n'
            f'上下文：{request.context}'
        )
        fallback = {'task_type': 'general_analysis', 'summary': '模型兜底失败', 'agent_names': []}
        data = LLMService.chat_json(
            system_prompt=AgentPrompts.AGENT_JSON_SYSTEM_PROMPT,
            user_prompt=prompt,
            fallback_data=fallback
        )

        valid_agents = {
            'customer_insight_agent',
            'followup_strategy_agent',
            'task_execution_agent',
            'order_analysis_agent',
            'knowledge_rag_agent'
        }
        agents: list[str] = []
        for name in data.get('agent_names', []):
            agent_name = str(name or '').strip()
            if agent_name in valid_agents:
                agents.append(agent_name)
        agents = self._deduplicate_agents(agents)

        task_type = str(data.get('task_type', 'general_analysis')).strip() or 'general_analysis'
        return {
            'task_type': task_type,
            'summary': str(data.get('summary', '模型兜底规划')),
            'plan': self._make_plan(task_type=task_type, agents=agents, reason='LLM 兜底路由结果')
        }

    @staticmethod
    def _make_plan(task_type: str, agents: list[str], reason: str) -> dict[str, Any]:
        """构建统一计划结构。"""
        return {
            'task_type': task_type,
            'agents': agents,
            'need_rag': 'knowledge_rag_agent' in agents,
            'reason': reason
        }

    @staticmethod
    def _deduplicate_agents(agents: list[str]) -> list[str]:
        """对 Agent 列表去重并保留顺序。"""
        result: list[str] = []
        seen: set[str] = set()
        for agent in agents:
            name = str(agent or '').strip()
            if not name or name in seen:
                continue
            seen.add(name)
            result.append(name)
        return result

    @staticmethod
    def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
        """关键词命中判断。"""
        return any(keyword in text for keyword in keywords)
