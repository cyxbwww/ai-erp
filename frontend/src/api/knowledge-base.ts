// 知识库接口文件：封装文档列表、索引重建与知识库问答请求。
import http from './http'

export interface KnowledgeAskPayload {
  question: string
  top_k?: number
}

export interface KnowledgeSourceItem {
  source: string
  hit_count: number
}

export interface KnowledgeChunkItem {
  chunk_id: string
  source: string
  content: string
  score: number
}

export interface KnowledgeAskResult {
  question: string
  answer: string
  basis: string[]
  sources: KnowledgeSourceItem[]
  primary_sources?: string[]
  secondary_sources?: string[]
  retrieved_chunks: KnowledgeChunkItem[]
  index_backend: string
}

export interface KnowledgeDocumentItem {
  source: string
  size: number
  updated_at: string
}

export const knowledgeAskApi = (payload: KnowledgeAskPayload) => {
  return http.post('/api/knowledge-base/ask', payload)
}

export const knowledgeDocumentsApi = () => {
  return http.get('/api/knowledge-base/documents')
}

export const knowledgeRebuildApi = () => {
  return http.post('/api/knowledge-base/rebuild')
}
