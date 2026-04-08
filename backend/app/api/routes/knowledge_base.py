"""知识库路由文件：提供文档列表、索引重建和知识库问答接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.knowledge_base import KnowledgeAskRequest
from app.services.knowledge_base_service import KnowledgeRAGService

router = APIRouter(prefix='/api/knowledge-base', tags=['knowledge-base'])


@router.get('/documents')
def kb_documents(
    _current_user: User = Depends(get_current_user),
    _db: Session = Depends(get_db)
):
    """知识库文档列表接口。"""
    data = KnowledgeRAGService.list_documents()
    return api_success(data)


@router.post('/rebuild')
def kb_rebuild(
    _current_user: User = Depends(get_current_user),
    _db: Session = Depends(get_db)
):
    """知识库索引重建接口。"""
    data = KnowledgeRAGService.rebuild_index()
    return api_success(data)


@router.post('/ask')
def kb_ask(
    payload: KnowledgeAskRequest,
    _current_user: User = Depends(get_current_user),
    _db: Session = Depends(get_db)
):
    """知识库问答接口：返回答案、命中文档与命中片段。"""
    try:
        data = KnowledgeRAGService.ask(payload.question, top_k=payload.top_k)
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))

