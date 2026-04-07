from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginData(BaseModel):
    token: str
    username: str
    role: str
    permissions: list[str]
