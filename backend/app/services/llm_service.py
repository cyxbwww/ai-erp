"""LLM 服务文件：统一封装 DeepSeek 文本与 JSON 调用能力。"""

from __future__ import annotations

import copy
import json
import re
from typing import Any

from openai import OpenAI

from app.core.config import settings


class LLMService:
    """统一 LLM 服务：提供 chat_text 与 chat_json。"""

    @staticmethod
    def _get_client() -> OpenAI:
        """创建 DeepSeek 客户端。"""
        if not settings.deepseek_api_key.strip():
            raise ValueError('未配置 DEEPSEEK_API_KEY')
        return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

    @staticmethod
    def _extract_message_text(response: Any) -> str:
        """从 OpenAI SDK 响应中提取文本内容。"""
        choices = getattr(response, 'choices', []) or []
        if not choices:
            return ''
        message = getattr(choices[0], 'message', None)
        if not message:
            return ''
        content = getattr(message, 'content', '')
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
    def chat_text(
        system_prompt: str,
        user_prompt: str,
        fallback_text: str = '',
        temperature: float = 0.2
    ) -> str:
        """调用 LLM 返回文本，失败时返回 fallback_text。"""
        try:
            client = LLMService._get_client()
            response = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=temperature
            )
            text = LLMService._extract_message_text(response).strip()
            return text or fallback_text
        except Exception:
            return fallback_text

    @staticmethod
    def chat_json(
        system_prompt: str,
        user_prompt: str,
        fallback_data: dict[str, Any],
        temperature: float = 0.2
    ) -> dict[str, Any]:
        """调用 LLM 返回 JSON，解析失败或调用失败时返回 fallback_data。"""
        fallback = copy.deepcopy(fallback_data)
        try:
            raw = LLMService.chat_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                fallback_text='',
                temperature=temperature
            )
            if not raw:
                return fallback
            parsed = LLMService._extract_json_object(raw)
            if not isinstance(parsed, dict):
                return fallback
            return parsed
        except Exception:
            return fallback

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        """从多种文本形态中提取 JSON 对象。"""
        candidates: list[str] = []
        raw = (text or '').strip()
        if not raw:
            raise ValueError('空文本')

        # 1) 原样尝试。
        candidates.append(raw)

        # 2) markdown 代码块：```json ... ``` 和 ``` ... ```。
        fenced_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', raw, flags=re.IGNORECASE)
        candidates.extend([block.strip() for block in fenced_blocks if block.strip()])

        # 3) 文本夹杂 JSON：提取首个平衡花括号对象。
        balanced = LLMService._find_balanced_json_objects(raw)
        candidates.extend(balanced)

        # 逐个尝试解析，取第一个 dict。
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                continue

        raise ValueError('未提取到有效 JSON 对象')

    @staticmethod
    def _find_balanced_json_objects(text: str) -> list[str]:
        """扫描文本中的平衡 JSON 对象片段。"""
        results: list[str] = []
        start = -1
        depth = 0
        in_string = False
        escaped = False

        for idx, ch in enumerate(text):
            if ch == '"' and not escaped:
                in_string = not in_string
            if ch == '\\' and not escaped:
                escaped = True
                continue
            escaped = False

            if in_string:
                continue

            if ch == '{':
                if depth == 0:
                    start = idx
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start >= 0:
                        results.append(text[start:idx + 1].strip())
                        start = -1

        return results

