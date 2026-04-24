"""Agent 总结构建服务：集中生成多 Agent 最终摘要与前端渲染块。"""

from __future__ import annotations

from typing import Any

from app.schemas.ai_chat import AIExecutionPlan


class AgentSummaryBuilder:
    """多 Agent 响应构建器：避免编排器继续堆积展示层汇总逻辑。"""

    @staticmethod
    def build_summary(
        task_type: str,
        supervisor_summary: str,
        plan: AIExecutionPlan,
        agent_outputs: dict[str, Any]
    ) -> str:
        """结合任务类型与多 Agent 输出，生成兼容旧前端的总摘要。"""
        customer_out = agent_outputs.get('customer_insight_agent', {})
        follow_out = agent_outputs.get('followup_strategy_agent', {})
        task_out = agent_outputs.get('task_execution_agent', {})
        order_out = agent_outputs.get('order_analysis_agent', {})
        knowledge_out = agent_outputs.get('knowledge_rag_agent', {})

        if task_type == 'customer_followup_analysis':
            stage = str(customer_out.get('customer_stage', '')).strip() or '未知'
            intent = str(customer_out.get('intent_level', '')).strip() or '未知'
            priority = str(follow_out.get('priority', '')).strip()
            task_title = str(task_out.get('title', '')).strip()
            refs = knowledge_out.get('references', []) if isinstance(knowledge_out, dict) else []
            parts = [f'客户阶段 {stage}，意向等级 {intent}。']
            if priority:
                parts.append(f'建议跟进优先级 {priority}。')
            if task_title:
                parts.append(f'已生成待办任务：{task_title}。')
            if refs:
                parts.append(f'已引用 {len(refs)} 份知识来源。')
            return ''.join(parts)

        if task_type == 'order_analysis':
            risk_level = str(order_out.get('risk_level', '')).strip() or 'low'
            need_manual = bool(order_out.get('need_manual_intervention', False))
            manual_text = '需要人工介入' if need_manual else '可按标准流程推进'
            if plan.need_rag:
                return f'订单风险等级 {risk_level}，{manual_text}，并已结合知识规则校验。'
            return f'订单风险等级 {risk_level}，{manual_text}。'

        if task_type == 'knowledge_query':
            hits = knowledge_out.get('hits', []) if isinstance(knowledge_out, dict) else []
            refs = knowledge_out.get('references', []) if isinstance(knowledge_out, dict) else []
            return f'知识检索完成，命中 {len(hits)} 个片段，覆盖 {len(refs)} 个引用来源。'

        return supervisor_summary or '已完成多 Agent 分析。'

    @staticmethod
    def build_ui_blocks(
        task_type: str,
        summary: str,
        plan: AIExecutionPlan,
        agent_outputs: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """构建前端可直接渲染的 UI blocks，并兼容原有字段结构。"""
        blocks: list[dict[str, Any]] = [
            {
                'type': 'summary',
                'title': AgentSummaryBuilder.summary_title(task_type),
                'content': summary
            }
        ]

        # 优先展示实际执行顺序；若没有实际执行记录，则回退到 supervisor 原始计划。
        display_agents = plan.actual_agents or plan.agents
        for agent_name in display_agents:
            output = agent_outputs.get(agent_name, {})
            block = {
                'type': 'agent_result',
                'agent_name': agent_name,
                'title': AgentSummaryBuilder.agent_title(agent_name),
                'data': output
            }
            if isinstance(output, dict) and isinstance(output.get('execution_meta'), dict):
                # 新增执行元数据只作为增强字段，旧前端忽略该字段也不影响渲染。
                block['execution_meta'] = output.get('execution_meta')
            blocks.append(block)
        return blocks

    @staticmethod
    def summary_title(task_type: str) -> str:
        """根据任务类型返回总结标题。"""
        if task_type == 'customer_followup_analysis':
            return '客户综合结论'
        if task_type == 'order_analysis':
            return '订单风险结论'
        if task_type == 'knowledge_query':
            return '知识检索结论'
        return '综合结论'

    @staticmethod
    def agent_title(agent_name: str) -> str:
        """Agent 名称到展示标题映射。"""
        title_map = {
            'supervisor_agent': '任务规划',
            'customer_insight_agent': '客户洞察',
            'followup_strategy_agent': '跟进策略',
            'task_execution_agent': '任务建议',
            'order_analysis_agent': '订单分析',
            'knowledge_rag_agent': '知识支持'
        }
        return title_map.get(agent_name, agent_name)
