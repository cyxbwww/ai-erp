"""LLM 响应解析工具：统一提取模型文本并生成安全调试摘要。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponseExtractResult:
    """LLM 响应提取结果：同时返回最终文本和安全摘要。"""

    text: str
    summary: dict[str, Any]


class LLMResponseParser:
    """LLM 响应解析器：兼容 OpenAI SDK 对象、字典和分段 content。"""

    @staticmethod
    def extract_text(response: Any) -> LLMResponseExtractResult:
        """从模型响应中提取最终文本；为空时抛出明确错误。"""
        summary = LLMResponseParser.build_safe_summary(response)
        choices = LLMResponseParser._get_choices(response)
        if not choices:
            raise ValueError('AI 返回内容为空：choices 为空')

        choice = choices[0]
        message = LLMResponseParser._get_value(choice, 'message')
        if message is None:
            raise ValueError('AI 返回内容为空：message 为空')

        content = LLMResponseParser._get_value(message, 'content')
        if content is None or content == '' or content == []:
            raise ValueError('AI 返回内容为空：message.content 为空')

        text = LLMResponseParser.extract_content_text(content)
        if not text.strip():
            raise ValueError('AI 返回内容为空：content 提取后为空')

        return LLMResponseExtractResult(text=text, summary=summary)

    @staticmethod
    def extract_content_text(content: Any) -> str:
        """提取 content 文本，兼容 str、list、dict 和 SDK 分段对象。"""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                    continue

                # 兼容 {"text": "..."} 与 {"type": "text", "text": "..."} 两种分段结构。
                text_value = LLMResponseParser._get_value(item, 'text')
                if text_value is not None:
                    text_parts.append(str(text_value))
                    continue

                # 兼容少数 SDK 分段对象把文本放在 content 字段的情况。
                nested_content = LLMResponseParser._get_value(item, 'content')
                if isinstance(nested_content, str):
                    text_parts.append(nested_content)

            return ''.join(text_parts)

        if isinstance(content, dict):
            text_value = content.get('text')
            if text_value is not None:
                return str(text_value)

        return str(content or '')

    @staticmethod
    def build_safe_summary(response: Any) -> dict[str, Any]:
        """生成安全响应摘要：只保留结构信息，不记录 API Key、headers 等敏感内容。"""
        choices = LLMResponseParser._get_choices(response)
        first_choice = choices[0] if choices else None
        message = LLMResponseParser._get_value(first_choice, 'message') if first_choice is not None else None
        content = LLMResponseParser._get_value(message, 'content') if message is not None else None
        content_text = LLMResponseParser.extract_content_text(content) if content not in (None, '', []) else ''

        # reasoning_content 只用于判断模型是否返回了推理内容，不作为最终 JSON 解析文本。
        reasoning_content = LLMResponseParser._get_value(message, 'reasoning_content') if message is not None else None

        return {
            'model': LLMResponseParser._get_value(response, 'model'),
            'choices_count': len(choices),
            'finish_reason': LLMResponseParser._get_value(first_choice, 'finish_reason') if first_choice is not None else None,
            'message_keys': LLMResponseParser._get_message_keys(message),
            'content_type': type(content).__name__ if content is not None else None,
            'content_length': len(content_text),
            'has_reasoning_content': bool(str(reasoning_content or '').strip())
        }

    @staticmethod
    def build_safe_summary_text(response: Any) -> str | None:
        """将安全摘要转换为 JSON 字符串，供 AI 调用日志失败 response 字段保存。"""
        if response is None:
            return None
        return json.dumps(LLMResponseParser.build_safe_summary(response), ensure_ascii=False)

    @staticmethod
    def _get_choices(response: Any) -> list[Any]:
        """从 SDK 对象或字典中安全读取 choices 列表。"""
        choices = LLMResponseParser._get_value(response, 'choices')
        if isinstance(choices, list):
            return choices
        if choices is None:
            return []
        try:
            return list(choices)
        except Exception:
            return []

    @staticmethod
    def _get_message_keys(message: Any) -> list[str]:
        """提取 message 可见字段名，帮助判断返回结构是否与当前解析逻辑兼容。"""
        if message is None:
            return []
        if isinstance(message, dict):
            return sorted(str(key) for key in message.keys())
        if hasattr(message, 'model_dump'):
            try:
                dumped = message.model_dump()
                if isinstance(dumped, dict):
                    return sorted(str(key) for key in dumped.keys())
            except Exception:
                pass
        keys = [key for key in ('role', 'content', 'reasoning_content', 'tool_calls') if hasattr(message, key)]
        return keys

    @staticmethod
    def _get_value(obj: Any, key: str) -> Any:
        """兼容 dict、Pydantic/SDK 对象和 model_dump 的字段读取。"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        if hasattr(obj, key):
            return getattr(obj, key)
        if hasattr(obj, 'model_dump'):
            try:
                dumped = obj.model_dump()
                if isinstance(dumped, dict):
                    return dumped.get(key)
            except Exception:
                return None
        return None
