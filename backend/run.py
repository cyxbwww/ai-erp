from app.main import app

if __name__ == '__main__':
    import uvicorn
    # Windows 环境下 reload 依赖多进程重载，部分权限受限场景会导致服务异常不可用。
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=False)




