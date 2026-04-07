"""订单数据模型文件：定义订单模块请求与响应结构。"""

from pydantic import BaseModel, Field


class OrderItemPayload(BaseModel):
    """订单明细请求模型：用于创建或更新订单时提交商品明细。"""

    product_id: int
    quantity: int = Field(ge=1, default=1)
    unit_price: float | None = Field(default=None, ge=0)


class OrderCreate(BaseModel):
    """订单新增请求模型。"""

    customer_id: int
    status: str = 'draft'
    remark: str = ''
    items: list[OrderItemPayload]


class OrderUpdate(BaseModel):
    """订单编辑请求模型。"""

    id: int
    customer_id: int
    status: str = 'draft'
    remark: str = ''
    items: list[OrderItemPayload]


class OrderStatusUpdate(BaseModel):
    """订单状态流转请求模型。"""

    id: int
    status: str


class OrderAIAnalysisPayload(BaseModel):
    """订单 AI 分析请求模型：用于区分分析类型。"""

    analysis_type: str = 'analysis'
