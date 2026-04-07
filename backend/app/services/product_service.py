"""商品服务文件：封装商品列表查询、详情、新增、编辑、删除等业务逻辑。"""

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """商品业务服务：统一处理商品 CRUD 与列表筛选分页。"""

    @staticmethod
    def list_products(
        db: Session,
        keyword: str,
        category: str,
        status: str,
        page: int,
        page_size: int
    ) -> dict:
        """商品列表查询：支持关键词、分类、状态筛选和分页。"""
        query = db.query(Product)

        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(
                or_(
                    Product.name.like(like_keyword),
                    Product.code.like(like_keyword)
                )
            )

        if category:
            query = query.filter(Product.category == category)
        if status:
            query = query.filter(Product.status == status)

        total = query.with_entities(func.count(Product.id)).scalar() or 0
        items = (
            query.order_by(desc(Product.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            'list': [ProductService.serialize(item) for item in items],
            'total': total,
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_product(db: Session, product_id: int) -> Product | None:
        """按编号查询商品详情。"""
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_product_by_code(db: Session, code: str) -> Product | None:
        """按商品编码查询商品，常用于编码唯一性校验。"""
        return db.query(Product).filter(Product.code == code).first()

    @staticmethod
    def create_product(db: Session, payload: ProductCreate) -> dict:
        """创建商品。"""
        product = Product(
            name=payload.name,
            code=payload.code,
            category=payload.category,
            spec_model=payload.spec_model,
            sale_price=max(0, payload.sale_price),
            unit=payload.unit,
            stock_qty=max(0, payload.stock_qty),
            status=payload.status,
            remark=payload.remark
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return ProductService.serialize(product)

    @staticmethod
    def update_product(db: Session, payload: ProductUpdate) -> dict | None:
        """编辑商品，商品不存在时返回 None。"""
        product = ProductService.get_product(db, payload.id)
        if not product:
            return None

        product.name = payload.name
        product.code = payload.code
        product.category = payload.category
        product.spec_model = payload.spec_model
        product.sale_price = max(0, payload.sale_price)
        product.unit = payload.unit
        product.stock_qty = max(0, payload.stock_qty)
        product.status = payload.status
        product.remark = payload.remark

        db.commit()
        db.refresh(product)
        return ProductService.serialize(product)

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """删除商品，删除成功返回 True。"""
        product = ProductService.get_product(db, product_id)
        if not product:
            return False

        db.delete(product)
        db.commit()
        return True

    @staticmethod
    def serialize(product: Product) -> dict:
        """将商品数据库对象序列化为接口响应结构。"""
        return {
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'category': product.category,
            'spec_model': product.spec_model,
            'sale_price': float(product.sale_price or 0),
            'unit': product.unit,
            'stock_qty': int(product.stock_qty or 0),
            'status': product.status,
            'remark': product.remark,
            'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else '',
            'updated_at': product.updated_at.strftime('%Y-%m-%d %H:%M:%S') if product.updated_at else ''
        }

