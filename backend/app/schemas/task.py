"""任务 Schema 文件：定义 AI 草稿确认创建任务的请求与返回结构。"""

from pydantic import BaseModel, Field


class TaskFromAIDraftCreate(BaseModel):
    """AI 任务草稿确认创建请求模型。"""

    # 任务类型来自 task_payload，当前阶段仅用于兼容和后续扩展。
    task_type: str = Field(default='customer_followup_task', max_length=60)
    # 任务标题，用户确认前端展示的核心字段。
    title: str = Field(min_length=1, max_length=120)
    # 任务描述，允许为空但限制最大长度。
    description: str = Field(default='', max_length=2000)
    # 优先级：高/中/低，后端会做白名单兜底。
    priority: str = Field(default='中', max_length=20)
    # 负责人展示名。
    owner: str = Field(default='销售负责人', max_length=60)
    # 截止时间，支持 YYYY-MM-DD HH:mm:ss 或 YYYY-MM-DD。
    due_time: str | None = Field(default=None)
    # 提醒文案当前不落独立字段，合并进入描述，保留请求兼容性。
    reminder_text: str = Field(default='', max_length=500)
    # 关联客户编号，允许为空或 0。
    related_customer_id: int = Field(default=0, ge=0)
    # 来源由后端强制覆盖为 ai_agent_confirmed，入参仅兼容 task_payload。
    source: str = Field(default='ai_agent_draft', max_length=40)


class TaskDetail(BaseModel):
    """任务详情返回模型。"""

    id: int
    title: str
    description: str
    priority: str
    status: str
    owner: str
    due_time: str
    customer_id: int | None
    source: str
    created_by: int | None
    created_at: str
    updated_at: str
