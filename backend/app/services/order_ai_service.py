"""订单 AI 服务文件：封装订单 AI 分析、风险检测与销售建议能力。"""

from typing import Any

from sqlalchemy.orm import Session

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
        """构建订单 AI 提示词，要求严格返回 JSON。"""
        analysis_title = OrderAIService.ANALYSIS_TYPE_TITLE[analysis_type]
        return (
            f'请基于订单数据生成“{analysis_title}”。\n'
            '你必须严格返回 JSON 对象，不要输出额外说明文字。\n'
            'JSON 结构如下：\n'
            '{\n'
            '  "title": "string",\n'
            '  "summary": "string",\n'
            '  "highlights": ["string"],\n'
            '  "risks": ["string"],\n'
            '  "suggestions": ["string"]\n'
            '}\n'
            f'订单数据：{detail}'
        )

    @staticmethod
    def _normalize_ai_result(data: dict[str, Any], analysis_type: str) -> dict[str, Any]:
        """标准化 AI 返回结构，确保前端可稳定渲染。"""
        return {
            'analysis_type': analysis_type,
            'title': str(data.get('title', '')).strip() or OrderAIService.ANALYSIS_TYPE_TITLE[analysis_type],
            'summary': str(data.get('summary', '')).strip(),
            'highlights': OrderAIService._ensure_list(data.get('highlights')),
            'risks': OrderAIService._ensure_list(data.get('risks')),
            'suggestions': OrderAIService._ensure_list(data.get('suggestions'))
        }

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        """统一将结果字段转为字符串数组。"""
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _fallback_result(detail: dict[str, Any], analysis_type: str) -> dict[str, Any]:
        """DeepSeek 异常时的规则回退结果。"""
        total_amount = float(detail.get('total_amount') or 0)
        status = str(detail.get('status') or '')
        items = detail.get('items') or []
        item_count = len(items)

        summary = f'当前订单金额为 ¥{total_amount:.2f}，包含 {item_count} 条商品明细，状态为 {status}。'
        highlights = [
            f'订单编号：{detail.get("order_no", "-")}',
            f'客户名称：{detail.get("customer_name", "-")}',
            f'订单状态：{status}'
        ]

        risks: list[str] = []
        if status == 'draft':
            risks.append('订单仍处于草稿状态，可能影响成交节奏。')
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

