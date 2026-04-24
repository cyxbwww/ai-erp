"""AI 调用日志模型文件：定义 ai_call_logs 表结构，用于记录模型调用明细。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AiCallLog(Base):
    """AI 调用日志表：保存每次模型调用的输入、输出、状态与耗时。"""

    __tablename__ = 'ai_call_logs'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='AI 调用日志主键编号')
    # 调用模块：customer/order/knowledge_base 等，可为空
    module: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True, comment='AI 调用所属业务模块')
    # 任务类型：follow_advice/order_analysis/rag_answer 等，可为空
    task_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment='AI 调用任务类型')
    # 用户提示词：记录传给模型的 user_prompt
    prompt: Mapped[str] = mapped_column(Text, default='', comment='传给模型的用户提示词')
    # 模型返回内容：成功时记录原始返回文本或解析后的 JSON 字符串
    response: Mapped[str | None] = mapped_column(Text, nullable=True, comment='模型原始返回文本或解析后的 JSON 字符串')
    # 调用状态：success/failed
    status: Mapped[str] = mapped_column(String(20), default='success', index=True, comment='AI 调用状态')
    # 错误信息：失败时记录异常描述
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment='AI 调用错误信息')
    # 模型名称：默认 deepseek-chat
    model_name: Mapped[str] = mapped_column(String(80), default='deepseek-chat', comment='模型名称')
    # 调用耗时：单位毫秒，可为空
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='AI 调用耗时毫秒数')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, comment='创建时间')
