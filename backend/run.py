"""后端启动脚本：统一使用 settings 中的环境变量配置启动 FastAPI。"""

from app.main import app
from app.core.config import settings


if __name__ == '__main__':
    import uvicorn

    # 支持通过 backend/.env 或系统环境变量覆盖监听地址，便于本地排查端口占用问题。
    host = settings.backend_host
    port = settings.backend_port
    # Windows 环境下 reload 依赖多进程重载，部分权限受限场景会导致服务异常不可用。
    uvicorn.run('app.main:app', host=host, port=port, reload=False)
