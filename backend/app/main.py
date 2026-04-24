from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.core.auth import AuthError
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models.customer import Customer
from app.models.customer_follow_record import CustomerFollowRecord
from app.models.ai_call_log import AiCallLog
from app.models.ai_record import AIRecord
from app.models.memory_record import MemoryRecord
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.task import Task
from app.models.user import User
from app.services.auth_service import AuthService

# 触发模型加载，确保用户表与客户表等数据表被创建。
_ = User.__tablename__
_ = Customer.__tablename__
_ = CustomerFollowRecord.__tablename__
_ = AiCallLog.__tablename__
_ = AIRecord.__tablename__
_ = MemoryRecord.__tablename__
_ = Product.__tablename__
_ = Order.__tablename__
_ = OrderItem.__tablename__
_ = Task.__tablename__
Base.metadata.create_all(bind=engine)


def _migrate_customer_table() -> None:
    """为历史数据库补齐 customers 新增字段。"""
    alter_sql_map = {
        'contact_name': "ALTER TABLE customers ADD COLUMN contact_name VARCHAR(60) DEFAULT ''",
        'owner_name': "ALTER TABLE customers ADD COLUMN owner_name VARCHAR(60) DEFAULT ''",
        'last_follow_at': 'ALTER TABLE customers ADD COLUMN last_follow_at DATETIME'
    }

    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        ).fetchone()
        if not table_exists:
            return

        columns = conn.execute(text('PRAGMA table_info(customers)')).fetchall()
        existing = {row[1] for row in columns}
        for col, sql in alter_sql_map.items():
            if col not in existing:
                conn.execute(text(sql))


_migrate_customer_table()


def _migrate_customer_follow_record_table() -> None:
    """为历史数据库补齐 customer_follow_records 来源追踪字段。"""
    alter_sql_map = {
        'source_type': "ALTER TABLE customer_follow_records ADD COLUMN source_type VARCHAR(30) DEFAULT 'manual'",
        'source_module': 'ALTER TABLE customer_follow_records ADD COLUMN source_module VARCHAR(60)',
        'source_ref_id': 'ALTER TABLE customer_follow_records ADD COLUMN source_ref_id INTEGER'
    }

    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_follow_records'")
        ).fetchone()
        if not table_exists:
            return

        columns = conn.execute(text('PRAGMA table_info(customer_follow_records)')).fetchall()
        existing = {row[1] for row in columns}
        for col, sql in alter_sql_map.items():
            if col not in existing:
                conn.execute(text(sql))


_migrate_customer_follow_record_table()


def _migrate_ai_call_log_table() -> None:
    """为历史数据库补齐 ai_call_logs 的 Prompt 模板追踪字段。"""
    alter_sql_map = {
        'prompt_template_key': 'ALTER TABLE ai_call_logs ADD COLUMN prompt_template_key VARCHAR(100)',
        'prompt_version': 'ALTER TABLE ai_call_logs ADD COLUMN prompt_version VARCHAR(30)'
    }

    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_call_logs'")
        ).fetchone()
        if not table_exists:
            return

        columns = conn.execute(text('PRAGMA table_info(ai_call_logs)')).fetchall()
        existing = {row[1] for row in columns}
        for col, sql in alter_sql_map.items():
            if col not in existing:
                conn.execute(text(sql))


_migrate_ai_call_log_table()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:5173', 'http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


@app.exception_handler(AuthError)
def auth_error_handler(_request: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content={
            'code': 401,
            'message': str(exc),
            'data': None
        }
    )


@app.on_event('startup')
def seed_admin_user() -> None:
    db = SessionLocal()
    try:
        AuthService.ensure_seed_admin(db)
    finally:
        db.close()


app.include_router(api_router)


