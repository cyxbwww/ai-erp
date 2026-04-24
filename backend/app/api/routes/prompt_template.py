"""Prompt 模板路由文件：提供内存模板的只读调试接口。"""

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.core.response import api_error, api_success
from app.models.user import User
from app.services.prompt_template_service import PromptTemplateService

router = APIRouter(prefix='/api/prompt-templates', tags=['prompt-templates'])


@router.get('')
def prompt_template_list(
    _current_user: User = Depends(get_current_user)
):
    """Prompt 模板列表接口：返回模板基础信息，便于调试和确认注册状态。"""
    return api_success(PromptTemplateService.list_templates())


@router.get('/{template_key}')
def prompt_template_detail(
    template_key: str,
    _current_user: User = Depends(get_current_user)
):
    """Prompt 模板详情接口：返回指定模板的完整系统提示词和用户模板。"""
    data = PromptTemplateService.get_template(template_key)
    if not data:
        return api_error('Prompt 模板不存在')
    return api_success(data)
