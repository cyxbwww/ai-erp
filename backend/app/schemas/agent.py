"""Agent 输出 Schema 文件：定义各 Agent 结构化输出模型。"""

from pydantic import BaseModel, Field


class CustomerInsightOutput(BaseModel):
    """客户洞察 Agent 输出模型。"""

    customer_stage: str = Field(default='线索阶段')
    intent_level: str = Field(default='中')
    main_concerns: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    analysis_summary: str = Field(default='')


class FollowupStrategyOutput(BaseModel):
    """跟进策略 Agent 输出模型。"""

    priority: str = Field(default='中')
    next_action: list[str] = Field(default_factory=list)
    communication_script: str = Field(default='')
    recommended_follow_up_time: str = Field(default='')
    risk_alert: list[str] = Field(default_factory=list)
    strategy_summary: str = Field(default='')


class OrderAnalysisOutput(BaseModel):
    """订单分析 Agent 输出模型。"""

    risk_score: int = Field(default=0)
    order_status: str = Field(default='')
    risk_level: str = Field(default='low')
    risk_factors: list[dict[str, int | str]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    need_manual_intervention: bool = Field(default=False)
    analysis_summary: str = Field(default='')


class KnowledgeRAGHit(BaseModel):
    """知识命中片段模型。"""

    title: str = Field(default='')
    content: str = Field(default='')
    score: float = Field(default=0.0)


class KnowledgeRAGOutput(BaseModel):
    """知识检索 Agent 输出模型。"""

    query: str = Field(default='')
    hits: list[KnowledgeRAGHit] = Field(default_factory=list)
    summary: str = Field(default='')
    references: list[str] = Field(default_factory=list)


class TaskExecutionOutput(BaseModel):
    """任务执行 Agent 输出模型。"""

    task_type: str = Field(default='customer_followup_task')
    title: str = Field(default='')
    description: str = Field(default='')
    priority: str = Field(default='中')
    suggested_owner: str = Field(default='销售负责人')
    suggested_due_time: str = Field(default='')
    reminder_text: str = Field(default='')
    related_customer_id: int = Field(default=0)
