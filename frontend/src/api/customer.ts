// 客户与跟进记录接口文件：封装客户模块全部请求方法与类型。
import http from './http'

// 客户列表项类型
export interface CustomerItem {
  id: number
  name: string
  contact_name: string
  phone: string
  email: string
  company: string
  level: string
  status: string
  source: string
  owner_name: string
  last_follow_at: string
  follow_reminder_type: string
  follow_reminder_text: string
  remark: string
  created_at: string
  updated_at: string
}

// 客户列表查询参数
export interface CustomerListParams {
  keyword?: string
  level?: string
  status?: string
  source?: string
  owner_name?: string
  created_start?: string
  created_end?: string
  follow_start?: string
  follow_end?: string
  page?: number
  page_size?: number
}

// 客户新增/编辑表单参数
export interface CustomerFormPayload {
  id?: number
  name: string
  contact_name: string
  phone: string
  email?: string
  company: string
  level: string
  status: string
  source: string
  owner_name: string
  last_follow_at?: string
  remark: string
}

// 客户跟进记录列表项类型
export interface CustomerFollowRecordItem {
  id: number
  customer_id: number
  follow_type: string
  content: string
  result: string
  next_follow_time: string
  follow_user_id: number
  follow_user_name: string
  created_at: string
}

// 客户跟进记录查询参数
export interface CustomerFollowRecordListParams {
  customer_id: number
  keyword?: string
  follow_type?: string
  page?: number
  page_size?: number
}

// 客户跟进记录新增/编辑参数
export interface CustomerFollowRecordPayload {
  id?: number
  customer_id: number
  follow_type: string
  content: string
  result: string
  next_follow_time?: string | null
}

// 获取客户列表（搜索 + 分页）
export const customerListApi = (params: CustomerListParams) => {
  return http.get('/api/customer/list', { params })
}

// 新增客户
export const customerCreateApi = (payload: CustomerFormPayload) => {
  return http.post('/api/customer/create', payload)
}

// 编辑客户
export const customerUpdateApi = (payload: CustomerFormPayload) => {
  return http.put('/api/customer/update', payload)
}

// 删除客户
export const customerDeleteApi = (id: number) => {
  return http.delete(`/api/customer/delete/${id}`)
}

// 获取客户详情
export const customerDetailApi = (id: number) => {
  return http.get(`/api/customer/detail/${id}`)
}

// 获取客户跟进记录列表
export const customerFollowRecordListApi = (params: CustomerFollowRecordListParams) => {
  return http.get('/api/customer-follow-record/list', { params })
}

// 新增客户跟进记录
export const customerFollowRecordCreateApi = (payload: CustomerFollowRecordPayload) => {
  return http.post('/api/customer-follow-record/create', payload)
}

// 编辑客户跟进记录
export const customerFollowRecordUpdateApi = (payload: CustomerFollowRecordPayload) => {
  return http.put('/api/customer-follow-record/update', payload)
}

// 删除客户跟进记录
export const customerFollowRecordDeleteApi = (id: number) => {
  return http.delete(`/api/customer-follow-record/delete/${id}`)
}
