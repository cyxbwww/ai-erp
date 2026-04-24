"""客户路由文件：提供客户列表、详情与增删改接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.customer_service import CustomerService

router = APIRouter(prefix='/api/customer', tags=['customer'])


@router.get('/list')
def customer_list(
    keyword: str = Query(default=''),
    level: str = Query(default=''),
    status: str = Query(default=''),
    source: str = Query(default=''),
    owner_name: str = Query(default=''),
    created_start: str = Query(default=''),
    created_end: str = Query(default=''),
    follow_start: str = Query(default=''),
    follow_end: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """客户列表接口：支持关键词、枚举、负责人和时间范围筛选。"""
    data = CustomerService.list_customers(
        db,
        keyword=keyword.strip(),
        level=level.strip(),
        status=status.strip(),
        source=source.strip(),
        owner_name=owner_name.strip(),
        created_start=created_start.strip(),
        created_end=created_end.strip(),
        follow_start=follow_start.strip(),
        follow_end=follow_end.strip(),
        page=page,
        page_size=page_size
    )
    return api_success(data)


@router.post('/create')
def customer_create(
    payload: CustomerCreate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新增客户接口。"""
    data = CustomerService.create_customer(db, payload)
    return api_success(data)


@router.put('/update')
def customer_update(
    payload: CustomerUpdate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑客户接口。"""
    data = CustomerService.update_customer(db, payload)
    if not data:
        return api_error('客户不存在')
    return api_success(data)


@router.delete('/delete/{customer_id}')
def customer_delete(
    customer_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除客户接口。"""
    ok = CustomerService.delete_customer(db, customer_id)
    if not ok:
        return api_error('客户不存在')
    return api_success(True)


@router.get('/detail/{customer_id}')
def customer_detail(
    customer_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """客户详情接口。"""
    customer = CustomerService.get_customer(db, customer_id)
    if not customer:
        return api_error('客户不存在')
    return api_success(CustomerService.serialize(customer))
