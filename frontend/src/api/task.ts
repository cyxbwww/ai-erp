// 任务接口文件：封装 AI 任务草稿确认创建接口。
import http from './http'

// AI 任务草稿落库请求结构：尽量复用后端 task_payload。
export interface TaskFromAIDraftPayload {
  task_type?: string
  title: string
  description?: string
  priority?: string
  owner?: string
  due_time?: string
  reminder_text?: string
  related_customer_id?: number
  source?: string
}

// 真实任务基础返回结构。
export interface TaskDetail {
  id: number
  title: string
  description: string
  priority: string
  status: string
  owner: string
  due_time: string
  customer_id?: number | null
  source: string
  created_by?: number | null
  created_at: string
  updated_at: string
}

// 查询客户关联任务参数。
export interface TaskListParams {
  customer_id: number
  status?: string
}

// 根据 AI 任务草稿创建真实任务。
export const createTaskFromAIDraftApi = (payload: TaskFromAIDraftPayload) => {
  return http.post('/api/tasks/from-ai-draft', payload)
}

// 查询客户关联任务列表。
export const taskListApi = (params: TaskListParams) => {
  return http.get('/api/tasks', { params })
}
