"""AI 调用记录模型：用于存储多 Agent 调用链路追踪信息。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIRecord(Base):
    """AI 调用记录表：保存请求、计划、执行明细与最终结果。"""

    __tablename__ = 'ai_records'

    # 主键编号
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment='AI 调用记录主键编号')
    # 调用场景
    scene: Mapped[str] = mapped_column(String(60), default='', index=True, comment='调用场景')
    # 用户问题
    user_message: Mapped[str] = mapped_column(Text, default='', comment='用户输入问题')
    # 请求上下文 JSON
    context_json: Mapped[str] = mapped_column(Text, default='{}', comment='请求上下文 JSON 字符串')
    # 任务类型
    task_type: Mapped[str] = mapped_column(String(80), default='', index=True, comment='任务类型')
    # Supervisor 计划 JSON
    plan_json: Mapped[str] = mapped_column(Text, default='{}', comment='执行计划 JSON 字符串')
    # 所有 Agent 输出 JSON
    agent_outputs_json: Mapped[str] = mapped_column(Text, default='{}', comment='Agent 输出 JSON 字符串')
    # Agent 执行明细 JSON
    agent_details_json: Mapped[str] = mapped_column(Text, default='[]', comment='Agent 执行明细 JSON 字符串')
    # 最终摘要
    final_summary: Mapped[str] = mapped_column(Text, default='', comment='最终摘要')
    # 总耗时毫秒
    total_duration_ms: Mapped[int] = mapped_column(Integer, default=0, comment='整体请求耗时毫秒')
    # 执行状态：success/partial_failed/failed
    status: Mapped[str] = mapped_column(String(30), default='success', index=True, comment='执行状态')
    # 错误信息
    error_message: Mapped[str] = mapped_column(Text, default='', comment='错误信息')
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='创建时间')

