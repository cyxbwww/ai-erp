// 订单接口文件：封装订单模块列表、详情、新增、编辑、删除与状态流转请求。
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

// 订单支付信息类型
export interface OrderPaymentInfo {
  method?: string
  status?: string
  transaction_no?: string
  paid_at?: string
}

// 订单发货信息类型
export interface OrderShippingInfo {
  status?: string
  company?: string
  tracking_no?: string
  shipped_at?: string
}

// 订单收货信息类型
export interface OrderReceiverInfo {
  receiver_name?: string
  receiver_phone?: string
  receiver_address?: string
  receive_status?: string
}

// 订单操作记录类型
export interface OrderOperationLog {
  id?: number
  action_type: string
  content: string
  operator: string
  operated_at: string
  remark?: string
}

// 订单详情类型
export interface OrderDetail extends Omit<OrderListItem, 'item_count'> {
  items: OrderItem[]
  // 以下字段为详情页扩展字段，后端可按需返回
  discount_amount?: number
  paid_amount?: number
  payment_info?: OrderPaymentInfo
  shipping_info?: OrderShippingInfo
  receiver_info?: OrderReceiverInfo
  operation_logs?: OrderOperationLog[]
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

