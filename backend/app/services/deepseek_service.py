"""DeepSeek 服务文件：封装基于 OpenAI SDK 兼容协议的 DeepSeek 调用逻辑。"""

import json
import os
from typing import Any

from openai import OpenAI


class DeepSeekService:
    """DeepSeek 调用服务：统一处理提示词、模型调用与 JSON 解析。"""

    # 系统提示词：约束模型只返回 JSON，避免输出额外说明文本。
    SYSTEM_PROMPT = (
        '你是一名销售管理助手，请根据客户资料和历史跟进记录进行分析，'
        '不要输出系统内部枚举值（如 normal、intention、key 等），必须使用中文业务表达，如普通客户、意向客户、重点客户，'
        '并严格按照指定 JSON 格式返回结果，不要输出多余文本。'
    )

    # DeepSeek 兼容 OpenAI 接口的基础地址。
    BASE_URL = 'https://api.deepseek.com'
    # 本项目使用的模型名称。
    MODEL_NAME = 'deepseek-chat'

    @staticmethod
    def _get_client() -> OpenAI:
        """创建 DeepSeek 客户端：从环境变量读取 API Key。"""
        api_key = os.getenv('DEEPSEEK_API_KEY', '').strip()
        if not api_key:
            raise ValueError('未配置 DEEPSEEK_API_KEY 环境变量')
        return OpenAI(api_key=api_key, base_url=DeepSeekService.BASE_URL)

    @staticmethod
    def _extract_text(content: Any) -> str:
        """从 SDK 返回内容中提取文本，兼容字符串或分段结构。"""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(str(item.get('text', '')))
                else:
                    text_parts.append(str(item))
            return ''.join(text_parts)
        return str(content or '')

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
    def chat_json(user_prompt: str) -> dict[str, Any]:
        """调用 DeepSeek 对话接口并返回 JSON 对象。"""
        client = DeepSeekService._get_client()
        response = client.chat.completions.create(
            model=DeepSeekService.MODEL_NAME,
            messages=[
                {'role': 'system', 'content': DeepSeekService.SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=0.3
        )

        choices = response.choices or []
        if not choices:
            raise ValueError('AI 返回内容为空')
        message = choices[0].message
        content = DeepSeekService._extract_text(getattr(message, 'content', ''))
        if not content.strip():
            raise ValueError('AI 返回内容为空文本')
        return DeepSeekService.parse_json(content)

