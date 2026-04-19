"""BaseAgent 抽象基类：定义所有 Agent 的统一执行接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.ai_chat import AIChatRequest


class BaseAgent(ABC):
    """多 Agent 抽象基类。"""

    # Agent 唯一名称，供编排器路由使用。
    name: str = 'base_agent'

    @abstractmethod
    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 主逻辑并返回结构化结果。"""

