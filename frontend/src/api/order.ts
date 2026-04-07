// 订单接口文件：封装订单模块列表、详情、新增、编辑、删除、状态流转与 AI 分析请求。
import http from './http'

// 订单明细项类型
export interface OrderItem {
  id?: number
  order_id?: number
  product_id: number
  product_name?: string
  product_code?: string
  unit?: string
  unit_price: number
  quantity: number
  subtotal?: number
}

// 订单列表项类型
export interface OrderListItem {
  id: number
  order_no: string
  customer_id: number
  customer_name: string
  status: string
  total_amount: number
  item_count: number
  remark: string
  created_at: string
  updated_at: string
}

// 订单详情类型
export interface OrderDetail extends Omit<OrderListItem, 'item_count'> {
  items: OrderItem[]
}

// 订单列表查询参数
export interface OrderListParams {
  keyword?: string
  status?: string
  page?: number
  page_size?: number
}

// 订单新增/编辑参数
export interface OrderFormPayload {
  id?: number
  customer_id: number
  status: string
  remark: string
  items: Array<{
    product_id: number
    unit_price: number
    quantity: number
  }>
}

// 订单状态流转参数
export interface OrderStatusPayload {
  id: number
  status: 'draft' | 'confirmed' | 'completed' | 'cancelled'
}

// 订单 AI 分析请求参数
export interface OrderAIAnalysisPayload {
  analysis_type: 'analysis' | 'risk' | 'advice'
}

// 订单 AI 分析返回结构
export interface OrderAIAnalysisResult {
  analysis_type: 'analysis' | 'risk' | 'advice'
  title: string
  summary: string
  highlights: string[]
  risks: string[]
  suggestions: string[]
  ai_source: 'deepseek' | 'fallback'
}

// 获取订单列表
export const orderListApi = (params: OrderListParams) => {
  return http.get('/api/order/list', { params })
}

// 获取订单详情
export const orderDetailApi = (id: number) => {
  return http.get(`/api/order/detail/${id}`)
}

// 新增订单
export const orderCreateApi = (payload: OrderFormPayload) => {
  return http.post('/api/order/create', payload)
}

// 编辑订单
export const orderUpdateApi = (payload: OrderFormPayload) => {
  return http.put('/api/order/update', payload)
}

// 更新订单状态
export const orderStatusUpdateApi = (payload: OrderStatusPayload) => {
  return http.put('/api/order/status', payload)
}

// 删除订单
export const orderDeleteApi = (id: number) => {
  return http.delete(`/api/order/delete/${id}`)
}

// 订单 AI 分析
export const orderAIAnalysisApi = (id: number, payload: OrderAIAnalysisPayload) => {
  return http.post(`/api/order/${id}/ai-analysis`, payload)
}

