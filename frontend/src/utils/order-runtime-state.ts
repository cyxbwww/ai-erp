// 订单运行态工具：用于前端演示支付/发货/风险状态，后续可替换为真实接口字段。
export type OrderPaymentStatus = 'unpaid' | 'paid' | 'closed'
export type OrderShippingStatus = 'unshipped' | 'shipped'
export type OrderRiskLevel = 'low' | 'medium' | 'high'

// 订单运行态结构：保存列表与详情页共享的演示状态。
export interface OrderRuntimeState {
  payment_status: OrderPaymentStatus
  payment_time?: string
  shipping_status: OrderShippingStatus
  shipping_time?: string
  risk_level: OrderRiskLevel
  ai_analyzed: boolean
  ai_analyzed_at?: string
}

const STORAGE_KEY = 'ai_erp_order_runtime_state_map'

// 读取运行态映射。
export const getOrderRuntimeStateMap = (): Record<number, OrderRuntimeState> => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    return JSON.parse(raw) as Record<number, OrderRuntimeState>
  } catch (_error) {
    return {}
  }
}

// 保存运行态映射。
export const setOrderRuntimeStateMap = (map: Record<number, OrderRuntimeState>) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
}

// 获取单个订单运行态。
export const getOrderRuntimeState = (orderId: number): OrderRuntimeState | null => {
  const map = getOrderRuntimeStateMap()
  return map[orderId] || null
}

// 更新单个订单运行态（增量合并）。
export const patchOrderRuntimeState = (orderId: number, patch: Partial<OrderRuntimeState>) => {
  const map = getOrderRuntimeStateMap()
  const prev = map[orderId]
  const baseState: OrderRuntimeState = {
    payment_status: 'unpaid',
    shipping_status: 'unshipped',
    risk_level: 'low',
    ai_analyzed: false
  }
  map[orderId] = Object.assign(baseState, prev || {}, patch)
  setOrderRuntimeStateMap(map)
}

// 按订单状态生成默认运行态，避免列表与详情出现空白。
// 注意：风险等级统一以后端 AI 返回为准，默认态不再使用前端随机推导。
const buildDefaultStateByStatus = (status: string): OrderRuntimeState => {
  if (status === 'cancelled') {
    return {
      payment_status: 'closed',
      shipping_status: 'unshipped',
      risk_level: 'low',
      ai_analyzed: false
    }
  }
  if (status === 'completed') {
    return {
      payment_status: 'paid',
      shipping_status: 'shipped',
      risk_level: 'low',
      ai_analyzed: false
    }
  }
  if (status === 'confirmed') {
    return {
      payment_status: 'paid',
      shipping_status: 'unshipped',
      risk_level: 'low',
      ai_analyzed: false
    }
  }
  return {
    payment_status: 'unpaid',
    shipping_status: 'unshipped',
    risk_level: 'low',
    ai_analyzed: false
  }
}

// 初始化订单运行态（仅补齐缺失项，不覆盖已存在状态）。
export const ensureOrderRuntimeStates = (orders: Array<{ id: number; status: string }>) => {
  const map = getOrderRuntimeStateMap()
  let changed = false
  orders.forEach((order) => {
    if (!map[order.id]) {
      map[order.id] = buildDefaultStateByStatus(order.status)
      changed = true
    }
  })
  if (changed) {
    setOrderRuntimeStateMap(map)
  }
}
