from pydantic import BaseModel, Field


class CustomerFollowRecordBase(BaseModel):
    """客户跟进记录基础字段。"""

    customer_id: int = Field(ge=1)
    follow_type: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1, max_length=2000)
    result: str = Field(default='', max_length=255)
    next_follow_time: str | None = None
    source_type: str = Field(default='manual', max_length=30)
    source_module: str | None = Field(default=None, max_length=60)
    source_ref_id: int | None = Field(default=None, ge=1)


class CustomerFollowRecordCreate(CustomerFollowRecordBase):
    """新增客户跟进记录请求模型。"""


class CustomerFollowRecordUpdate(BaseModel):
    """编辑客户跟进记录请求模型。"""

    id: int = Field(ge=1)
    customer_id: int = Field(ge=1)
    follow_type: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1, max_length=2000)
    result: str = Field(default='', max_length=255)
    next_follow_time: str | None = None
    source_type: str | None = Field(default=None, max_length=30)
    source_module: str | None = Field(default=None, max_length=60)
    source_ref_id: int | None = Field(default=None, ge=1)
