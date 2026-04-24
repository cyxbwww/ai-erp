// AI 调用日志接口文件：封装日志列表与详情查询请求。
import http from './http'

// AI 调用日志列表查询参数
export interface AiCallLogListParams {
  module?: string
  task_type?: string
  status?: string
  keyword?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

// AI 调用日志列表项类型
export interface AiCallLogItem {
  id: number
  module: string | null
  task_type: string | null
  prompt_template_key: string | null
  prompt_version: string | null
  prompt: string
  response: string | null
  status: string
  error_message: string | null
  model_name: string
  latency_ms: number | null
  created_at: string
}

// AI 调用日志分页结果类型
export interface AiCallLogListResult {
  total: number
  page: number
  page_size: number
  items: AiCallLogItem[]
}

// AI 调用日志详情类型：详情接口返回完整 prompt、response 和错误信息。
export type AiCallLogDetail = AiCallLogItem

// AI 效果统计类型：用于日志页顶部统计卡片。
export interface AiCallLogSummary {
  total_calls: number
  success_calls: number
  failed_calls: number
  success_rate: number
  avg_latency_ms: number
  customer_follow_advice_calls: number
  customer_ai_adopted_count: number
  customer_ai_adoption_rate: number
}

// Prompt 模板维度调用效果统计类型。
export interface PromptTemplateSummaryItem {
  prompt_template_key: string
  prompt_version: string | null
  module: string | null
  task_type: string | null
  total_calls: number
  success_calls: number
  failed_calls: number
  success_rate: number
  avg_latency_ms: number
}

// 查询 AI 调用日志列表。
export const aiCallLogListApi = (params: AiCallLogListParams) => {
  return http.get('/api/ai-call-logs', { params })
}

// 查询 AI 调用日志详情。
export const aiCallLogDetailApi = (id: number) => {
  return http.get(`/api/ai-call-logs/${id}`)
}

// 查询 AI 效果统计。
export const aiCallLogSummaryApi = () => {
  return http.get('/api/ai-call-logs/summary')
}

// 查询 Prompt 模板维度调用效果统计。
export const aiCallLogPromptSummaryApi = () => {
  return http.get('/api/ai-call-logs/prompt-summary')
}
