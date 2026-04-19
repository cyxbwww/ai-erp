"""订单风险评分服务：提供确定性规则评分能力。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class OrderRiskScoringService:
    """订单风险评分服务。"""

    # 规则分值配置：便于后续按业务调整。
    UNPAID_SCORE = 30
    OVERDUE_UNSHIPPED_SCORE = 25
    HIGH_AMOUNT_SCORE = 15
    CUSTOMER_COMPLAINT_SCORE = 20
    AFTERSALE_EXCEPTION_SCORE = 20
    HIGH_AMOUNT_THRESHOLD = 100000
    OVERDUE_DAYS = 7

    @staticmethod
    def score(order_detail: dict[str, Any]) -> dict[str, Any]:
        """根据订单详情进行规则打分并返回风险因子。"""
        risk_factors: list[dict[str, Any]] = []
        score = 0

        status = str(order_detail.get('status', '')).strip().lower()
        total_amount = float(order_detail.get('total_amount') or 0)
        remark = str(order_detail.get('remark', '')).strip().lower()
        created_at = str(order_detail.get('created_at', '')).strip()

        # 规则1：未付款。
        if status in {'confirmed', 'unpaid', 'pending'}:
            score += OrderRiskScoringService.UNPAID_SCORE
            risk_factors.append({'name': '未付款', 'score': OrderRiskScoringService.UNPAID_SCORE})

        # 规则2：超期未发货（兼容版）。
        # TODO: 后续接入真实履约/发货表后，替换为发货状态和承诺发货时间判断。
        if OrderRiskScoringService._is_overdue(created_at, days=OrderRiskScoringService.OVERDUE_DAYS) and status in {'confirmed', 'unpaid', 'pending'}:
            score += OrderRiskScoringService.OVERDUE_UNSHIPPED_SCORE
            risk_factors.append({'name': '超期未发货', 'score': OrderRiskScoringService.OVERDUE_UNSHIPPED_SCORE})

        # 规则3：高金额订单。
        if total_amount >= OrderRiskScoringService.HIGH_AMOUNT_THRESHOLD:
            score += OrderRiskScoringService.HIGH_AMOUNT_SCORE
            risk_factors.append({'name': '高金额订单', 'score': OrderRiskScoringService.HIGH_AMOUNT_SCORE})

        # 规则4：客户历史投诉（兼容版）。
        # TODO: 后续接入客户投诉表/工单表后，改为真实投诉次数和严重度统计。
        complaint_keywords = ('投诉', '不满', '争议', '客诉')
        if any(keyword in remark for keyword in complaint_keywords):
            score += OrderRiskScoringService.CUSTOMER_COMPLAINT_SCORE
            risk_factors.append({'name': '客户历史投诉', 'score': OrderRiskScoringService.CUSTOMER_COMPLAINT_SCORE})

        # 规则5：售后异常（兼容版）。
        # TODO: 后续接入售后工单/退款退货表后，改为真实售后异常率判断。
        aftersale_keywords = ('售后异常', '退货', '退款', '返修')
        if any(keyword in remark for keyword in aftersale_keywords):
            score += OrderRiskScoringService.AFTERSALE_EXCEPTION_SCORE
            risk_factors.append({'name': '售后异常', 'score': OrderRiskScoringService.AFTERSALE_EXCEPTION_SCORE})

        risk_level = OrderRiskScoringService._risk_level(score)
        need_manual_intervention = risk_level in {'medium', 'high'}
        return {
            'risk_score': score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'need_manual_intervention': need_manual_intervention
        }

    @staticmethod
    def _risk_level(score: int) -> str:
        """根据分数映射风险等级。"""
        if score >= 70:
            return 'high'
        if score >= 30:
            return 'medium'
        return 'low'

    @staticmethod
    def _is_overdue(created_at_text: str, days: int) -> bool:
        """判断订单是否超过指定天数。"""
        if not created_at_text:
            return False
        try:
            created_at = datetime.strptime(created_at_text, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False
        return datetime.now() - created_at > timedelta(days=days)
