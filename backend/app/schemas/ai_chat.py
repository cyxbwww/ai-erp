"""AI 对话 Schema 文件：定义多 Agent 编排请求与响应结构。"""

from typing import Any

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    """多 Agent 对话请求模型。"""

    # 业务场景：如 customer_detail / order_detail / knowledge_base。
    scene: str = Field(default='')
    # 用户输入原文。
    user_message: str = Field(default='')
    # 页面上下文：用于传递 customer_id / order_id / top_k 等参数。
    context: dict[str, Any] = Field(default_factory=dict)


class AIExecutionPlan(BaseModel):
    """统一执行计划模型：用于前端稳定渲染。"""

    # 任务类型：如 customer_followup_analysis。
    task_type: str
    # 执行 Agent 顺序列表。
    agents: list[str]
    # 是否需要知识库检索。
    need_rag: bool
    # 路由原因说明。
    reason: str


class AIChatResult(BaseModel):
    """多 Agent 编排结果数据结构。"""

    task_type: str
    summary: str
    plan: AIExecutionPlan
    agent_outputs: dict[str, Any]
    # 前端友好渲染块：用于直接绘制总结区和各 Agent 结果区。
    ui_blocks: list[dict[str, Any]] = Field(default_factory=list)
