"""系统配置文件：集中管理应用与第三方服务配置。"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """应用配置对象。"""

    app_name: str = 'AI 智能销售 ERP API'
    app_version: str = '0.1.0'
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./erp.db')
    jwt_secret: str = os.getenv('JWT_SECRET', 'erp-secret-key')
    # DeepSeek 兼容 OpenAI SDK 配置。
    deepseek_base_url: str = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    deepseek_model: str = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    deepseek_api_key: str = os.getenv('DEEPSEEK_API_KEY', '')


settings = Settings()

