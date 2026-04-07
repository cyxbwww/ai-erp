from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = 'AI 智能销售 ERP API'
    app_version: str = '0.1.0'
    database_url: str = 'sqlite:///./erp.db'
    jwt_secret: str = 'erp-secret-key'


settings = Settings()
