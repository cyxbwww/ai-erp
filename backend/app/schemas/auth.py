"""认证 Schema 文件：定义登录与刷新令牌接口的数据模型。"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求参数。"""
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求参数。"""
    refresh_token: str = Field(min_length=1)


class AuthTokenData(BaseModel):
    """认证接口返回数据模型。"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    token: str
    username: str
    role: str
    permissions: list[str]
