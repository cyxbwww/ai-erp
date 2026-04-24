"""AI 调用日志路由文件：提供 ai_call_logs 查询接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.services.ai_call_log_service import AiCallLogService

router = APIRouter(prefix='/api/ai-call-logs', tags=['ai-call-logs'])


@router.get('')
def ai_call_log_list(
    module: str = Query(default=''),
    task_type: str = Query(default=''),
    status: str = Query(default=''),
    keyword: str = Query(default=''),
    start_time: str = Query(default=''),
    end_time: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI 调用日志列表接口：支持模块、任务、状态、关键词和时间范围筛选。"""
    data = AiCallLogService.list_logs(
        db=db,
        module=module.strip(),
        task_type=task_type.strip(),
        status=status.strip(),
        keyword=keyword.strip(),
        start_time=start_time.strip(),
        end_time=end_time.strip(),
        page=page,
        page_size=page_size
    )
    return api_success(data)


@router.get('/summary')
def ai_call_log_summary(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI 效果统计接口：返回全局调用成功率、平均耗时与客户采纳转化。"""
    data = AiCallLogService.get_summary(db=db)
    return api_success(data)


@router.get('/prompt-summary')
def ai_call_log_prompt_summary(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prompt 模板效果统计接口：按模板 key、版本、模块和任务类型聚合调用效果。"""
    data = AiCallLogService.get_prompt_summary(db=db)
    return api_success(data)


@router.get('/{log_id}')
def ai_call_log_detail(
    log_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI 调用日志详情接口：按主键返回完整调用记录。"""
    data = AiCallLogService.get_log_detail(db=db, log_id=log_id)
    if not data:
        return api_error('AI 调用日志不存在')
    return api_success(data)
