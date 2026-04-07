"""客户跟进记录路由文件：提供跟进记录列表、详情与增删改接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.customer_follow_record import CustomerFollowRecordCreate, CustomerFollowRecordUpdate
from app.services.customer_follow_record_service import CustomerFollowRecordService

router = APIRouter(prefix='/api/customer-follow-record', tags=['customer-follow-record'])


@router.get('/list')
def follow_record_list(
    customer_id: int = Query(ge=1),
    keyword: str = Query(default=''),
    follow_type: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """跟进记录列表接口：支持分页、关键词和跟进类型筛选。"""
    data = CustomerFollowRecordService.list_records(
        db,
        customer_id=customer_id,
        keyword=keyword.strip(),
        follow_type=follow_type.strip(),
        page=page,
        page_size=page_size
    )
    return api_success(data)


@router.get('/detail/{record_id}')
def follow_record_detail(
    record_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """跟进记录详情接口。"""
    data = CustomerFollowRecordService.get_record(db, record_id)
    if not data:
        return api_error('跟进记录不存在')
    return api_success(CustomerFollowRecordService.serialize(db, data))


@router.post('/create')
def follow_record_create(
    payload: CustomerFollowRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新增跟进记录接口。"""
    data = CustomerFollowRecordService.create_record(db, payload, current_user)
    return api_success(data)


@router.put('/update')
def follow_record_update(
    payload: CustomerFollowRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑跟进记录接口。"""
    data = CustomerFollowRecordService.update_record(db, payload, current_user)
    if not data:
        return api_error('跟进记录不存在')
    return api_success(data)


@router.delete('/delete/{record_id}')
def follow_record_delete(
    record_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除跟进记录接口。"""
    ok = CustomerFollowRecordService.delete_record(db, record_id)
    if not ok:
        return api_error('跟进记录不存在')
    return api_success(True)
