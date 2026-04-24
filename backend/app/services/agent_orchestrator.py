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
from app.services.agent_summary_builder import AgentSummaryBuilder
from app.services.ai_trace_service import AITraceService


class AgentOrchestrator:
    """多 Agent 编排执行器。"""

    # 任务意图关键词：仅用于第二阶段从跟进策略动态追加任务建议 Agent。
    TASK_INTENT_KEYWORDS = ('生成待办', '创建任务', '安排下一步', '转成任务', '安排销售动作')

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

            # 统一计划结构读取；新增字段提供默认值，保持旧计划数据兼容。
            plan = AIExecutionPlan(
                task_type=str(plan_data.get('task_type', task_type)).strip() or task_type,
                agents=[str(name).strip() for name in plan_data.get('agents', []) if str(name).strip()],
                need_rag=bool(plan_data.get('need_rag', False)),
                reason=str(plan_data.get('reason', '')).strip(),
                actual_agents=[
                    str(name).strip()
                    for name in plan_data.get('actual_agents', [])
                    if str(name).strip()
                ],
                skipped_agents=[
                    str(name).strip()
                    for name in plan_data.get('skipped_agents', [])
                    if str(name).strip()
                ],
                dynamic_reason=str(plan_data.get('dynamic_reason', '')).strip()
            )

            actual_agents: list[str] = []
            skipped_agents: list[str] = []
            dynamic_reasons: list[str] = []
            executed_agents: set[str] = set()
            execution_queue = list(plan.agents)
            queued_or_executed_agents = set(execution_queue)
            max_steps = len(self._agent_map) + 2
            step_count = 0

            while execution_queue:
                if step_count >= max_steps:
                    # 最大步数保护用于防止错误计划或后续扩展造成无限追加。
                    dynamic_reasons.append(f'执行步数达到上限 {max_steps}，已停止继续追加 Agent。')
                    break
                step_count += 1
                agent_name = execution_queue.pop(0)
                agent = self._agent_map.get(agent_name)
                skip_message = self._get_skip_message(
                    agent_name=agent_name,
                    previous_outputs=previous_outputs,
                    executed_agents=executed_agents
                )

                input_preview = AITraceService.build_input_preview(
                    request=request,
                    previous_outputs=previous_outputs,
                    agent_name=agent_name
                )
                agent_start = time.perf_counter()

                if skip_message:
                    # 跳过逻辑保持可解释，避免在缺少关键上游时生成误导性结果。
                    output = agent.build_skipped_output(skip_message) if agent else self._build_missing_agent_output(agent_name)
                    skipped_agents.append(agent_name)
                    dynamic_reasons.append(skip_message)
                elif not agent:
                    output = self._build_missing_agent_output(agent_name)
                else:
                    try:
                        # 串联执行：后续 Agent 可以读取 previous_outputs。
                        output = agent.run(db=db, request=request, previous_outputs=previous_outputs)
                    except ValueError as exc:
                        output = self._build_failed_output(agent_name=agent_name, message=str(exc))
                    except Exception as exc:
                        output = self._build_failed_output(agent_name=agent_name, message=f'Agent 执行异常: {exc}')

                duration_ms = int((time.perf_counter() - agent_start) * 1000)
                used_fallback = AITraceService.detect_fallback(output if isinstance(output, dict) else {})

                actual_agents.append(agent_name)
                executed_agents.add(agent_name)
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

                self._append_dynamic_agents(
                    current_agent_name=agent_name,
                    output=output,
                    request=request,
                    execution_queue=execution_queue,
                    queued_or_executed_agents=queued_or_executed_agents,
                    dynamic_reasons=dynamic_reasons
                )

            # 将轻量调度结果写回 plan，方便 Trace 和前端查看真实执行轨迹。
            plan.actual_agents = actual_agents
            plan.skipped_agents = skipped_agents
            plan.dynamic_reason = '；'.join(dynamic_reasons)
            plan.need_rag = 'knowledge_rag_agent' in actual_agents

            final_summary = AgentSummaryBuilder.build_summary(
                task_type=task_type,
                supervisor_summary=supervisor_summary,
                plan=plan,
                agent_outputs=agent_outputs
            )
            final_status = self._resolve_final_status(agent_outputs)

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
            ui_blocks=AgentSummaryBuilder.build_ui_blocks(
                task_type=task_type,
                summary=final_summary,
                plan=plan,
                agent_outputs=agent_outputs
            )
        )

    @staticmethod
    def _get_skip_message(
        agent_name: str,
        previous_outputs: dict[str, Any],
        executed_agents: set[str]
    ) -> str:
        """根据当前上下文判断是否跳过 Agent，本阶段只保留最小规则。"""
        if agent_name == 'knowledge_rag_agent' and agent_name in executed_agents:
            return 'knowledge_rag_agent 已执行过，本次跳过重复知识检索。'

        if agent_name == 'task_execution_agent':
            followup_output = previous_outputs.get('followup_strategy_agent', {})
            if not isinstance(followup_output, dict) or not followup_output:
                return '缺少 followup_strategy_agent 输出，跳过任务建议生成，避免生成无依据任务。'
            meta = followup_output.get('execution_meta', {})
            if isinstance(meta, dict) and meta.get('status') in {'failed', 'skipped'}:
                return '跟进策略未有效生成，跳过任务建议生成。'

        return ''

    def _append_dynamic_agents(
        self,
        current_agent_name: str,
        output: dict[str, Any],
        request: AIChatRequest,
        execution_queue: list[str],
        queued_or_executed_agents: set[str],
        dynamic_reasons: list[str]
    ) -> None:
        """根据当前 Agent 输出追加少量可解释 Agent，本阶段只允许两条规则。"""
        if not isinstance(output, dict):
            return

        if current_agent_name == 'order_analysis_agent':
            risk_level = str(output.get('risk_level', '')).strip().lower()
            need_manual = bool(output.get('need_manual_intervention', False))
            if (risk_level == 'high' or need_manual) and 'knowledge_rag_agent' not in queued_or_executed_agents:
                self._append_agent_once(
                    agent_name='knowledge_rag_agent',
                    execution_queue=execution_queue,
                    queued_or_executed_agents=queued_or_executed_agents,
                    dynamic_reasons=dynamic_reasons,
                    reason='订单分析识别到高风险，追加知识检索用于规则校验'
                )
            return

        if current_agent_name == 'followup_strategy_agent':
            message = request.user_message or ''
            has_task_intent = any(keyword in message for keyword in self.TASK_INTENT_KEYWORDS)
            if has_task_intent and 'task_execution_agent' not in queued_or_executed_agents:
                self._append_agent_once(
                    agent_name='task_execution_agent',
                    execution_queue=execution_queue,
                    queued_or_executed_agents=queued_or_executed_agents,
                    dynamic_reasons=dynamic_reasons,
                    reason='用户表达任务创建意图，追加任务建议 Agent'
                )

    @staticmethod
    def _append_agent_once(
        agent_name: str,
        execution_queue: list[str],
        queued_or_executed_agents: set[str],
        dynamic_reasons: list[str],
        reason: str
    ) -> None:
        """将 Agent 追加到执行队列，并通过集合保证不会重复追加。"""
        if agent_name in queued_or_executed_agents:
            return
        execution_queue.append(agent_name)
        queued_or_executed_agents.add(agent_name)
        dynamic_reasons.append(reason)

    @staticmethod
    def _build_missing_agent_output(agent_name: str) -> dict[str, Any]:
        """构建未找到 Agent 的标准失败输出。"""
        return {
            'error': f'未找到 Agent: {agent_name}',
            'execution_meta': {
                'status': 'failed',
                'confidence': 0.0,
                'next_recommendation': '请检查 Supervisor 计划中的 Agent 名称。',
                'message': f'未找到 Agent: {agent_name}'
            },
            'agent_meta': {
                'name': agent_name,
                'description': '未注册的 Agent',
                'supported_scenes': [],
                'dependencies': []
            }
        }

    @staticmethod
    def _build_failed_output(agent_name: str, message: str) -> dict[str, Any]:
        """构建 Agent 执行异常的标准失败输出。"""
        return {
            'error': message,
            'execution_meta': {
                'status': 'failed',
                'confidence': 0.0,
                'next_recommendation': '请检查该 Agent 的输入上下文或业务逻辑。',
                'message': message
            },
            'agent_meta': {
                'name': agent_name,
                'description': '执行失败的 Agent',
                'supported_scenes': [],
                'dependencies': []
            }
        }

    @staticmethod
    def _resolve_final_status(agent_outputs: dict[str, Any]) -> str:
        """根据各 Agent 执行元数据计算编排整体状态。"""
        if not agent_outputs:
            return 'success'

        statuses: list[str] = []
        for output in agent_outputs.values():
            if not isinstance(output, dict):
                continue
            meta = output.get('execution_meta', {})
            if isinstance(meta, dict):
                statuses.append(str(meta.get('status', '')).strip())
            elif output.get('error'):
                statuses.append('failed')

        if statuses and all(status == 'failed' for status in statuses):
            return 'failed'
        if any(status in {'failed', 'partial_failed', 'skipped'} for status in statuses):
            return 'partial_failed'
        if AITraceService.has_error(agent_outputs):
            return 'partial_failed'
        return 'success'
