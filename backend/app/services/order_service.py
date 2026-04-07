"""订单服务文件：封装订单主表与明细表的增删改查业务逻辑。"""

from datetime import datetime

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderItemPayload, OrderUpdate


class OrderService:
    """订单业务服务：统一处理订单列表、详情、创建、更新、删除。"""

    # 订单状态流转规则：只允许按业务流程推进。
    STATUS_TRANSITION_MAP = {
        'draft': {'confirmed', 'cancelled'},
        'confirmed': {'completed', 'cancelled'},
        'completed': set(),
        'cancelled': set()
    }

    @staticmethod
    def list_orders(
        db: Session,
        keyword: str,
        status: str,
        page: int,
        page_size: int
    ) -> dict:
        """订单列表查询：支持关键词与状态筛选，并返回分页数据。"""
        query = db.query(Order, Customer).join(Customer, Customer.id == Order.customer_id)

        if keyword:
            like_keyword = f'%{keyword}%'
            query = query.filter(
                or_(
                    Order.order_no.like(like_keyword),
                    Customer.name.like(like_keyword)
                )
            )
        if status:
            query = query.filter(Order.status == status)

        total = query.with_entities(func.count(Order.id)).scalar() or 0
        rows = (
            query.order_by(desc(Order.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 统计当前页订单的明细行数，减少前端展示时的额外查询。
        order_ids = [row[0].id for row in rows]
        item_count_map: dict[int, int] = {}
        if order_ids:
            count_rows = (
                db.query(OrderItem.order_id, func.count(OrderItem.id))
                .filter(OrderItem.order_id.in_(order_ids))
                .group_by(OrderItem.order_id)
                .all()
            )
            item_count_map = {int(order_id): int(count) for order_id, count in count_rows}

        items: list[dict] = []
        for order, customer in rows:
            items.append(OrderService.serialize_order(order, customer.name, item_count_map.get(order.id, 0)))

        return {
            'list': items,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def get_order(db: Session, order_id: int) -> Order | None:
        """按编号查询订单主表。"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_order_items(db: Session, order_id: int) -> list[OrderItem]:
        """查询订单明细列表。"""
        return (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order_id)
            .order_by(OrderItem.id.asc())
            .all()
        )

    @staticmethod
    def get_order_detail(db: Session, order_id: int) -> dict | None:
        """查询订单详情：包含主表与明细。"""
        order = OrderService.get_order(db, order_id)
        if not order:
            return None

        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        items = OrderService.get_order_items(db, order.id)

        return {
            'id': order.id,
            'order_no': order.order_no,
            'customer_id': order.customer_id,
            'customer_name': customer.name if customer else '',
            'status': order.status,
            'total_amount': float(order.total_amount or 0),
            'remark': order.remark,
            'created_at': OrderService._format_datetime(order.created_at),
            'updated_at': OrderService._format_datetime(order.updated_at),
            'items': [OrderService.serialize_order_item(item) for item in items]
        }

    @staticmethod
    def create_order(db: Session, payload: OrderCreate) -> dict:
        """创建订单（含明细）：自动计算明细小计与订单总金额。"""
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise ValueError('客户不存在')
        if not payload.items:
            raise ValueError('订单明细不能为空')

        order = Order(
            order_no=OrderService.generate_order_no(),
            customer_id=payload.customer_id,
            status=payload.status,
            total_amount=0,
            remark=payload.remark
        )
        db.add(order)
        db.flush()

        total_amount = OrderService._replace_order_items(db, order.id, payload.items)
        order.total_amount = total_amount

        db.commit()
        return OrderService.get_order_detail(db, order.id) or {}

    @staticmethod
    def update_order(db: Session, payload: OrderUpdate) -> dict | None:
        """更新订单（含明细）：重建明细并重新计算总金额。"""
        order = OrderService.get_order(db, payload.id)
        if not order:
            return None
        if not payload.items:
            raise ValueError('订单明细不能为空')

        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise ValueError('客户不存在')

        order.customer_id = payload.customer_id
        order.status = payload.status
        order.remark = payload.remark

        total_amount = OrderService._replace_order_items(db, order.id, payload.items)
        order.total_amount = total_amount

        db.commit()
        return OrderService.get_order_detail(db, order.id)

    @staticmethod
    def delete_order(db: Session, order_id: int) -> bool:
        """删除订单：先删明细再删主表。"""
        order = OrderService.get_order(db, order_id)
        if not order:
            return False

        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
        db.delete(order)
        db.commit()
        return True

    @staticmethod
    def update_order_status(db: Session, order_id: int, target_status: str) -> dict | None:
        """更新订单状态：按预设状态机执行流转校验。"""
        order = OrderService.get_order(db, order_id)
        if not order:
            return None

        current_status = order.status
        target_status = (target_status or '').strip()

        if target_status not in OrderService.STATUS_TRANSITION_MAP:
            raise ValueError('目标状态不合法')
        if target_status == current_status:
            return OrderService.get_order_detail(db, order_id)

        allowed = OrderService.STATUS_TRANSITION_MAP.get(current_status, set())
        if target_status not in allowed:
            raise ValueError('当前状态不允许流转到目标状态')

        order.status = target_status
        db.commit()
        return OrderService.get_order_detail(db, order_id)

    @staticmethod
    def _replace_order_items(db: Session, order_id: int, item_payloads: list[OrderItemPayload]) -> float:
        """重建订单明细并返回订单总金额。"""
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

        total_amount = 0.0
        for item in item_payloads:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise ValueError(f'商品不存在：{item.product_id}')

            # 单价优先使用前端传入值，否则回退为当前商品销售单价。
            unit_price = float(item.unit_price if item.unit_price is not None else product.sale_price or 0)
            if unit_price < 0:
                unit_price = 0

            quantity = int(item.quantity)
            if quantity <= 0:
                raise ValueError('商品数量必须大于 0')
            # 下单数量不能超过商品库存，避免超卖。
            if quantity > int(product.stock_qty or 0):
                raise ValueError(f'商品库存不足：{product.name}，可用库存 {int(product.stock_qty or 0)}')

            subtotal = round(unit_price * quantity, 2)
            total_amount += subtotal

            db.add(
                OrderItem(
                    order_id=order_id,
                    product_id=product.id,
                    product_name=product.name,
                    product_code=product.code,
                    unit=product.unit,
                    unit_price=unit_price,
                    quantity=quantity,
                    subtotal=subtotal
                )
            )

        return round(total_amount, 2)

    @staticmethod
    def generate_order_no() -> str:
        """生成订单编号：ORD + 年月日时分秒。"""
        return f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}'

    @staticmethod
    def serialize_order(order: Order, customer_name: str, item_count: int) -> dict:
        """序列化订单列表项。"""
        return {
            'id': order.id,
            'order_no': order.order_no,
            'customer_id': order.customer_id,
            'customer_name': customer_name,
            'status': order.status,
            'total_amount': float(order.total_amount or 0),
            'item_count': item_count,
            'remark': order.remark,
            'created_at': OrderService._format_datetime(order.created_at),
            'updated_at': OrderService._format_datetime(order.updated_at)
        }

    @staticmethod
    def serialize_order_item(item: OrderItem) -> dict:
        """序列化订单明细项。"""
        return {
            'id': item.id,
            'order_id': item.order_id,
            'product_id': item.product_id,
            'product_name': item.product_name,
            'product_code': item.product_code,
            'unit': item.unit,
            'unit_price': float(item.unit_price or 0),
            'quantity': int(item.quantity or 0),
            'subtotal': float(item.subtotal or 0)
        }

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        """格式化日期时间。"""
        if not value:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')

