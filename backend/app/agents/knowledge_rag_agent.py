"""知识检索 Agent：复用现有 RAG 服务完成检索、摘要与引用返回。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.schemas.agent import KnowledgeRAGHit, KnowledgeRAGOutput
from app.schemas.ai_chat import AIChatRequest
from app.tools.agent_query_tools import AgentQueryTools


class KnowledgeRAGAgent(BaseAgent):
    """knowledge_rag_agent 实现。"""

    name = 'knowledge_rag_agent'
    description = '检索销售 ERP 知识库，返回命中片段、摘要和引用来源。'
    supported_scenes = ['knowledge_base', 'customer_detail', 'order_detail', 'general']
    dependencies: list[str] = []

    def run(self, db: Session, request: AIChatRequest, previous_outputs: dict[str, Any]) -> dict[str, Any]:
        """执行知识检索并输出结构化结果。"""
        _ = db
        _ = previous_outputs

        query = (request.user_message or '').strip()
        if not query:
            output = KnowledgeRAGOutput(
                query='',
                hits=[],
                summary='问题为空，无法执行知识检索。',
                references=[]
            ).model_dump()
            return self.attach_execution_meta(
                output,
                status='skipped',
                confidence=0.0,
                next_recommendation='请补充明确问题后重新检索知识库。',
                message='用户问题为空，已跳过知识检索。'
            )

        # 从上下文读取 top_k，默认 4；保底限制在 1~8。
        raw_top_k = int(request.context.get('top_k') or 4)
        top_k = min(max(raw_top_k, 1), 8)

        payload = AgentQueryTools.get_knowledge_rag_payload(question=query, top_k=top_k)
        normalized = self._normalize(payload)
        output = normalized.model_dump()
        hit_count = len(output.get('hits', [])) if isinstance(output.get('hits'), list) else 0
        if hit_count <= 0:
            return self.attach_execution_meta(
                output,
                status='partial_failed',
                confidence=0.45,
                next_recommendation='建议补充更具体的关键词后重新检索。',
                message='知识库未命中有效片段。'
            )
        return self.attach_execution_meta(
            output,
            status='success',
            confidence=0.78,
            next_recommendation='可结合知识来源完善业务分析结论。',
            message='知识检索完成。'
        )

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> KnowledgeRAGOutput:
        """标准化知识检索结果，确保字段稳定。"""
        raw_hits = payload.get('hits', [])
        hits: list[KnowledgeRAGHit] = []
        if isinstance(raw_hits, list):
            for item in raw_hits:
                if not isinstance(item, dict):
                    continue
                title = str(item.get('title', '')).strip()
                content = str(item.get('content', '')).strip()
                score = float(item.get('score') or 0.0)
                if not title and not content:
                    continue
                hits.append(KnowledgeRAGHit(title=title, content=content, score=score))

        references: list[str] = []
        raw_refs = payload.get('references', [])
        if isinstance(raw_refs, list):
            for ref in raw_refs:
                value = str(ref or '').strip()
                if value and value not in references:
                    references.append(value)

        return KnowledgeRAGOutput(
            query=str(payload.get('query', '')).strip(),
            hits=hits,
            summary=str(payload.get('summary', '')).strip(),
            references=references
        )
