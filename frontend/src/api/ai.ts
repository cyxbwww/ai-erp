// AI 接口文件：封装多 Agent 聊天分析请求与错误信息提取。
import { AxiosError } from 'axios'
import http from './http'
import type { AIChatRequest } from '@/types/ai'

// AI 多 Agent 会串联多个模型/检索步骤，单独放宽超时时间，避免沿用普通接口 10 秒超时。
const AI_CHAT_TIMEOUT_MS = 60000

// 调用多 Agent 分析接口。
export const aiChatApi = (payload: AIChatRequest) => {
  return http.post('/api/ai/chat', payload, {
    timeout: AI_CHAT_TIMEOUT_MS
  })
}

// 提取多 Agent 请求失败原因：优先展示后端统一响应 message，避免页面只显示固定失败文案。
export const getAiRequestErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof AxiosError) {
    const data = error.response?.data as { message?: string; detail?: string } | undefined
    return data?.message || data?.detail || error.message || fallback
  }
  if (error instanceof Error) {
    return error.message || fallback
  }
  return fallback
}
