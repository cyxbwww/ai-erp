"""知识库服务：基于 LangChain 实现文档加载、切分、检索与答案生成。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import HashingVectorizer

from app.services.deepseek_service import DeepSeekService


class HashingEmbeddings(Embeddings):
    """Hashing Embedding 适配器：将现有 HashingVectorizer 封装为 LangChain Embeddings。"""

    def __init__(self) -> None:
        # 使用字符 ngram 兼容中文语料；后续可替换为标准 embedding 模型。
        self.vectorizer = HashingVectorizer(
            n_features=1024,
            alternate_sign=False,
            norm=None,
            analyzer='char',
            ngram_range=(1, 2)
        )

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        """L2 归一化：使向量内积更接近余弦相似度。"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return (vectors / norms).astype(np.float32)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化。"""
        matrix = self.vectorizer.transform(texts)
        dense = matrix.toarray().astype(np.float32)
        return self._normalize(dense).tolist()

    def embed_query(self, text: str) -> list[float]:
        """单条查询向量化。"""
        return self.embed_documents([text])[0]


class KnowledgeRAGService:
    """知识库 RAG 服务：LangChain Loader + Splitter + VectorStore + Retriever。"""

    KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / 'knowledge_base'
    # 索引持久化目录：保存 FAISS 索引与元数据，避免服务重启后重复重建。
    INDEX_DIR = Path(__file__).resolve().parents[2] / 'knowledge_index'
    INDEX_META_FILE = INDEX_DIR / 'meta.json'
    SUPPORTED_SUFFIXES = {'.md', '.txt', '.pdf'}

    _vector_store: FAISS | None = None
    _retriever: Any = None
    _chunks: list[dict[str, Any]] = []
    _documents: list[dict[str, Any]] = []
    _index_backend: str = 'langchain-faiss'
    _embedding_backend: str = 'hashing-vectorizer'

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
    def _scan_document_files() -> list[dict[str, Any]]:
        """扫描知识库目录并返回文档元数据（用于文档列表展示）。"""
        root = KnowledgeRAGService.KNOWLEDGE_DIR
        root.mkdir(parents=True, exist_ok=True)

        files: list[dict[str, Any]] = []
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in KnowledgeRAGService.SUPPORTED_SUFFIXES:
                continue
            stat = path.stat()
            files.append(
                {
                    'source': str(path.relative_to(root)).replace('\\', '/'),
                    'size': stat.st_size,
                    'updated_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'suffix': path.suffix.lower()
                }
            )
        return files

    @staticmethod
    def _load_documents_with_langchain(files: list[dict[str, Any]]) -> list[Document]:
        """使用 LangChain Loader 加载 .md/.txt/.pdf 文档。"""
        root = KnowledgeRAGService.KNOWLEDGE_DIR
        loaded_docs: list[Document] = []

        for file_info in files:
            source = str(file_info.get('source', ''))
            suffix = str(file_info.get('suffix', '')).lower()
            if not source:
                continue
            path = root / source
            if not path.exists():
                continue

            try:
                if suffix in {'.md', '.txt'}:
                    docs = TextLoader(str(path), autodetect_encoding=True).load()
                elif suffix == '.pdf':
                    docs = PyPDFLoader(str(path)).load()
                else:
                    docs = []
            except Exception:
                # 文本类文档回退到本地读取，保证索引构建稳定可用。
                if suffix in {'.md', '.txt'}:
                    try:
                        text = path.read_text(encoding='utf-8', errors='ignore').strip()
                        docs = [Document(page_content=text, metadata={'source': source})] if text else []
                    except Exception:
                        docs = []
                else:
                    # PDF 若加载失败暂时跳过，后续可接入更稳健的 OCR/PDF 解析链路。
                    docs = []

            for doc in docs:
                content = (doc.page_content or '').strip()
                if not content:
                    continue
                metadata = dict(doc.metadata or {})
                metadata['source'] = source
                doc.metadata = metadata
                loaded_docs.append(doc)

        return loaded_docs

    @staticmethod
    def _split_documents_with_langchain(documents: list[Document]) -> list[Document]:
        """使用 LangChain TextSplitter 对文档进行切分。"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=360,
            chunk_overlap=60,
            separators=['\n\n', '\n', '。', '！', '？', '.', ' ']
        )
        chunks = splitter.split_documents(documents)

        # 为每个 chunk 生成稳定 chunk_id，便于前端渲染与交互。
        for idx, chunk in enumerate(chunks, start=1):
            source = str(chunk.metadata.get('source', 'unknown'))
            page = chunk.metadata.get('page')
            page_tag = ''
            if isinstance(page, int):
                page_tag = f':p{page + 1}'
            chunk.metadata['chunk_id'] = f'{source}{page_tag}#{idx}'

        return chunks

    @staticmethod
    def _save_index_metadata(
        files: list[dict[str, Any]],
        chunks: list[dict[str, Any]]
    ) -> None:
        """保存索引元数据：用于重启后恢复文档列表与片段基础信息。"""
        KnowledgeRAGService.INDEX_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'documents': files,
            'chunks': chunks,
            'index_backend': KnowledgeRAGService._index_backend,
            'embedding_backend': KnowledgeRAGService._embedding_backend
        }
        KnowledgeRAGService.INDEX_META_FILE.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding='utf-8'
        )

    @staticmethod
    def _load_index_metadata() -> None:
        """加载索引元数据：恢复文档列表与片段信息。"""
        if not KnowledgeRAGService.INDEX_META_FILE.exists():
            return
        try:
            payload = json.loads(KnowledgeRAGService.INDEX_META_FILE.read_text(encoding='utf-8'))
            docs = payload.get('documents', [])
            chunks = payload.get('chunks', [])
            if isinstance(docs, list):
                KnowledgeRAGService._documents = docs
            if isinstance(chunks, list):
                KnowledgeRAGService._chunks = chunks
        except Exception:
            # 元数据损坏不阻塞主流程，后续可通过 rebuild 重新生成。
            pass

    @staticmethod
    def _load_persisted_index() -> bool:
        """尝试从磁盘加载 FAISS 索引，成功返回 True。"""
        index_file = KnowledgeRAGService.INDEX_DIR / 'index.faiss'
        pkl_file = KnowledgeRAGService.INDEX_DIR / 'index.pkl'
        if not index_file.exists() or not pkl_file.exists():
            return False
        try:
            vector_store = FAISS.load_local(
                str(KnowledgeRAGService.INDEX_DIR),
                HashingEmbeddings(),
                allow_dangerous_deserialization=True
            )
            KnowledgeRAGService._vector_store = vector_store
            KnowledgeRAGService._retriever = vector_store.as_retriever(
                search_type='similarity',
                search_kwargs={'k': 4}
            )
            KnowledgeRAGService._load_index_metadata()
            return True
        except Exception:
            return False

    @staticmethod
    def get_index_info() -> dict[str, Any]:
        """获取索引状态信息：用于前端展示索引健康状态与构建时间。"""
        index_file = KnowledgeRAGService.INDEX_DIR / 'index.faiss'
        pkl_file = KnowledgeRAGService.INDEX_DIR / 'index.pkl'
        meta_exists = KnowledgeRAGService.INDEX_META_FILE.exists()
        index_exists = index_file.exists() and pkl_file.exists()
        loaded = KnowledgeRAGService._vector_store is not None and KnowledgeRAGService._retriever is not None

        documents_count = len(KnowledgeRAGService._documents)
        chunks_count = len(KnowledgeRAGService._chunks)
        saved_at = ''

        if meta_exists:
            try:
                payload = json.loads(KnowledgeRAGService.INDEX_META_FILE.read_text(encoding='utf-8'))
                saved_at = str(payload.get('saved_at', ''))
                if not documents_count:
                    docs = payload.get('documents', [])
                    if isinstance(docs, list):
                        documents_count = len(docs)
                if not chunks_count:
                    chunks = payload.get('chunks', [])
                    if isinstance(chunks, list):
                        chunks_count = len(chunks)
            except Exception:
                # 元数据异常时不抛错，返回当前可用状态。
                pass

        index_size_bytes = 0
        if KnowledgeRAGService.INDEX_DIR.exists():
            for path in KnowledgeRAGService.INDEX_DIR.rglob('*'):
                if path.is_file():
                    try:
                        index_size_bytes += path.stat().st_size
                    except OSError:
                        continue

        return {
            'index_loaded': loaded,
            'index_exists': index_exists,
            'metadata_exists': meta_exists,
            'saved_at': saved_at,
            'document_count': documents_count,
            'chunk_count': chunks_count,
            'index_size_bytes': index_size_bytes,
            'index_backend': KnowledgeRAGService._index_backend,
            'embedding_backend': KnowledgeRAGService._embedding_backend
        }

    @staticmethod
    def rebuild_index() -> dict[str, Any]:
        """重建索引：LangChain 文档加载 -> 切分 -> FAISS 向量库。"""
        files = KnowledgeRAGService._scan_document_files()
        documents = KnowledgeRAGService._load_documents_with_langchain(files)

        if not documents:
            KnowledgeRAGService._documents = files
            KnowledgeRAGService._chunks = []
            KnowledgeRAGService._vector_store = None
            KnowledgeRAGService._retriever = None
            return {
                'document_count': len(files),
                'chunk_count': 0,
                'index_backend': KnowledgeRAGService._index_backend,
                'embedding_backend': KnowledgeRAGService._embedding_backend
            }

        chunk_docs = KnowledgeRAGService._split_documents_with_langchain(documents)
        embeddings = HashingEmbeddings()
        vector_store = FAISS.from_documents(chunk_docs, embeddings)
        retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': 4})

        KnowledgeRAGService._documents = files
        KnowledgeRAGService._vector_store = vector_store
        KnowledgeRAGService._retriever = retriever
        KnowledgeRAGService._chunks = [
            {
                'chunk_id': str(doc.metadata.get('chunk_id', '')),
                'source': str(doc.metadata.get('source', 'unknown')),
                'content': str(doc.page_content or ''),
                'score': 0.0
            }
            for doc in chunk_docs
        ]
        # 保存索引与元数据，支持服务重启后直接加载。
        KnowledgeRAGService.INDEX_DIR.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(KnowledgeRAGService.INDEX_DIR))
        KnowledgeRAGService._save_index_metadata(files, KnowledgeRAGService._chunks)

        return {
            'document_count': len(files),
            'chunk_count': len(chunk_docs),
            'index_backend': KnowledgeRAGService._index_backend,
            'embedding_backend': KnowledgeRAGService._embedding_backend
        }

    @staticmethod
    def _ensure_index_ready() -> None:
        """懒加载索引：首次问答时自动构建。"""
        if KnowledgeRAGService._vector_store is not None and KnowledgeRAGService._retriever is not None:
            return
        if KnowledgeRAGService._load_persisted_index():
            return
        KnowledgeRAGService.rebuild_index()

    @staticmethod
    def list_documents() -> dict[str, Any]:
        """返回知识库文档列表。"""
        if not KnowledgeRAGService._documents:
            KnowledgeRAGService._documents = KnowledgeRAGService._scan_document_files()
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
        """通过 LangChain Retriever 检索片段，并补充分数信息。"""
        KnowledgeRAGService._ensure_index_ready()
        if KnowledgeRAGService._vector_store is None:
            return []

        k = max(1, int(top_k))
        retriever = KnowledgeRAGService._vector_store.as_retriever(
            search_type='similarity',
            search_kwargs={'k': k}
        )
        docs = retriever.invoke(question)

        # 使用向量库分数接口补充相关度，便于前端显示“最高相关度”。
        score_rows = KnowledgeRAGService._vector_store.similarity_search_with_score(question, k=k)
        score_map: dict[str, float] = {}
        for doc, score in score_rows:
            chunk_id = str(doc.metadata.get('chunk_id', ''))
            if not chunk_id:
                continue
            score_map[chunk_id] = float(score)

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for doc in docs:
            chunk_id = str(doc.metadata.get('chunk_id', '')).strip()
            source = str(doc.metadata.get('source', 'unknown')).strip()
            content = str(doc.page_content or '').strip()
            if not content:
                continue
            if not chunk_id:
                chunk_id = f'{source}#{len(results) + 1}'
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            score = score_map.get(chunk_id, 0.0)
            results.append(
                {
                    'chunk_id': chunk_id,
                    'source': source,
                    'content': content,
                    'score': round(max(score, 0.0), 6)
                }
            )

        return results

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

        # 记录知识库问答的 AI 调用来源，便于 ai_call_logs 按模块和任务类型追踪。
        data = DeepSeekService.chat_json(prompt, module='knowledge_base', task_type='rag_answer')
        answer = str(data.get('answer', '')).strip()
        basis_raw = data.get('basis', [])
        basis = [str(item).strip() for item in basis_raw] if isinstance(basis_raw, list) else []
        basis = KnowledgeRAGService._sanitize_basis(basis, chunks)

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
            'index_backend': KnowledgeRAGService._index_backend,
            'embedding_backend': KnowledgeRAGService._embedding_backend
        }
