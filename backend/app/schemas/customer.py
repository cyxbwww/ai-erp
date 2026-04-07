from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    contact_name: str = ''
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = None
    company: str = ''
    level: str = 'normal'
    status: str = 'active'
    source: str = 'manual'
    owner_name: str = ''
    last_follow_at: str | None = None
    remark: str = ''


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    contact_name: str = ''
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = None
    company: str = ''
    level: str = 'normal'
    status: str = 'active'
    source: str = 'manual'
    owner_name: str = ''
    last_follow_at: str | None = None
    remark: str = ''


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str
    updated_at: str
