from fastapi import APIRouter

from app.api.routes import ai, ai_call_log, auth, customer, customer_follow_record, health, knowledge_base, order, product, prompt_template, task

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(customer.router)
api_router.include_router(customer_follow_record.router)
api_router.include_router(product.router)
api_router.include_router(order.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(ai.router)
api_router.include_router(ai_call_log.router)
api_router.include_router(prompt_template.router)
api_router.include_router(task.router)
