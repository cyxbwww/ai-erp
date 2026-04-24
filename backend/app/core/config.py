"""系统配置文件：集中管理后端环境变量、数据库、JWT 与 AI 服务配置。"""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


# 后端目录路径：用于固定读取 backend/.env，避免不同启动目录导致配置文件找不到。
BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / '.env'

# 优先加载项目本地 backend/.env，覆盖当前进程里的同名变量，避免 Windows 用户级旧 Key 干扰本项目。
load_dotenv(dotenv_path=ENV_FILE, override=True)


class Settings(BaseSettings):
    """应用配置对象：统一从环境变量和 backend/.env 读取配置。"""

    # 只读取 backend/.env，extra=ignore 用于兼容后续新增但当前未使用的配置项。
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # 应用基础信息：用于 FastAPI 文档标题与版本展示。
    app_name: str = 'AI 智能销售 ERP API'
    app_version: str = '0.1.0'

    # 后端监听配置：run.py 统一从 settings 读取，未配置 .env 时使用默认值。
    backend_host: str = '0.0.0.0'
    backend_port: int = 8000

    # 数据库配置：默认使用项目现有 SQLite 文件。
    database_url: str = 'sqlite:///./erp.db'

    # JWT 配置：JWT_SECRET_KEY 为新规范，JWT_SECRET 用于兼容旧环境变量。
    jwt_secret_key: str = Field(
        default='erp-secret-key',
        validation_alias=AliasChoices('JWT_SECRET_KEY', 'JWT_SECRET')
    )
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7

    # DeepSeek 兼容 OpenAI SDK 配置。
    deepseek_api_key: str = ''
    deepseek_base_url: str = 'https://api.deepseek.com'
    deepseek_model: str = 'deepseek-v4-flash'

    @property
    def jwt_secret(self) -> str:
        """兼容旧代码中的 settings.jwt_secret 访问方式。"""
        return self.jwt_secret_key


settings = Settings()
