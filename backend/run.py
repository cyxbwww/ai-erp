"""后端启动脚本：支持通过环境变量覆盖端口，避免本地端口冲突导致接口不可用。"""

import os

from app.main import app

if __name__ == '__main__':
    import uvicorn

    # 支持通过 BACKEND_HOST / BACKEND_PORT 覆盖默认监听地址，便于本地排查端口占用问题。
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '8000'))
    # Windows 环境下 reload 依赖多进程重载，部分权限受限场景会导致服务异常不可用。
    uvicorn.run('app.main:app', host=host, port=port, reload=False)
