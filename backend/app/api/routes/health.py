"""健康检查路由文件：用于服务连通性探活。"""

from fastapi import APIRouter

from app.core.response import api_success

router = APIRouter(prefix='/api/health', tags=['health'])


@router.get('/ping')
def ping():
    """健康检查接口：返回服务存活状态。"""
    return api_success({'status': 'up'})
