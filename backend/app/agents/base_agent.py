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
    # Agent 能力说明，供编排器追踪和前端展示使用。
    description: str = ''
    # Agent 支持的业务场景，如 customer_detail / order_detail / knowledge_base。
    supported_scenes: list[str] = []
    # Agent 依赖的上游 Agent 名称，用于轻量跳过和后续扩展调度。
    dependencies: list[str] = []

    def get_profile(self) -> dict[str, Any]:
        """返回 Agent 统一元信息，避免各处重复拼装展示数据。"""
        return {
            'name': self.name,
            'description': self.description,
            'supported_scenes': list(self.supported_scenes),
            'dependencies': list(self.dependencies)
        }

    def build_execution_meta(
        self,
        status: str = 'success',
        confidence: float = 0.8,
        next_recommendation: str = '',
        message: str = ''
    ) -> dict[str, Any]:
        """构建统一执行元数据，供编排器和前端判断执行质量。"""
        allowed_status = {'success', 'partial_failed', 'failed', 'skipped'}
        normalized_status = status if status in allowed_status else 'success'
        normalized_confidence = min(max(float(confidence or 0), 0.0), 1.0)
        return {
            'status': normalized_status,
            'confidence': normalized_confidence,
            'next_recommendation': (next_recommendation or '').strip(),
            'message': (message or '').strip()
        }

    def attach_execution_meta(
        self,
        output: dict[str, Any],
        status: str = 'success',
        confidence: float = 0.8,
        next_recommendation: str = '',
        message: str = ''
    ) -> dict[str, Any]:
        """在保留原业务字段的前提下追加执行元数据和 Agent 元信息。"""
        safe_output = output if isinstance(output, dict) else {'data': output}
        safe_output['execution_meta'] = self.build_execution_meta(
            status=status,
            confidence=confidence,
            next_recommendation=next_recommendation,
            message=message
        )
        safe_output['agent_meta'] = self.get_profile()
        return safe_output

    def build_skipped_output(self, message: str, confidence: float = 0.0) -> dict[str, Any]:
        """构建标准跳过输出，保证跳过场景也有稳定结构。"""
        return self.attach_execution_meta(
            output={},
            status='skipped',
            confidence=confidence,
            next_recommendation='请先补齐上游业务信息后再执行该 Agent。',
            message=message
        )

    @abstractmethod
    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 主逻辑并返回结构化结果。"""
