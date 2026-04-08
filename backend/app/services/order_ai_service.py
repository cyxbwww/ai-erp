"""订单 AI 服务文件：封装订单 AI 分析、风险检测与销售建议能力。"""

from typing import Any

from sqlalchemy.orm import Session

from app.core.order_status import get_order_status_label, replace_order_status_enums
from app.services.deepseek_service import DeepSeekService
from app.services.order_service import OrderService


class OrderAIService:
    """订单 AI 业务服务：基于订单详情调用 DeepSeek，失败时回退规则分析。"""

    ANALYSIS_TYPE_TITLE = {
        'analysis': 'AI 分析订单',
        'risk': 'AI 风险检测',
        'advice': 'AI 销售建议'
    }

    @staticmethod
    def analyze_order(db: Session, order_id: int, analysis_type: str) -> dict[str, Any]:
        """执行订单 AI 分析：支持 analysis/risk/advice 三种类型。"""
        detail = OrderService.get_order_detail(db, order_id)
        if not detail:
            raise ValueError('订单不存在')

        analysis_type = (analysis_type or 'analysis').strip().lower()
        if analysis_type not in OrderAIService.ANALYSIS_TYPE_TITLE:
            raise ValueError('分析类型不合法')

        try:
            prompt = OrderAIService._build_prompt(detail, analysis_type)
            data = DeepSeekService.chat_json(prompt)
            result = OrderAIService._normalize_ai_result(data, analysis_type)
            result['ai_source'] = 'deepseek'
            return result
        except Exception:
            result = OrderAIService._fallback_result(detail, analysis_type)
            result['ai_source'] = 'fallback'
            return result

    @staticmethod
    def _build_prompt(detail: dict[str, Any], analysis_type: str) -> str:
        """构建订单 AI 提示词，要求严格返回 JSON 且仅使用中文状态描述。"""
        analysis_title = OrderAIService.ANALYSIS_TYPE_TITLE[analysis_type]
        localized_detail = {
            **detail,
            # 向模型提供中文状态，降低模型输出英文枚举值概率。
            'status': get_order_status_label(str(detail.get('status') or ''))
        }
        return (
            f'请基于订单数据生成“{analysis_title}”。\n'
            '你必须严格返回 JSON 对象，不要输出额外说明文字。\n'
            '你必须使用中文业务表达，严禁输出任何英文状态枚举值。\n'
            '订单状态请仅使用以下中文语义：待确认、待付款、已付款、已完成、已取消。\n'
            '若输入中存在 pending/unpaid/paid/completed/cancelled，也必须转换为对应中文。\n'
            'JSON 结构如下：\n'
            '{\n'
            '  "title": "string",\n'
            '  "summary": "string",\n'
            '  "highlights": ["string"],\n'
            '  "risks": ["string"],\n'
            '  "suggestions": ["string"]\n'
            '}\n'
            f'订单数据：{localized_detail}'
        )

    @staticmethod
    def _normalize_ai_result(data: dict[str, Any], analysis_type: str) -> dict[str, Any]:
        """标准化 AI 返回结构，并兜底替换所有英文状态枚举。"""
        return {
            'analysis_type': analysis_type,
            'title': replace_order_status_enums(
                str(data.get('title', '')).strip() or OrderAIService.ANALYSIS_TYPE_TITLE[analysis_type]
            ),
            'summary': replace_order_status_enums(str(data.get('summary', '')).strip()),
            'highlights': OrderAIService._ensure_list(data.get('highlights')),
            'risks': OrderAIService._ensure_list(data.get('risks')),
            'suggestions': OrderAIService._ensure_list(data.get('suggestions'))
        }

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        """统一将结果字段转为字符串数组，并替换英文状态枚举。"""
        if isinstance(value, list):
            normalized_list = [str(item).strip() for item in value if str(item).strip()]
            return [replace_order_status_enums(item) for item in normalized_list]
        if isinstance(value, str) and value.strip():
            return [replace_order_status_enums(value.strip())]
        return []

    @staticmethod
    def _fallback_result(detail: dict[str, Any], analysis_type: str) -> dict[str, Any]:
        """DeepSeek 异常时的规则回退结果。"""
        total_amount = float(detail.get('total_amount') or 0)
        status = str(detail.get('status') or '')
        status_label = get_order_status_label(status)
        items = detail.get('items') or []
        item_count = len(items)

        summary = f'当前订单金额为 ¥{total_amount:.2f}，包含 {item_count} 条商品明细，状态为 {status_label}。'
        highlights = [
            f'订单编号：{detail.get("order_no", "-")}',
            f'客户名称：{detail.get("customer_name", "-")}',
            f'订单状态：{status_label}'
        ]

        risks: list[str] = []
        if status in {'draft', 'pending'}:
            risks.append('订单仍处于待确认阶段，可能影响成交节奏。')
        if status in {'confirmed', 'unpaid'}:
            risks.append('订单处于待付款阶段，需关注回款风险。')
        if total_amount >= 100000:
            risks.append('订单金额较高，建议重点关注审批与回款风险。')
        if item_count == 0:
            risks.append('订单无明细数据，需确认是否为异常单据。')
        if not risks:
            risks.append('当前未识别到明显高风险信号。')

        suggestions = [
            '建议与客户确认最终采购清单与签约时间。',
            '建议同步跟踪付款节点与交付计划。'
        ]

        if analysis_type == 'risk':
            suggestions = ['建议优先完成订单确认，降低销售机会流失风险。', '建议检查库存和交付资源，提前识别履约阻塞点。']
        elif analysis_type == 'advice':
            suggestions = ['建议结合客户历史订单进行交叉销售推荐。', '建议在报价沟通中突出高价值商品组合。']

        return {
            'analysis_type': analysis_type,
            'title': OrderAIService.ANALYSIS_TYPE_TITLE[analysis_type],
            'summary': summary,
            'highlights': highlights,
            'risks': risks,
            'suggestions': suggestions
        }
