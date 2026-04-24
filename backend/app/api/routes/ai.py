"""AI 路由文件：提供多 Agent 统一对话接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.ai_chat import AIChatRequest
from app.services.ai_chat_service import AIChatService

router = APIRouter(prefix='/api/ai', tags=['ai'])


@router.post('/chat')
def ai_chat(
    payload: AIChatRequest,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """多 Agent 统一聊天接口：返回任务类型、计划和各 Agent 结构化输出。"""
    if not payload.scene.strip():
        return api_error('scene 不能为空')
    if not payload.user_message.strip():
        return api_error('user_message 不能为空')

    try:
        data = AIChatService.chat(db=db, request=payload)
        return api_success(data.model_dump())
    except Exception as exc:
        # 编排级异常也返回统一响应结构，避免前端只能显示“请求失败”而看不到真实原因。
        return api_error(f'多 Agent 分析失败：{exc}')
