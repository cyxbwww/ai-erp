"""商品数据模型文件：定义商品模块请求与响应结构。"""

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """商品基础字段模型：定义商品新增与编辑通用字段。"""

    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=60)
    category: str = 'software'
    spec_model: str = ''
    sale_price: float = 0
    unit: str = 'set'
    stock_qty: int = 0
    status: str = 'enabled'
    remark: str = ''


class ProductCreate(ProductBase):
    """商品新增请求模型。"""


class ProductUpdate(ProductBase):
    """商品编辑请求模型。"""

    id: int


class ProductOut(ProductBase):
    """商品响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str
    updated_at: str

