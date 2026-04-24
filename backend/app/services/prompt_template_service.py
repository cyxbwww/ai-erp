"""Prompt 模板服务文件：使用内存字典集中管理 AI 提示词模板。"""

from string import Formatter
from typing import Any


class PromptTemplateService:
    """Prompt 模板服务：提供模板列表、详情读取和简单变量渲染能力。"""

    # 内存模板注册表：当前为最小版本，不依赖数据库，后续可平滑迁移到配置表。
    _templates: dict[str, dict[str, Any]] = {
        'customer_follow_advice': {
            'template_key': 'customer_follow_advice',
            'module': 'customer',
            'task_type': 'follow_advice',
            'name': '客户跟进建议',
            'description': '基于客户洞察、历史跟进和知识支持生成下一步跟进策略。',
            'version': 'v1',
            'system_prompt': (
                '你是 AI 智能销售 ERP 系统的客户跟进策略助手。'
                '你必须严格只输出 JSON，不要输出 markdown，不要输出额外解释。'
            ),
            'user_prompt_template': (
                '请基于客户上下文制定下一步跟进策略。\n'
                '用户问题：{user_message}\n'
                '客户上下文：{customer_context}\n'
                '客户洞察输出：{customer_insight}\n'
                '知识检索支持：{knowledge_support}\n'
                '历史策略记忆：{memory_context}\n'
                '请输出 priority、next_action、communication_script、recommended_follow_up_time、risk_alert、strategy_summary。'
            )
        },
        'customer_follow_summary': {
            'template_key': 'customer_follow_summary',
            'module': 'customer',
            'task_type': 'follow_summary',
            'name': '客户跟进总结',
            'description': '基于客户资料、跟进记录和订单历史生成客户意向与风险总结。',
            'version': 'v1',
            'system_prompt': (
                '你是 AI 智能销售 ERP 系统的客户洞察助手。'
                '你必须严格只输出 JSON，不要输出 markdown，不要输出额外解释。'
            ),
            'user_prompt_template': (
                '请基于以下 ERP 客户上下文进行客户跟进总结。\n'
                '用户问题：{user_message}\n'
                '客户上下文：{customer_context}\n'
                '历史分析记忆：{memory_context}\n'
                '请输出 customer_stage、intent_level、main_concerns、risks、suggestions、analysis_summary。'
            )
        },
        'order_analysis': {
            'template_key': 'order_analysis',
            'module': 'order',
            'task_type': 'order_analysis',
            'name': '订单分析',
            'description': '基于订单详情和规则评分结果生成风险解释与处理建议。',
            'version': 'v1',
            'system_prompt': (
                '你是 AI 智能销售 ERP 系统的订单分析助手。'
                '你必须严格只输出 JSON，不要输出 markdown，不要输出额外解释。'
            ),
            'user_prompt_template': (
                '请基于 ERP 订单详情和规则评分结果生成风险解释与处理建议。\n'
                '用户问题：{user_message}\n'
                '订单详情：{order_detail}\n'
                '规则评分结果：{rule_scoring}\n'
                '请输出 order_status、recommendations、analysis_summary，不要重新计算 risk_score 和 risk_level。'
            )
        },
        'knowledge_base_rag_answer': {
            'template_key': 'knowledge_base_rag_answer',
            'module': 'knowledge_base',
            'task_type': 'rag_answer',
            'name': '知识库问答',
            'description': '基于检索命中的知识片段生成结构化问答结果。',
            'version': 'v1',
            'system_prompt': (
                '你是企业 ERP 系统中的知识库助手。'
                '你必须仅依据给定知识片段回答，并严格只输出 JSON。'
            ),
            'user_prompt_template': (
                '请仅依据给定知识片段回答问题。\n'
                '若证据不足，请明确说明“当前知识库证据不足”。\n'
                '问题：{question}\n'
                '知识片段：\n{knowledge_chunks}\n'
                '请输出 answer 和 basis，basis 为依据摘要，不能粘贴大段原文。'
            )
        },
        'supervisor_plan': {
            'template_key': 'supervisor_plan',
            'module': 'ai',
            'task_type': 'supervisor_plan',
            'name': 'Supervisor 编排规划',
            'description': '根据场景、用户问题和上下文判断任务类型与执行 Agent 计划。',
            'version': 'v1',
            'system_prompt': (
                '你是 ERP 系统中的 supervisor_agent。'
                '你必须严格只输出 JSON，不要输出 markdown，不要输出额外解释。'
            ),
            'user_prompt_template': (
                '请根据输入判断任务类型与执行 Agent 计划。\n'
                '场景：{scene}\n'
                '用户问题：{user_message}\n'
                '上下文：{context}\n'
                '可选 agent_names：customer_insight_agent、followup_strategy_agent、task_execution_agent、'
                'order_analysis_agent、knowledge_rag_agent。\n'
                '请输出 task_type、summary、agent_names。'
            )
        }
    }

    @staticmethod
    def list_templates() -> list[dict[str, Any]]:
        """获取模板列表：列表场景不返回完整模板正文，避免响应过长。"""
        return [
            {
                'template_key': item['template_key'],
                'module': item['module'],
                'task_type': item['task_type'],
                'name': item['name'],
                'description': item['description'],
                'version': item['version']
            }
            for item in PromptTemplateService._templates.values()
        ]

    @staticmethod
    def get_template(template_key: str) -> dict[str, Any] | None:
        """按模板 key 获取完整模板，未找到返回 None。"""
        template = PromptTemplateService._templates.get(template_key)
        if not template:
            return None
        return dict(template)

    @staticmethod
    def get_template_version(template_key: str) -> str | None:
        """获取模板版本号：调用日志写入时用于记录本次使用的 Prompt 版本。"""
        template = PromptTemplateService.get_template(template_key)
        if not template:
            return None
        return str(template.get('version') or '') or None

    @staticmethod
    def render_template(template_key: str, variables: dict[str, Any]) -> str:
        """渲染用户 Prompt 模板：支持 {变量名} 的简单替换。"""
        template = PromptTemplateService.get_template(template_key)
        if not template:
            raise ValueError(f'Prompt 模板不存在：{template_key}')

        user_prompt_template = str(template.get('user_prompt_template') or '')
        required_variables = PromptTemplateService._extract_variables(user_prompt_template)
        missing_variables = [name for name in required_variables if name not in variables]
        if missing_variables:
            # 明确指出缺失变量，便于后续接入 Agent 时快速定位模板参数问题。
            raise ValueError(f'Prompt 模板变量缺失：{", ".join(missing_variables)}')

        safe_variables = {key: PromptTemplateService._stringify_value(value) for key, value in variables.items()}
        try:
            return user_prompt_template.format(**safe_variables)
        except Exception as exc:
            raise ValueError(f'Prompt 模板渲染失败：{exc}') from exc

    @staticmethod
    def _extract_variables(template_text: str) -> list[str]:
        """提取模板中的变量名，忽略纯文本片段。"""
        formatter = Formatter()
        variables: list[str] = []
        for _literal, field_name, _format_spec, _conversion in formatter.parse(template_text):
            if field_name and field_name not in variables:
                variables.append(field_name)
        return variables

    @staticmethod
    def _stringify_value(value: Any) -> str:
        """将变量值转成字符串，保证字典、列表等上下文也能安全写入 Prompt。"""
        if value is None:
            return ''
        return str(value)
