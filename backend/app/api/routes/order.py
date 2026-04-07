"""订单路由文件：提供订单管理、状态流转与 AI 分析接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.order import OrderAIAnalysisPayload, OrderCreate, OrderStatusUpdate, OrderUpdate
from app.services.order_ai_service import OrderAIService
from app.services.order_service import OrderService

router = APIRouter(prefix='/api/order', tags=['order'])


@router.get('/list')
def order_list(
    keyword: str = Query(default=''),
    status: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单列表接口：支持关键词、状态筛选与分页。"""
    data = OrderService.list_orders(
        db,
        keyword=keyword.strip(),
        status=status.strip(),
        page=page,
        page_size=page_size
    )
    return api_success(data)


@router.get('/detail/{order_id}')
def order_detail(
    order_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单详情接口：返回订单主信息与明细列表。"""
    data = OrderService.get_order_detail(db, order_id)
    if not data:
        return api_error('订单不存在')
    return api_success(data)


@router.post('/create')
def order_create(
    payload: OrderCreate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单新增接口：创建订单并写入订单明细。"""
    try:
        data = OrderService.create_order(db, payload)
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.put('/update')
def order_update(
    payload: OrderUpdate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单编辑接口：更新订单主信息与订单明细。"""
    try:
        data = OrderService.update_order(db, payload)
        if not data:
            return api_error('订单不存在')
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.put('/status')
def order_status_update(
    payload: OrderStatusUpdate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单状态流转接口：支持草稿->确认->完成/取消。"""
    try:
        data = OrderService.update_order_status(db, payload.id, payload.status)
        if not data:
            return api_error('订单不存在')
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.post('/{order_id}/ai-analysis')
def order_ai_analysis(
    order_id: int,
    payload: OrderAIAnalysisPayload,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单 AI 分析接口：支持订单分析、风险检测与销售建议。"""
    try:
        data = OrderAIService.analyze_order(db, order_id, payload.analysis_type)
        return api_success(data)
    except ValueError as exc:
        return api_error(str(exc))


@router.delete('/delete/{order_id}')
def order_delete(
    order_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单删除接口：按订单编号删除订单和明细。"""
    ok = OrderService.delete_order(db, order_id)
    if not ok:
        return api_error('订单不存在')
    return api_success(True)

