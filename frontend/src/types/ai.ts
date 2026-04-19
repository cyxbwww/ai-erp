// AI 接口类型定义：用于统一多 Agent 聊天请求与响应结构。
export interface AIChatRequest {
  scene: string
  user_message: string
  context: Record<string, any>
}

export interface AIPlan {
  task_type: string
  agents: string[]
  need_rag: boolean
  reason: string
}

export interface UIBlock {
  type: 'summary' | 'agent_result' | string
  title?: string
  content?: string
  agent_name?: string
  data?: Record<string, any>
}

export interface AIChatResult {
  task_type: string
  summary: string
  plan: AIPlan
  agent_outputs: Record<string, any>
  ui_blocks: UIBlock[]
}
