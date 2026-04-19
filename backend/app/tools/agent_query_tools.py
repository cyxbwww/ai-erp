"""多 Agent 查询工具：统一封装 customer/order/rag 数据读取能力。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.order import Order
from app.services.customer_follow_record_service import CustomerFollowRecordService
from app.services.customer_service import CustomerService
from app.services.knowledge_base_service import KnowledgeRAGService
from app.services.order_service import OrderService


class AgentQueryTools:
    """多 Agent 工具集：为 Agent 提供可复用、可替换的数据访问方法。"""

    @staticmethod
    def get_customer_insight_context(db: Session, customer_id: int, follow_limit: int = 5) -> dict[str, Any]:
        """获取客户洞察所需上下文：客户详情、跟进记录、订单概览。"""
        customer = CustomerService.get_customer(db, customer_id)
        if not customer:
            raise ValueError('客户不存在')

        customer_data = CustomerService.serialize(customer)
        follow_page = CustomerFollowRecordService.list_records(
            db=db,
            customer_id=customer_id,
            keyword='',
            follow_type='',
            page=1,
            page_size=max(1, follow_limit)
        )
        follow_records = follow_page.get('list', [])

        # 订单历史先使用简化查询，后续可替换为专用订单检索工具。
        order_rows = (
            db.query(Order)
            .filter(Order.customer_id == customer_id)
            .order_by(desc(Order.id))
            .limit(5)
            .all()
        )
        order_history = [
            {
                'id': order.id,
                'order_no': order.order_no,
                'status': order.status,
                'total_amount': float(order.total_amount or 0)
            }
            for order in order_rows
        ]

        order_count = len(order_history)
        total_amount = sum(item['total_amount'] for item in order_history)
        return {
            'customer': customer_data,
            'follow_records': follow_records,
            'order_history': order_history,
            'order_summary': {
                'order_count': order_count,
                'total_amount': round(total_amount, 2)
            }
        }

    @staticmethod
    def get_order_analysis_context(db: Session, order_id: int) -> dict[str, Any]:
        """获取订单分析上下文：复用既有订单详情服务。"""
        detail = OrderService.get_order_detail(db, order_id)
        if not detail:
            raise ValueError('订单不存在')
        return detail

    @staticmethod
    def ask_knowledge(question: str, top_k: int = 4) -> dict[str, Any]:
        """调用知识库检索问答服务。"""
        return KnowledgeRAGService.ask(question=question, top_k=top_k)

    @staticmethod
    def get_knowledge_rag_payload(question: str, top_k: int = 4) -> dict[str, Any]:
        """获取 Knowledge Agent 专用结构：轻量封装现有 RAG 返回格式。"""
        rag_data = KnowledgeRAGService.ask(question=question, top_k=top_k)

        hits: list[dict[str, Any]] = []
        for chunk in rag_data.get('retrieved_chunks', []):
            title = str(chunk.get('source', '')).strip()
            content = str(chunk.get('content', '')).strip()
            score = float(chunk.get('score') or 0.0)
            if not title and not content:
                continue
            hits.append(
                {
                    'title': title,
                    'content': content,
                    'score': round(score, 6)
                }
            )

        references: list[str] = []
        for item in rag_data.get('sources', []):
            source = str(item.get('source', '')).strip()
            if source and source not in references:
                references.append(source)

        return {
            'query': str(rag_data.get('question', question)).strip(),
            'hits': hits,
            'summary': str(rag_data.get('answer', '')).strip(),
            'references': references
        }
