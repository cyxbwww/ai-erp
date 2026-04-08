"""知识库数据模型文件：定义知识库问答与索引接口请求结构。"""

from pydantic import BaseModel, Field


class KnowledgeAskRequest(BaseModel):
    """知识库提问请求模型。"""

    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)

