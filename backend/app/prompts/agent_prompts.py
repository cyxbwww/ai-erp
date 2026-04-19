"""Agent 提示词文件：集中管理 Supervisor 与业务 Agent 的提示词。"""

from __future__ import annotations

from typing import Any


class AgentPrompts:
    """多 Agent 提示词常量与模板。"""

    SUPERVISOR_ROUTE_PROMPT = (
        '你是 ERP 系统中的 supervisor_agent，请根据输入判断任务类型与执行 Agent 计划。\n'
        '你必须返回 JSON：\n'
        '{\n'
        '  "task_type": "customer_followup_analysis|order_analysis|knowledge_query|general_analysis",\n'
        '  "summary": "string",\n'
        '  "agent_names": ["customer_insight_agent", "followup_strategy_agent"]\n'
        '}\n'
        '可选 agent_names：customer_insight_agent、followup_strategy_agent、task_execution_agent、order_analysis_agent、knowledge_rag_agent。\n'
        '严格只输出 JSON，不要输出 markdown，不要输出额外解释。'
    )

    AGENT_JSON_SYSTEM_PROMPT = (
        '你是 AI 智能销售 ERP 系统的业务分析助手。\n'
        '你必须严格只输出 JSON，不要输出 markdown，不要输出额外解释，不要输出代码块。'
    )

    @staticmethod
    def build_customer_insight_prompt(
        context: dict[str, Any],
        user_message: str,
        memory_context: str = ''
    ) -> str:
        """构建客户洞察 Agent 提示词。"""
        return (
            '请基于以下 ERP 客户上下文进行分析，重点结合客户基本信息、跟进记录与订单历史。\n'
            '请输出稳定结构 JSON：\n'
            '{\n'
            '  "customer_stage": "线索阶段|意向阶段|商机推进|成交|流失风险",\n'
            '  "intent_level": "高|中|低",\n'
            '  "main_concerns": ["string"],\n'
            '  "risks": ["string"],\n'
            '  "suggestions": ["string"],\n'
            '  "analysis_summary": "string"\n'
            '}\n'
            '要求：\n'
            '1) main_concerns、risks、suggestions 至少各返回 2 条（若信息不足请说明不足点）。\n'
            '2) 结论必须贴合销售 ERP 场景，不要泛化成通用客服建议。\n'
            '3) 严格只输出 JSON，不要输出 markdown，不要输出额外解释。\n'
            f'用户问题：{user_message}\n'
            f'客户上下文：{context}\n'
            f'历史分析记忆：{memory_context or "无历史记忆"}'
        )

    @staticmethod
    def build_followup_strategy_prompt(
        user_message: str,
        customer_context: dict[str, Any],
        customer_insight: dict[str, Any],
        knowledge_support: dict[str, Any] | None = None,
        memory_context: str = ''
    ) -> str:
        """构建跟进策略 Agent 提示词。"""
        return (
            '你需要基于“客户洞察输出”制定下一步跟进策略。\n'
            '请输出稳定结构 JSON：\n'
            '{\n'
            '  "priority": "高|中|低",\n'
            '  "next_action": ["string"],\n'
            '  "communication_script": "string",\n'
            '  "recommended_follow_up_time": "YYYY-MM-DD HH:mm:ss 或 时间建议",\n'
            '  "risk_alert": ["string"],\n'
            '  "strategy_summary": "string"\n'
            '}\n'
            '要求：\n'
            '1) next_action 至少 3 条，必须可执行。\n'
            '2) communication_script 需为可直接对客户使用的话术。\n'
            '3) risk_alert 需与客户洞察中的风险保持一致并补充提醒。\n'
            '4) 严格只输出 JSON，不要输出 markdown，不要输出额外解释。\n'
            f'用户问题：{user_message}\n'
            f'客户基础上下文：{customer_context}\n'
            f'客户洞察输出：{customer_insight}\n'
            f'知识检索支持：{knowledge_support or {}}\n'
            f'历史策略记忆：{memory_context or "无历史记忆"}'
        )

    @staticmethod
    def build_order_analysis_prompt(
        order_detail: dict[str, Any],
        rule_scoring: dict[str, Any],
        user_message: str
    ) -> str:
        """构建订单分析 Agent 提示词。"""
        return (
            '请基于 ERP 订单详情和“规则评分结果”生成风险解释与处理建议。\n'
            '请输出稳定结构 JSON：\n'
            '{\n'
            '  "order_status": "string",\n'
            '  "recommendations": ["string"],\n'
            '  "analysis_summary": "string"\n'
            '}\n'
            '要求：\n'
            '1) 不要重新计算 risk_score 和 risk_level，不要修改规则评分结果。\n'
            '2) order_status 要用自然语言描述当前履约风险状态。\n'
            '3) recommendations 至少 2 条，必须可执行。\n'
            '4) 严格只输出 JSON，不要输出 markdown，不要输出额外解释。\n'
            f'用户问题：{user_message}\n'
            f'订单详情：{order_detail}\n'
            f'规则评分结果：{rule_scoring}'
        )

    @staticmethod
    def build_task_execution_prompt(
        user_message: str,
        customer_id: int,
        followup_strategy: dict[str, Any],
        customer_insight: dict[str, Any]
    ) -> str:
        """构建任务执行 Agent 提示词。"""
        return (
            '请将跟进策略转换为可执行销售任务，面向 ERP 待办管理场景。\n'
            '请严格输出 JSON：\n'
            '{\n'
            '  "task_type": "customer_followup_task",\n'
            '  "title": "string",\n'
            '  "description": "string",\n'
            '  "priority": "高|中|低",\n'
            '  "suggested_owner": "string",\n'
            '  "suggested_due_time": "YYYY-MM-DD HH:mm:ss 或 时间建议",\n'
            '  "reminder_text": "string",\n'
            '  "related_customer_id": 0\n'
            '}\n'
            '要求：\n'
            '1) title 必须可直接作为待办标题展示。\n'
            '2) description 必须包含下一步动作要点。\n'
            '3) reminder_text 要体现提醒语气，便于后续接消息系统。\n'
            '4) 严格只输出 JSON，不要输出 markdown，不要输出额外解释。\n'
            f'用户问题：{user_message}\n'
            f'客户编号：{customer_id}\n'
            f'客户洞察：{customer_insight}\n'
            f'跟进策略：{followup_strategy}'
        )
