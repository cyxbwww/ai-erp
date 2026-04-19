from fastapi import APIRouter

from app.api.routes import ai, auth, customer, customer_follow_record, health, knowledge_base, order, product

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(customer.router)
api_router.include_router(customer_follow_record.router)
api_router.include_router(product.router)
api_router.include_router(order.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(ai.router)
