"""订单状态工具文件：统一维护订单状态中英文映射与文本替换逻辑。"""

from __future__ import annotations

import re

# 订单状态中文映射：覆盖标准状态与历史兼容状态。
ORDER_STATUS_LABEL_MAP: dict[str, str] = {
    'pending': '待确认',
    'unpaid': '待付款',
    'paid': '已付款',
    'completed': '已完成',
    'cancelled': '已取消',
    # 兼容历史状态值，避免老数据在 AI 输出中出现英文。
    'draft': '待确认',
    'confirmed': '待付款'
}

# 预编译状态替换正则，按长度倒序，避免短词误匹配。
_ORDER_STATUS_PATTERN = re.compile(
    r'\\b(' + '|'.join(sorted((re.escape(key) for key in ORDER_STATUS_LABEL_MAP.keys()), key=len, reverse=True)) + r')\\b',
    flags=re.IGNORECASE
)


def get_order_status_label(status: str) -> str:
    """将订单状态英文值转换为中文业务语义。"""
    normalized = (status or '').strip().lower()
    if not normalized:
        return '未知状态'
    return ORDER_STATUS_LABEL_MAP.get(normalized, '未知状态')


def replace_order_status_enums(text: str) -> str:
    """将文本中的订单状态英文枚举值替换为中文，防止界面出现英文状态。"""
    if not text:
        return ''

    def _replace(match: re.Match[str]) -> str:
        matched = match.group(1).lower()
        return ORDER_STATUS_LABEL_MAP.get(matched, match.group(1))

    return _ORDER_STATUS_PATTERN.sub(_replace, text)
