"""AI 调用日志 Schema 文件：定义日志查询接口的返回结构。"""

from pydantic import BaseModel


class AiCallLogListItem(BaseModel):
    """AI 调用日志列表项：列表页只返回摘要字段，避免长文本影响响应体积。"""

    id: int
    module: str | None = None
    task_type: str | None = None
    prompt: str
    response: str | None = None
    status: str
    error_message: str | None = None
    model_name: str
    latency_ms: int | None = None
    created_at: str


class AiCallLogDetail(BaseModel):
    """AI 调用日志详情：返回完整 prompt、response 和错误信息。"""

    id: int
    module: str | None = None
    task_type: str | None = None
    prompt: str
    response: str | None = None
    status: str
    error_message: str | None = None
    model_name: str
    latency_ms: int | None = None
    created_at: str


class AiCallLogListResult(BaseModel):
    """AI 调用日志分页结果：用于承载总数、分页参数和列表数据。"""

    total: int
    page: int
    page_size: int
    items: list[AiCallLogListItem]
