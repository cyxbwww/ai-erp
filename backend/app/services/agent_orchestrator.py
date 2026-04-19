"""多 Agent 编排器：执行 Supervisor 计划并汇总最终结果。"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.agents.customer_insight_agent import CustomerInsightAgent
from app.agents.followup_strategy_agent import FollowupStrategyAgent
from app.agents.knowledge_rag_agent import KnowledgeRAGAgent
from app.agents.order_analysis_agent import OrderAnalysisAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.task_execution_agent import TaskExecutionAgent
from app.schemas.ai_chat import AIChatRequest, AIChatResult, AIExecutionPlan
from app.services.ai_trace_service import AITraceService


class AgentOrchestrator:
    """多 Agent 编排执行器。"""

    def __init__(self) -> None:
        # 可注册扩展：后续可继续追加 memory_agent / task_execution_agent。
        self._supervisor = SupervisorAgent()
        self._agent_map = {
            'customer_insight_agent': CustomerInsightAgent(),
            'followup_strategy_agent': FollowupStrategyAgent(),
            'task_execution_agent': TaskExecutionAgent(),
            'order_analysis_agent': OrderAnalysisAgent(),
            'knowledge_rag_agent': KnowledgeRAGAgent()
        }

    def execute(self, db: Session, request: AIChatRequest) -> AIChatResult:
        """执行编排流程：规划 -> 串联执行 -> 汇总。"""
        start_time = time.perf_counter()
        trace_record = None
        try:
            trace_record = AITraceService.start_record(db=db, request=request)
            # 将本次调用记录编号写入上下文，供 Agent 记忆落库关联来源。
            if trace_record is not None:
                request.context['source_record_id'] = trace_record.id
        except Exception:
            # 追踪写入失败不影响主流程。
            trace_record = None

        task_type = 'general_analysis'
        supervisor_summary = ''
        plan = AIExecutionPlan(task_type=task_type, agents=[], need_rag=False, reason='')
        agent_outputs: dict[str, Any] = {}
        previous_outputs: dict[str, Any] = {}
        agent_details: list[dict[str, Any]] = []
        final_summary = ''
        final_status = 'success'
        final_error_message = ''

        try:
            supervisor_output = self._supervisor.run(db=db, request=request, previous_outputs={})
            task_type = str(supervisor_output.get('task_type', 'general_analysis')).strip() or 'general_analysis'
            supervisor_summary = str(supervisor_output.get('summary', '')).strip()
            plan_data = supervisor_output.get('plan', {}) if isinstance(supervisor_output.get('plan', {}), dict) else {}

            # 统一计划结构读取。
            plan = AIExecutionPlan(
                task_type=str(plan_data.get('task_type', task_type)).strip() or task_type,
                agents=[str(name).strip() for name in plan_data.get('agents', []) if str(name).strip()],
                need_rag=bool(plan_data.get('need_rag', False)),
                reason=str(plan_data.get('reason', '')).strip()
            )

            for agent_name in plan.agents:
                input_preview = AITraceService.build_input_preview(
                    request=request,
                    previous_outputs=previous_outputs,
                    agent_name=agent_name
                )
                agent_start = time.perf_counter()

                agent = self._agent_map.get(agent_name)
                if not agent:
                    output = {'error': f'未找到 Agent: {agent_name}'}
                else:
                    try:
                        # 串联执行：后续 Agent 可以读取 previous_outputs。
                        output = agent.run(db=db, request=request, previous_outputs=previous_outputs)
                    except ValueError as exc:
                        output = {'error': str(exc)}
                    except Exception as exc:
                        output = {'error': f'Agent 执行异常: {exc}'}

                duration_ms = int((time.perf_counter() - agent_start) * 1000)
                used_fallback = AITraceService.detect_fallback(output if isinstance(output, dict) else {})

                previous_outputs[agent_name] = output
                agent_outputs[agent_name] = output
                agent_details.append(
                    {
                        'agent_name': agent_name,
                        'duration_ms': duration_ms,
                        'used_fallback': used_fallback,
                        'input_preview': input_preview,
                        'output_json': output
                    }
                )

            final_summary = self._build_final_summary(
                task_type=task_type,
                supervisor_summary=supervisor_summary,
                plan=plan,
                agent_outputs=agent_outputs
            )
            final_status = 'partial_failed' if AITraceService.has_error(agent_outputs) else 'success'

        except Exception as exc:
            # 编排级异常：保持接口异常抛出前先记追踪。
            final_status = 'failed'
            final_error_message = str(exc)
            final_summary = supervisor_summary or '编排执行失败'
            total_duration_ms = int((time.perf_counter() - start_time) * 1000)
            if trace_record is not None:
                try:
                    AITraceService.finish_record(
                        db=db,
                        record=trace_record,
                        task_type=task_type,
                        plan=plan,
                        agent_outputs=agent_outputs,
                        agent_details=agent_details,
                        final_summary=final_summary,
                        total_duration_ms=total_duration_ms,
                        status=final_status,
                        error_message=final_error_message
                    )
                except Exception:
                    pass
            raise

        total_duration_ms = int((time.perf_counter() - start_time) * 1000)
        if trace_record is not None:
            try:
                AITraceService.finish_record(
                    db=db,
                    record=trace_record,
                    task_type=task_type,
                    plan=plan,
                    agent_outputs=agent_outputs,
                    agent_details=agent_details,
                    final_summary=final_summary,
                    total_duration_ms=total_duration_ms,
                    status=final_status,
                    error_message=final_error_message
                )
            except Exception:
                pass

        return AIChatResult(
            task_type=task_type,
            summary=final_summary,
            plan=plan,
            agent_outputs=agent_outputs,
            ui_blocks=self._build_ui_blocks(
                task_type=task_type,
                summary=final_summary,
                plan=plan,
                agent_outputs=agent_outputs
            )
        )

    @staticmethod
    def _build_final_summary(
        task_type: str,
        supervisor_summary: str,
        plan: AIExecutionPlan,
        agent_outputs: dict[str, Any]
    ) -> str:
        """结合任务类型与多 Agent 输出，生成总摘要。"""
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
    def _build_ui_blocks(
        task_type: str,
        summary: str,
        plan: AIExecutionPlan,
        agent_outputs: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """构建前端可直接渲染的 UI blocks。"""
        blocks: list[dict[str, Any]] = [
            {
                'type': 'summary',
                'title': AgentOrchestrator._summary_title(task_type),
                'content': summary
            }
        ]

        for agent_name in plan.agents:
            blocks.append(
                {
                    'type': 'agent_result',
                    'agent_name': agent_name,
                    'title': AgentOrchestrator._agent_title(agent_name),
                    'data': agent_outputs.get(agent_name, {})
                }
            )
        return blocks

    @staticmethod
    def _summary_title(task_type: str) -> str:
        """根据任务类型返回总结标题。"""
        if task_type == 'customer_followup_analysis':
            return '客户综合结论'
        if task_type == 'order_analysis':
            return '订单风险结论'
        if task_type == 'knowledge_query':
            return '知识检索结论'
        return '综合结论'

    @staticmethod
    def _agent_title(agent_name: str) -> str:
        """Agent 名称到展示标题映射。"""
        title_map = {
            'customer_insight_agent': '客户洞察',
            'followup_strategy_agent': '跟进策略',
            'task_execution_agent': '任务建议',
            'order_analysis_agent': '订单分析',
            'knowledge_rag_agent': '知识支持'
        }
        return title_map.get(agent_name, agent_name)
