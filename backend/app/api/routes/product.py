"""商品路由文件：提供商品管理的列表、详情与增删改接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import api_error, api_success
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix='/api/product', tags=['product'])


@router.get('/list')
def product_list(
    keyword: str = Query(default=''),
    category: str = Query(default=''),
    status: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """商品列表接口：支持关键词、分类、状态筛选和分页查询。"""
    data = ProductService.list_products(
        db,
        keyword=keyword.strip(),
        category=category.strip(),
        status=status.strip(),
        page=page,
        page_size=page_size
    )
    return api_success(data)


@router.get('/detail/{product_id}')
def product_detail(
    product_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """商品详情接口：按商品编号返回完整商品信息。"""
    product = ProductService.get_product(db, product_id)
    if not product:
        return api_error('商品不存在')
    return api_success(ProductService.serialize(product))


@router.post('/create')
def product_create(
    payload: ProductCreate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """商品新增接口：创建商品并校验商品编码唯一性。"""
    exists = ProductService.get_product_by_code(db, payload.code)
    if exists:
        return api_error('商品编码已存在')
    data = ProductService.create_product(db, payload)
    return api_success(data)


@router.put('/update')
def product_update(
    payload: ProductUpdate,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """商品编辑接口：更新商品并校验商品编码冲突。"""
    exists = ProductService.get_product_by_code(db, payload.code)
    if exists and exists.id != payload.id:
        return api_error('商品编码已存在')

    data = ProductService.update_product(db, payload)
    if not data:
        return api_error('商品不存在')
    return api_success(data)


@router.delete('/delete/{product_id}')
def product_delete(
    product_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """商品删除接口：按商品编号删除商品。"""
    ok = ProductService.delete_product(db, product_id)
    if not ok:
        return api_error('商品不存在')
    return api_success(True)

