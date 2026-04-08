"""知识库服务：提供文档加载、切分、向量检索与基于检索结果的回答生成。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from app.services.deepseek_service import DeepSeekService

try:
    import faiss  # type: ignore

    HAS_FAISS = True
except Exception:
    faiss = None
    HAS_FAISS = False

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    HAS_LANGCHAIN_SPLITTER = True
except Exception:
    RecursiveCharacterTextSplitter = None
    HAS_LANGCHAIN_SPLITTER = False


class KnowledgeRAGService:
    """知识库 RAG 服务：读取->切分->向量化->检索->生成。"""

    # 固定知识库目录：当前仅支持 .md / .txt。
    KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / 'knowledge_base'
    SUPPORTED_SUFFIXES = {'.md', '.txt'}

    # 运行时缓存：减少每次问答都重建索引的开销。
    _vectorizer: HashingVectorizer | None = None
    _index: Any = None
    _vectors: np.ndarray | None = None
    _chunks: list[dict[str, Any]] = []
    _documents: list[dict[str, Any]] = []
    _index_backend: str = 'none'

    @staticmethod
    def _unique_keep_order(items: list[str]) -> list[str]:
        """来源去重：保持原有顺序，去除空值与重复项。"""
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            value = str(item or '').strip()
            if not value or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _ensure_vectorizer() -> HashingVectorizer:
        """初始化向量器：使用字符 ngram 以兼容中文语料。"""
        if KnowledgeRAGService._vectorizer is None:
            KnowledgeRAGService._vectorizer = HashingVectorizer(
                n_features=1024,
                alternate_sign=False,
                norm=None,
                analyzer='char',
                ngram_range=(1, 2)
            )
        return KnowledgeRAGService._vectorizer

    @staticmethod
    def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
        """L2 归一化向量，便于内积近似余弦相似度。"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return (vectors / norms).astype(np.float32)

    @staticmethod
    def _embed_texts(texts: list[str]) -> np.ndarray:
        """文本向量化：输出 float32 稠密向量。"""
        vectorizer = KnowledgeRAGService._ensure_vectorizer()
        matrix = vectorizer.transform(texts)
        dense = matrix.toarray().astype(np.float32)
        return KnowledgeRAGService._normalize_vectors(dense)

    @staticmethod
    def _load_documents() -> list[dict[str, Any]]:
        """读取知识库目录文档并返回基础元数据。"""
        root = KnowledgeRAGService.KNOWLEDGE_DIR
        root.mkdir(parents=True, exist_ok=True)

        docs: list[dict[str, Any]] = []
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in KnowledgeRAGService.SUPPORTED_SUFFIXES:
                continue
            text = path.read_text(encoding='utf-8', errors='ignore').strip()
            if not text:
                continue
            stat = path.stat()
            docs.append(
                {
                    'source': str(path.relative_to(root)).replace('\\', '/'),
                    'content': text,
                    'size': stat.st_size,
                    'updated_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        return docs

    @staticmethod
    def _split_text(content: str) -> list[str]:
        """文档切分：优先使用 LangChain；缺失时回退固定窗口切分。"""
        # 适度减小片段长度，避免命中片段过长导致“依据说明”与原文高度重复。
        chunk_size = 360
        overlap = 60

        if HAS_LANGCHAIN_SPLITTER and RecursiveCharacterTextSplitter is not None:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=['\n\n', '\n', '。', '！', '？', '.', ' ']
            )
            chunks = [item.strip() for item in splitter.split_text(content) if item.strip()]
            if chunks:
                return chunks

        step = max(chunk_size - overlap, 1)
        chunks: list[str] = []
        for i in range(0, len(content), step):
            piece = content[i:i + chunk_size].strip()
            if piece:
                chunks.append(piece)
        return chunks

    @staticmethod
    def _truncate_text(text: str, max_len: int) -> str:
        """文本截断：用于控制依据说明长度，避免复述整段原文。"""
        normalized = (text or '').replace('\n', ' ').strip()
        if len(normalized) <= max_len:
            return normalized
        return f'{normalized[:max_len].rstrip()}...'

    @staticmethod
    def _sanitize_basis(basis: list[str], chunks: list[dict[str, Any]]) -> list[str]:
        """依据说明清洗：保留摘要，过滤大段原文和重复内容。"""
        if not isinstance(basis, list):
            return []

        chunk_prefixes: list[str] = []
        for item in chunks:
            content = str(item.get('content', '')).replace('\n', ' ').strip()
            if content:
                chunk_prefixes.append(content[:80])

        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in basis:
            text = str(raw or '').replace('\n', ' ').strip()
            if not text:
                continue

            # 过滤“明显是命中片段原文复制”的长文本。
            likely_raw_excerpt = len(text) > 140 and any(prefix and prefix in text for prefix in chunk_prefixes)
            if likely_raw_excerpt:
                continue

            normalized = KnowledgeRAGService._truncate_text(text, 120)
            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(normalized)
            if len(cleaned) >= 4:
                break

        return cleaned

    @staticmethod
    def rebuild_index() -> dict[str, Any]:
        """重建知识库索引：文档加载 -> 切分 -> 向量化 -> FAISS/NumPy 索引。"""
        docs = KnowledgeRAGService._load_documents()
        chunks: list[dict[str, Any]] = []
        for doc in docs:
            pieces = KnowledgeRAGService._split_text(doc['content'])
            for idx, piece in enumerate(pieces):
                chunks.append(
                    {
                        'source': doc['source'],
                        'chunk_id': f"{doc['source']}#{idx + 1}",
                        'content': piece
                    }
                )

        if not chunks:
            KnowledgeRAGService._documents = docs
            KnowledgeRAGService._chunks = []
            KnowledgeRAGService._vectors = None
            KnowledgeRAGService._index = None
            KnowledgeRAGService._index_backend = 'none'
            return {'document_count': len(docs), 'chunk_count': 0, 'index_backend': 'none'}

        vectors = KnowledgeRAGService._embed_texts([item['content'] for item in chunks])
        index_backend = 'numpy'
        index = None

        if HAS_FAISS and faiss is not None:
            dim = int(vectors.shape[1])
            index = faiss.IndexFlatIP(dim)
            index.add(vectors)
            index_backend = 'faiss'

        KnowledgeRAGService._documents = docs
        KnowledgeRAGService._chunks = chunks
        KnowledgeRAGService._vectors = vectors
        KnowledgeRAGService._index = index
        KnowledgeRAGService._index_backend = index_backend
        return {
            'document_count': len(docs),
            'chunk_count': len(chunks),
            'index_backend': index_backend
        }

    @staticmethod
    def _ensure_index_ready() -> None:
        """懒加载索引：首次问答时自动构建。"""
        if KnowledgeRAGService._chunks:
            return
        KnowledgeRAGService.rebuild_index()

    @staticmethod
    def list_documents() -> dict[str, Any]:
        """返回知识库文档列表。"""
        if not KnowledgeRAGService._documents:
            KnowledgeRAGService._documents = KnowledgeRAGService._load_documents()
        return {
            'total': len(KnowledgeRAGService._documents),
            'documents': [
                {
                    'source': item['source'],
                    'size': item['size'],
                    'updated_at': item['updated_at']
                }
                for item in KnowledgeRAGService._documents
            ]
        }

    @staticmethod
    def _retrieve(question: str, top_k: int) -> list[dict[str, Any]]:
        """向量检索 top-k 片段。"""
        KnowledgeRAGService._ensure_index_ready()
        if not KnowledgeRAGService._chunks or KnowledgeRAGService._vectors is None:
            return []

        query_vec = KnowledgeRAGService._embed_texts([question])
        vectors = KnowledgeRAGService._vectors
        k = min(max(top_k, 1), len(KnowledgeRAGService._chunks))

        hit_pairs: list[tuple[int, float]] = []
        if KnowledgeRAGService._index_backend == 'faiss' and KnowledgeRAGService._index is not None:
            scores, idxs = KnowledgeRAGService._index.search(query_vec, k)
            for idx, score in zip(idxs[0], scores[0]):
                if idx < 0:
                    continue
                hit_pairs.append((int(idx), float(score)))
        else:
            scores = np.dot(vectors, query_vec[0])
            idxs = np.argsort(-scores)[:k]
            for idx in idxs:
                hit_pairs.append((int(idx), float(scores[idx])))

        results: list[dict[str, Any]] = []
        for idx, score in hit_pairs:
            chunk = KnowledgeRAGService._chunks[idx]
            results.append(
                {
                    'chunk_id': chunk['chunk_id'],
                    'source': chunk['source'],
                    'content': chunk['content'],
                    'score': round(max(score, 0.0), 6)
                }
            )
        return results

    @staticmethod
    def _build_answer_by_llm(question: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """基于检索上下文调用模型生成结构化回答。"""
        context_lines: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            context_lines.append(f"[片段{idx}] 来源：{chunk['source']}\n内容：{chunk['content']}")

        prompt = (
            '你是企业 ERP 系统中的知识库助手，请仅依据给定知识片段回答。\n'
            '若证据不足，请明确说明“当前知识库证据不足”。\n'
            '请严格返回 JSON 对象，不要输出额外文本。\n'
            '要求：basis 必须是“依据摘要”，不能粘贴大段原文；每条 20~70 字，最多 4 条。\n'
            'JSON 结构：\n'
            '{\n'
            '  "answer": "string",\n'
            '  "basis": ["string"]\n'
            '}\n'
            f'问题：{question}\n'
            f'知识片段：\n{chr(10).join(context_lines)}'
        )

        data = DeepSeekService.chat_json(prompt)
        answer = str(data.get('answer', '')).strip()
        basis_raw = data.get('basis', [])
        basis = [str(item).strip() for item in basis_raw] if isinstance(basis_raw, list) else []
        basis = KnowledgeRAGService._sanitize_basis(basis, chunks)

        # 兜底：若模型未给出有效依据摘要，则给出简短结构化依据，避免出现空白区块。
        if not basis and chunks:
            source_counter = Counter([item['source'] for item in chunks])
            top_sources = [source for source, _count in source_counter.most_common(2)]
            basis = [
                f"主要依据文档：{'、'.join(top_sources)}",
                f"共命中 {len(chunks)} 个相关片段，详情见下方“命中知识片段”。"
            ]

        return {
            'answer': answer or '当前知识库暂无可用答案。',
            'basis': basis
        }

    @staticmethod
    def _build_fallback_answer(question: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """模型调用失败时的回退回答。"""
        if not chunks:
            return {
                'answer': '未在知识库中检索到相关内容，建议补充文档后重试。',
                'basis': ['未命中有效知识片段。']
            }

        top_sources = KnowledgeRAGService._unique_keep_order(
            [str(item.get('source', '')) for item in chunks[:3] if item.get('source')]
        )
        source_text = '、'.join(top_sources) if top_sources else '未知来源文档'
        top_scores = [float(item.get('score', 0.0)) for item in chunks[:3]]
        max_score = max(top_scores) if top_scores else 0.0

        return {
            'answer': f'根据命中的知识片段，已找到与“{question}”相关的参考信息，请结合下方命中片段确认细节。',
            'basis': [
                f'主要依据来自：{source_text}',
                f'共命中 {len(chunks)} 个相关片段，最高相关度约 {max_score:.3f}'
            ]
        }

    @staticmethod
    def ask(question: str, top_k: int = 4) -> dict[str, Any]:
        """知识库问答主流程：检索 + 生成。"""
        q = (question or '').strip()
        if not q:
            raise ValueError('问题不能为空')

        chunks = KnowledgeRAGService._retrieve(q, top_k=top_k)
        try:
            answer_pack = (
                KnowledgeRAGService._build_answer_by_llm(q, chunks)
                if chunks
                else KnowledgeRAGService._build_fallback_answer(q, chunks)
            )
        except Exception:
            answer_pack = KnowledgeRAGService._build_fallback_answer(q, chunks)

        # 命中文档按命中次数排序，便于前端区分“主要依据文档”和“其他命中文档”。
        source_counter = Counter([item['source'] for item in chunks])
        source_pairs = source_counter.most_common()
        sources = [{'source': source, 'hit_count': count} for source, count in source_pairs]
        primary_sources = [source for source, _count in source_pairs[:2]]
        secondary_sources = [source for source, _count in source_pairs[2:]]
        return {
            'question': q,
            'answer': answer_pack['answer'],
            'basis': answer_pack['basis'],
            'sources': sources,
            'primary_sources': primary_sources,
            'secondary_sources': secondary_sources,
            'retrieved_chunks': chunks,
            'index_backend': KnowledgeRAGService._index_backend
        }
