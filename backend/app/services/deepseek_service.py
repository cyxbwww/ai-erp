"""DeepSeek 服务文件：封装基于 OpenAI SDK 兼容协议的 DeepSeek 调用逻辑。"""

import json
import time
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.services.ai_call_log_service import AiCallLogService
from app.services.llm_response_parser import LLMResponseParser


class DeepSeekService:
    """DeepSeek 调用服务：统一处理提示词、模型调用与 JSON 解析。"""

    # 系统提示词：约束模型只返回 JSON，避免输出额外说明文本。
    SYSTEM_PROMPT = (
        '你是一名销售管理助手，请根据客户资料和历史跟进记录进行分析，'
        '不要输出系统内部枚举值（如 normal、intention、key 等），必须使用中文业务表达，如普通客户、意向客户、重点客户，'
        '并严格按照指定 JSON 格式返回结果，不要输出多余文本。'
    )

    # DeepSeek 兼容 OpenAI 接口的基础地址，保留类属性便于历史代码读取。
    BASE_URL = settings.deepseek_base_url
    # 本项目使用的模型名称，实际调用时仍以 settings 为准。
    MODEL_NAME = settings.deepseek_model

    @staticmethod
    def _get_client() -> OpenAI:
        """创建 DeepSeek 客户端：统一从 settings 读取 API Key 与服务地址。"""
        api_key = settings.deepseek_api_key.strip()
        if not api_key:
            raise ValueError('未配置 DEEPSEEK_API_KEY 环境变量')
        return OpenAI(api_key=api_key, base_url=settings.deepseek_base_url)

    @staticmethod
    def _extract_text(content: Any) -> str:
        """从 SDK 返回内容中提取文本，兼容字符串或分段结构。"""
        return LLMResponseParser.extract_content_text(content)

    @staticmethod
    def parse_json(content: str) -> dict[str, Any]:
        """解析模型返回 JSON：兼容 ```json 包裹格式。"""
        raw = (content or '').strip()
        if raw.startswith('```'):
            lines = raw.splitlines()
            if lines and lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            raw = '\n'.join(lines).strip()

        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('AI 返回结果不是 JSON 对象')
        return data

    @staticmethod
    def chat_json(
        user_prompt: str,
        module: str | None = None,
        task_type: str | None = None,
        prompt_template_key: str | None = None,
        prompt_version: str | None = None
    ) -> dict[str, Any]:
        """调用 DeepSeek 对话接口并返回 JSON 对象。"""
        start_time = time.perf_counter()
        content: str | None = None
        response: Any | None = None
        try:
            client = DeepSeekService._get_client()
            response = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {'role': 'system', 'content': DeepSeekService.SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.3
            )

            # 统一解析 SDK 响应，能区分 choices/message/content 为空等具体问题。
            extract_result = LLMResponseParser.extract_text(response)
            content = extract_result.text
            data = DeepSeekService.parse_json(content)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            # 成功日志记录解析后的 JSON 字符串，便于后续检索和排查结构化结果。
            AiCallLogService.write_log(
                module=module,
                task_type=task_type,
                prompt=user_prompt,
                response=json.dumps(data, ensure_ascii=False),
                status='success',
                error_message=None,
                model_name=settings.deepseek_model,
                latency_ms=latency_ms,
                prompt_template_key=prompt_template_key,
                prompt_version=prompt_version
            )
            return data
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            # 失败日志优先记录安全响应摘要，便于排查 deepseek-v4-flash 等模型的返回结构差异。
            failed_response = LLMResponseParser.build_safe_summary_text(response) or content
            # 失败日志记录异常信息并继续抛出原异常，保证调用方现有错误处理不变。
            AiCallLogService.write_log(
                module=module,
                task_type=task_type,
                prompt=user_prompt,
                response=failed_response,
                status='failed',
                error_message=str(exc),
                model_name=settings.deepseek_model,
                latency_ms=latency_ms,
                prompt_template_key=prompt_template_key,
                prompt_version=prompt_version
            )
            raise
