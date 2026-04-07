"""客户 AI 服务文件：整合规则引擎与 DeepSeek，提供跟进建议与跟进总结能力。"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_follow_record import CustomerFollowRecord
from app.services.deepseek_service import DeepSeekService


class CustomerAIService:
    """客户 AI 业务服务：负责组装客户上下文、调用 AI、并在失败时回退规则逻辑。"""

    @staticmethod
    def generate_follow_advice(db: Session, customer_id: int) -> dict[str, Any]:
        """生成 AI 跟进建议：优先调用 DeepSeek，失败则回退规则逻辑。"""
        customer = CustomerAIService._get_customer_or_raise(db, customer_id)
        records = CustomerAIService._get_recent_records(db, customer_id, limit=10)

        context = CustomerAIService._build_context(customer, records)
        try:
            prompt = CustomerAIService._build_advice_prompt(context)
            ai_data = DeepSeekService.chat_json(prompt)
            # 记录日志：用于确认已成功调用 DeepSeek。
            print(f'[AI][DeepSeek] 客户{customer_id} 跟进建议调用成功')
            result = CustomerAIService._normalize_advice(ai_data)
            # 返回来源标记：便于前端和调试确认当前结果来源。
            result['ai_source'] = 'deepseek'
            return result
        except Exception as exc:
            # 记录日志：当 DeepSeek 异常时明确提示已触发 fallback。
            print(f'[AI][DeepSeek] 客户{customer_id} 跟进建议调用失败，已使用fallback：{exc}')
            result = CustomerAIService._fallback_follow_advice(customer, records)
            result['ai_source'] = 'fallback'
            return result

    @staticmethod
    def generate_follow_summary(db: Session, customer_id: int) -> dict[str, Any]:
        """生成 AI 跟进总结：优先调用 DeepSeek，失败则回退规则逻辑。"""
        customer = CustomerAIService._get_customer_or_raise(db, customer_id)
        records = CustomerAIService._get_recent_records(db, customer_id, limit=10)

        context = CustomerAIService._build_context(customer, records)
        try:
            prompt = CustomerAIService._build_summary_prompt(context)
            ai_data = DeepSeekService.chat_json(prompt)
            # 记录日志：用于确认已成功调用 DeepSeek。
            print(f'[AI][DeepSeek] 客户{customer_id} 跟进总结调用成功')
            result = CustomerAIService._normalize_summary(ai_data)
            # 返回来源标记：便于前端和调试确认当前结果来源。
            result['ai_source'] = 'deepseek'
            return result
        except Exception as exc:
            # 记录日志：当 DeepSeek 异常时明确提示已触发 fallback。
            print(f'[AI][DeepSeek] 客户{customer_id} 跟进总结调用失败，已使用fallback：{exc}')
            result = CustomerAIService._fallback_follow_summary(customer, records)
            result['ai_source'] = 'fallback'
            return result

    @staticmethod
    def _get_customer_or_raise(db: Session, customer_id: int) -> Customer:
        """查询客户信息，不存在则抛出业务异常。"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError('客户不存在')
        return customer

    @staticmethod
    def _get_recent_records(db: Session, customer_id: int, limit: int = 10) -> list[CustomerFollowRecord]:
        """查询最近跟进记录，按创建时间倒序。"""
        return (
            db.query(CustomerFollowRecord)
            .filter(CustomerFollowRecord.customer_id == customer_id)
            .order_by(desc(CustomerFollowRecord.created_at), desc(CustomerFollowRecord.id))
            .limit(limit)
            .all()
        )

    @staticmethod
    def _build_context(customer: Customer, records: list[CustomerFollowRecord]) -> dict[str, Any]:
        """组装客户上下文：客户信息 + 历史跟进记录。"""
        latest_follow_time = ''
        if records and records[0].created_at:
            latest_follow_time = records[0].created_at.strftime('%Y-%m-%d %H:%M:%S')

        record_items: list[dict[str, str]] = []
        for record in records:
            record_items.append(
                {
                    '跟进时间': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '',
                    '跟进类型': record.follow_type or '',
                    '跟进内容': record.content or '',
                    '跟进结果': record.result or '',
                    '下次跟进时间': record.next_follow_time.strftime('%Y-%m-%d %H:%M:%S') if record.next_follow_time else ''
                }
            )

        return {
            '客户基本信息': {
                '客户名称': customer.name or '',
                '联系人': customer.contact_name or '',
                '手机号': customer.phone or '',
                '邮箱': customer.email or '',
                '公司': customer.company or '',
                '负责人': customer.owner_name or ''
            },
            '客户等级': customer.level or '',
            '客户来源': customer.source or '',
            '跟进状态': customer.status or '',
            '历史跟进记录': record_items,
            '最近跟进时间': latest_follow_time
        }

    @staticmethod
    def _build_advice_prompt(context: dict[str, Any]) -> str:
        """构建 AI 跟进建议提示词，要求严格返回指定 JSON。"""
        return (
            '请基于以下客户信息，输出客户跟进建议。\n'
            '你必须严格返回 JSON 对象，不要输出任何解释文字。\n'
            'JSON 结构如下：\n'
            '{\n'
            '  "intent_level": {\n'
            '    "code": "high|medium|low",\n'
            '    "label": "高意向|中意向|低意向"\n'
            '  },\n'
            '  "current_focus": "string",\n'
            '  "next_step_advice": ["string"],\n'
            '  "recommended_talk_track": "string",\n'
            '  "suggested_next_follow_time": "string"\n'
            '}\n'
            f'客户上下文：{context}'
        )

    @staticmethod
    def _build_summary_prompt(context: dict[str, Any]) -> str:
        """构建 AI 跟进总结提示词，要求严格返回指定 JSON。"""
        return (
            '请基于以下客户信息，输出客户历史跟进总结。\n'
            '你必须严格返回 JSON 对象，不要输出任何解释文字。\n'
            'JSON 结构如下：\n'
            '{\n'
            '  "current_progress": "string",\n'
            '  "history_key_points": ["string"],\n'
            '  "potential_risks": ["string"]\n'
            '}\n'
            f'客户上下文：{context}'
        )

    @staticmethod
    def _normalize_intent_level(intent: Any) -> dict[str, str]:
        """标准化意向等级，保证 code 与 label 在允许值范围内。"""
        code_to_label = {'high': '高意向', 'medium': '中意向', 'low': '低意向'}
        label_to_code = {'高意向': 'high', '中意向': 'medium', '低意向': 'low'}

        if isinstance(intent, dict):
            raw_code = str(intent.get('code', '')).strip().lower()
            raw_label = str(intent.get('label', '')).strip()
            if raw_code in code_to_label:
                return {'code': raw_code, 'label': code_to_label[raw_code]}
            if raw_label in label_to_code:
                code = label_to_code[raw_label]
                return {'code': code, 'label': code_to_label[code]}

        return {'code': 'medium', 'label': '中意向'}

    @staticmethod
    def _ensure_str_list(value: Any) -> list[str]:
        """标准化列表字段，确保返回字符串数组。"""
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            return items
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _normalize_advice(data: dict[str, Any]) -> dict[str, Any]:
        """标准化跟进建议结果，保证字段齐全且类型正确。"""
        return {
            'intent_level': CustomerAIService._normalize_intent_level(data.get('intent_level')),
            'current_focus': str(data.get('current_focus', '')).strip(),
            'next_step_advice': CustomerAIService._ensure_str_list(data.get('next_step_advice')),
            'recommended_talk_track': str(data.get('recommended_talk_track', '')).strip(),
            'suggested_next_follow_time': str(data.get('suggested_next_follow_time', '')).strip()
        }

    @staticmethod
    def _normalize_summary(data: dict[str, Any]) -> dict[str, Any]:
        """标准化跟进总结结果，保证字段齐全且类型正确。"""
        return {
            'current_progress': str(data.get('current_progress', '')).strip(),
            'history_key_points': CustomerAIService._ensure_str_list(data.get('history_key_points')),
            'potential_risks': CustomerAIService._ensure_str_list(data.get('potential_risks'))
        }

    @staticmethod
    def _fallback_follow_advice(customer: Customer, records: list[CustomerFollowRecord]) -> dict[str, Any]:
        """DeepSeek 失败回退：使用规则逻辑生成跟进建议。"""
        intent_level = CustomerAIService._rule_intent_level(customer, records)
        current_focus = CustomerAIService._rule_current_focus(customer, records)
        next_step_advice = CustomerAIService._rule_next_step_advice(customer, intent_level['code'])
        talk_track = CustomerAIService._rule_talk_track(customer, current_focus, intent_level['label'])
        suggested_time = CustomerAIService._rule_suggest_next_follow_time(intent_level['code'])

        return {
            'intent_level': intent_level,
            'current_focus': current_focus,
            'next_step_advice': next_step_advice,
            'recommended_talk_track': talk_track,
            'suggested_next_follow_time': suggested_time
        }

    @staticmethod
    def _fallback_follow_summary(customer: Customer, records: list[CustomerFollowRecord]) -> dict[str, Any]:
        """DeepSeek 失败回退：使用规则逻辑生成跟进总结。"""
        return {
            'current_progress': CustomerAIService._rule_current_progress(customer, records),
            'history_key_points': CustomerAIService._rule_history_key_points(records),
            'potential_risks': CustomerAIService._rule_potential_risks(customer, records)
        }

    @staticmethod
    def _rule_intent_level(customer: Customer, records: list[CustomerFollowRecord]) -> dict[str, str]:
        """规则判断客户意向等级。"""
        code_to_label = {'high': '高意向', 'medium': '中意向', 'low': '低意向'}
        if customer.status == 'closed':
            return {'code': 'high', 'label': code_to_label['high']}
        if customer.status == 'lost':
            return {'code': 'low', 'label': code_to_label['low']}

        score = 0
        if customer.level == 'strategic':
            score += 3
        elif customer.level == 'vip':
            score += 2
        else:
            score += 1

        positive_keywords = ['报价', '合同', '预算', '采购', '方案', '演示', '试用']
        negative_keywords = ['延期', '观望', '暂无预算', '竞品', '搁置', '无需求']

        for record in records:
            text = f'{record.content or ""} {record.result or ""}'.lower()
            score += sum(1 for key in positive_keywords if key in text)
            score -= sum(1 for key in negative_keywords if key in text)

        if score >= 5:
            code = 'high'
        elif score >= 2:
            code = 'medium'
        else:
            code = 'low'
        return {'code': code, 'label': code_to_label[code]}

    @staticmethod
    def _rule_current_focus(customer: Customer, records: list[CustomerFollowRecord]) -> str:
        """规则推断客户当前关注点。"""
        if records:
            latest = records[0]
            latest_text = f'{latest.content or ""} {latest.result or ""}'
            if any(key in latest_text for key in ['价格', '报价', '预算', '成本']):
                return '价格与预算匹配'
            if any(key in latest_text for key in ['功能', '需求', '场景', '流程']):
                return '功能匹配与业务场景落地'
            if any(key in latest_text for key in ['上线', '周期', '交付', '实施']):
                return '实施周期与上线计划'
            if any(key in latest_text for key in ['合同', '法务', '采购', '审批']):
                return '采购流程与合同推进'
        if customer.source == 'campaign':
            return '活动线索质量与需求明确度'
        if customer.source == 'import':
            return '客户真实性与需求激活'
        return '业务痛点确认与方案价值匹配'

    @staticmethod
    def _rule_next_step_advice(customer: Customer, intent_code: str) -> list[str]:
        """规则生成下一步跟进建议。"""
        if intent_code == 'high':
            return [
                '尽快推进报价确认与采购流程。',
                '安排决策人参与的方案评审会。',
                '明确合同条款与预计签约时间。'
            ]
        if intent_code == 'medium':
            return [
                '围绕核心痛点安排一次针对性演示。',
                '补充 ROI 数据与行业案例增强信任。',
                '确认预算窗口与关键决策链路。'
            ]
        if customer.status == 'lost':
            return [
                '先复盘流失原因并记录阻塞点。',
                '2-4 周后以低打扰方式重新激活。',
                '准备更轻量的试用方案降低决策门槛。'
            ]
        return [
            '补充需求访谈，明确优先级与上线目标。',
            '确认决策人、预算区间与采购流程。',
            '按周建立固定跟进节奏。'
        ]

    @staticmethod
    def _rule_talk_track(customer: Customer, current_focus: str, intent_label: str) -> str:
        """规则生成推荐沟通话术。"""
        target = customer.company or customer.name or '贵司'
        return (
            f'基于您当前关注的“{current_focus}”，我们建议先对齐本期目标。'
            f'结合{target}的业务场景，我们可在一周内提供可落地方案与阶段收益评估。'
            f'当前判断为“{intent_label}”，建议本次重点确认决策人、预算与实施里程碑。'
        )

    @staticmethod
    def _rule_suggest_next_follow_time(intent_code: str) -> str:
        """规则推荐下次跟进时间。"""
        now = datetime.now()
        if intent_code == 'high':
            next_time = now + timedelta(days=1)
        elif intent_code == 'medium':
            next_time = now + timedelta(days=3)
        else:
            next_time = now + timedelta(days=7)
        return next_time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _rule_current_progress(customer: Customer, records: list[CustomerFollowRecord]) -> str:
        """规则总结客户当前进展。"""
        if customer.status == 'closed':
            return '客户已成交，建议转入交付与续费经营阶段。'
        if customer.status == 'lost':
            return '客户当前处于流失状态，建议进入低频激活与线索再培育。'
        if not records:
            return '当前仅有基础档案信息，尚未形成有效跟进闭环。'
        return f'已累计跟进 {len(records)} 次，当前处于持续推进阶段。'

    @staticmethod
    def _rule_history_key_points(records: list[CustomerFollowRecord]) -> list[str]:
        """规则提炼历史沟通重点。"""
        if not records:
            return ['暂无历史跟进记录。']
        points: list[str] = []
        for record in records[:3]:
            follow_date = record.created_at.strftime('%Y-%m-%d') if record.created_at else '未知日期'
            content = (record.content or '').strip()[:60] or '无内容'
            points.append(f'[{follow_date}] {content}')
        return points

    @staticmethod
    def _rule_potential_risks(customer: Customer, records: list[CustomerFollowRecord]) -> list[str]:
        """规则识别潜在风险。"""
        risks: list[str] = []
        if customer.status == 'active' and not records:
            risks.append('尚未建立有效沟通记录，需求真实性不充分。')

        negative_keywords = ['延期', '暂无预算', '竞品', '搁置', '不急']
        latest_text = ' '.join([f'{record.content or ""} {record.result or ""}' for record in records[:5]])
        if any(key in latest_text for key in negative_keywords):
            risks.append('最近沟通出现预算或优先级下滑信号。')

        if customer.source == 'import':
            risks.append('外部导入线索转化不确定性较高，需加强资格判定。')

        if not risks:
            risks.append('暂无明显高风险信号，建议按计划持续推进。')
        return risks
