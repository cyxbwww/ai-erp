// AI 接口文件：封装多 Agent 聊天分析请求。
import http from './http'
import type { AIChatRequest } from '@/types/ai'

// 调用多 Agent 分析接口。
export const aiChatApi = (payload: AIChatRequest) => {
  return http.post('/api/ai/chat', payload)
}
