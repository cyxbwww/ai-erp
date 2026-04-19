"""AI Chat 服务：封装 /api/ai/chat 的编排调用入口。"""

from sqlalchemy.orm import Session

from app.schemas.ai_chat import AIChatRequest, AIChatResult
from app.services.agent_orchestrator import AgentOrchestrator


class AIChatService:
    """统一 AI 对话服务。"""

    @staticmethod
    def chat(db: Session, request: AIChatRequest) -> AIChatResult:
        """执行多 Agent 编排并返回结构化结果。"""
        orchestrator = AgentOrchestrator()
        return orchestrator.execute(db=db, request=request)

