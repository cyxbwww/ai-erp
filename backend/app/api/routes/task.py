"""任务路由文件：提供 AI 草稿确认创建任务接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.task import TaskFromAIDraftCreate
from app.services.task_service import TaskService

router = APIRouter(prefix='/api/tasks', tags=['tasks'])


@router.post('/from-ai-draft')
def create_task_from_ai_draft(
    payload: TaskFromAIDraftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI 任务草稿确认创建接口：用户点击确认后才会真实落库。"""
    try:
        data = TaskService.create_from_ai_draft(db=db, payload=payload, current_user=current_user)
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.get('')
def task_list(
    customer_id: int = Query(ge=1),
    status: str = Query(default=''),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """客户关联任务列表接口：用于客户详情页展示已确认创建的任务。"""
    data = TaskService.list_by_customer(db=db, customer_id=customer_id, status=status)
    return api_success(data)
