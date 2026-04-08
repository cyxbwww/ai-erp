<template>
  <div class="dashboard-page">
    <n-card title="经营看板" :bordered="false">
      <template #header-extra>
        <n-space align="center">
          <n-select
            v-model:value="timeRangePreset"
            :options="timeRangeOptions"
            style="width: 140px"
            @update:value="handleTimeRangeChange"
          />
          <n-button :loading="pageLoading" @click="refreshDashboard">刷新数据</n-button>
        </n-space>
      </template>

      <n-spin :show="pageLoading">
        <n-grid :cols="24" :x-gap="12" :y-gap="12">
          <n-gi v-for="metric in metricsCards" :key="metric.key" :span="8">
            <n-card size="small" :title="metric.title" class="metric-card">
              <div class="metric-value">{{ metric.value }}</div>
            </n-card>
          </n-gi>
        </n-grid>
      </n-spin>
    </n-card>

    <div class="refresh-meta">看板数据时间范围：{{ currentRangeLabel }}，最近刷新：{{ dashboardRefreshedAt || '-' }}</div>

    <n-grid :cols="24" :x-gap="16" :y-gap="16">
      <n-gi :span="12">
        <n-card title="销售趋势" :bordered="false">
          <div ref="salesTrendRef" class="chart-container"></div>
        </n-card>
      </n-gi>
      <n-gi :span="12">
        <n-card title="订单状态分布" :bordered="false">
          <div ref="orderStatusRef" class="chart-container"></div>
        </n-card>
      </n-gi>
      <n-gi :span="12">
        <n-card title="客户等级分布" :bordered="false">
          <div ref="customerLevelRef" class="chart-container"></div>
        </n-card>
      </n-gi>
      <n-gi :span="12">
        <n-card title="热销商品 Top5" :bordered="false">
          <div ref="topProductsRef" class="chart-container"></div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid :cols="24" :x-gap="16" :y-gap="16">
      <n-gi :span="8">
        <n-card title="低库存商品" :bordered="false">
          <n-data-table
            :columns="lowStockColumns"
            :data="lowStockProducts"
            :pagination="false"
            :locale="{ emptyText: '暂无低库存商品' }"
            :max-height="260"
          />
        </n-card>
      </n-gi>
      <n-gi :span="8">
        <n-card title="风险订单" :bordered="false">
          <n-data-table
            :columns="riskOrderColumns"
            :data="riskOrders"
            :pagination="false"
            :locale="{ emptyText: '暂无风险订单' }"
            :max-height="260"
          />
        </n-card>
      </n-gi>
      <n-gi :span="8">
        <n-card title="待跟进客户" :bordered="false">
          <n-data-table
            :columns="followCustomerColumns"
            :data="pendingFollowCustomers"
            :pagination="false"
            :locale="{ emptyText: '暂无待跟进客户' }"
            :max-height="260"
          />
        </n-card>
      </n-gi>
    </n-grid>

    <n-card title="AI 经营助手" :bordered="false">
      <n-grid :cols="2" :x-gap="12" :y-gap="12">
        <n-gi v-for="card in aiCards" :key="card.type">
          <n-card size="small" :title="card.title" class="ai-card">
            <template #header-extra>
              <n-space size="small" align="center">
                <n-tag size="small" :type="aiResults[card.type] ? 'success' : 'default'">
                  {{ aiResults[card.type] ? '已生成' : '未生成' }}
                </n-tag>
                <n-button size="tiny" :loading="aiLoadingMap[card.type]" @click="generateAI(card.type)">重新生成</n-button>
                <n-button size="tiny" :disabled="!aiResults[card.type]" @click="copyAIResult(card.type)">复制结果</n-button>
              </n-space>
            </template>

            <n-spin :show="aiLoadingMap[card.type]">
              <div class="ai-meta">分析时间：{{ aiGeneratedAt[card.type] || '-' }}</div>
              <n-empty v-if="!aiResults[card.type]" :description="card.emptyText" />

              <n-space v-else vertical :size="10">
                <div class="ai-summary">{{ aiResults[card.type]?.summary || '-' }}</div>
                <div v-for="section in aiResults[card.type]?.sections || []" :key="`${card.type}-${section.title}`" class="ai-section">
                  <div class="ai-section-title">{{ section.title }}</div>
                  <ul class="ai-list">
                    <li v-for="(item, idx) in section.points" :key="`${card.type}-${section.title}-${idx}`">{{ item }}</li>
                  </ul>
                </div>
              </n-space>
            </n-spin>
          </n-card>
        </n-gi>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 经营看板页面：聚合客户、商品、订单数据并提供结构化 AI 经营分析。
import { computed, h, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NEmpty,
  NGi,
  NGrid,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import { customerListApi, type CustomerItem } from '@/api/customer'
import { productListApi, type ProductItem } from '@/api/product'
import { orderDetailApi, orderListApi, type OrderDetail, type OrderListItem } from '@/api/order'
import {
  getCustomerLevelLabel,
  getOrderStatusLabel,
  getOrderStatusTagType,
  getProductStatusLabel,
  getProductStatusTagType
} from '@/constants/enums'
import { getOrderRuntimeStateMap } from '@/utils/order-runtime-state'
import * as echarts from 'echarts'

type AIType = 'sales' | 'risk' | 'customer' | 'inventory'

type AISection = {
  title: string
  points: string[]
}

type DashboardAIResult = {
  summary: string
  sections: AISection[]
}

type DashboardPersistedAI = {
  results: Record<AIType, DashboardAIResult | null>
  generatedAt: Record<AIType, string>
}

type RiskOrderItem = {
  id: number
  order_no: string
  customer_name: string
  status: string
  risk_reason: string
}

type PendingFollowCustomerItem = {
  id: number
  name: string
  owner_name: string
  last_follow_at: string
  overdue_days: number
}

type TimeRangePreset = '7d' | '30d' | 'month'

const message = useMessage()
const router = useRouter()

// 页面数据加载状态。
const pageLoading = ref(false)

const customers = ref<CustomerItem[]>([])
const products = ref<ProductItem[]>([])
const orders = ref<OrderListItem[]>([])
const topProductData = ref<Array<{ product_name: string; quantity: number; amount: number }>>([])

const salesTrendRef = ref<HTMLElement | null>(null)
const orderStatusRef = ref<HTMLElement | null>(null)
const customerLevelRef = ref<HTMLElement | null>(null)
const topProductsRef = ref<HTMLElement | null>(null)

let salesTrendChart: any = null
let orderStatusChart: any = null
let customerLevelChart: any = null
let topProductsChart: any = null

const LOW_STOCK_THRESHOLD = 20
const DASHBOARD_AI_STORAGE_KEY = 'ai_erp_dashboard_ai_results_v1'

// 看板时间范围：用于控制聚合口径（近7天、近30天、本月）。
const timeRangePreset = ref<TimeRangePreset>('7d')
const timeRangeOptions = [
  { label: '近7天', value: '7d' },
  { label: '近30天', value: '30d' },
  { label: '本月', value: 'month' }
]
const dashboardRefreshedAt = ref('')

const aiCards: Array<{ type: AIType; title: string; emptyText: string }> = [
  { type: 'sales', title: 'AI 销售分析', emptyText: '暂无销售分析结果，请点击重新生成' },
  { type: 'risk', title: 'AI 风险概览', emptyText: '暂无风险分析结果，请点击重新生成' },
  { type: 'customer', title: 'AI 客户经营建议', emptyText: '暂无客户建议结果，请点击重新生成' },
  { type: 'inventory', title: 'AI 库存建议', emptyText: '暂无库存建议结果，请点击重新生成' }
]

const aiLoadingMap = reactive<Record<AIType, boolean>>({
  sales: false,
  risk: false,
  customer: false,
  inventory: false
})

const aiResults = reactive<Record<AIType, DashboardAIResult | null>>({
  sales: null,
  risk: null,
  customer: null,
  inventory: null
})

const aiGeneratedAt = reactive<Record<AIType, string>>({
  sales: '',
  risk: '',
  customer: '',
  inventory: ''
})

// 解析接口时间字符串，兼容 yyyy-MM-dd HH:mm:ss 格式。
const toTimeMs = (raw?: string) => {
  if (!raw) return 0
  const time = new Date(raw.replace(' ', 'T')).getTime()
  return Number.isNaN(time) ? 0 : time
}

// 根据当前选择返回时间范围起止（毫秒）。
const getRangeBoundaries = (preset: TimeRangePreset) => {
  const now = new Date()
  const end = new Date(now)
  end.setHours(23, 59, 59, 999)

  const start = new Date(now)
  if (preset === '7d') {
    start.setDate(now.getDate() - 6)
  } else if (preset === '30d') {
    start.setDate(now.getDate() - 29)
  } else {
    start.setDate(1)
  }
  start.setHours(0, 0, 0, 0)

  return { startMs: start.getTime(), endMs: end.getTime() }
}

const currentRangeLabel = computed(() => {
  const hit = timeRangeOptions.find((item) => item.value === timeRangePreset.value)
  return hit?.label || '近7天'
})

const filteredOrders = computed(() => {
  const { startMs, endMs } = getRangeBoundaries(timeRangePreset.value)
  return orders.value.filter((item) => {
    const time = toTimeMs(item.created_at)
    return time >= startMs && time <= endMs
  })
})

const filteredCustomers = computed(() => {
  const { startMs, endMs } = getRangeBoundaries(timeRangePreset.value)
  return customers.value.filter((item) => {
    const time = toTimeMs(item.created_at)
    return time >= startMs && time <= endMs
  })
})

const metricsCards = computed(() => {
  const salesTotal = filteredOrders.value
    .filter((item) => item.status !== 'cancelled')
    .reduce((sum, item) => sum + Number(item.total_amount || 0), 0)

  const rangeNewCustomers = filteredCustomers.value.length
  const pendingOrders = filteredOrders.value.filter((item) => ['draft', 'confirmed'].includes(item.status)).length

  return [
    { key: 'customer_total', title: '客户总数', value: `${customers.value.length}` },
    { key: 'product_total', title: '商品总数', value: `${products.value.length}` },
    { key: 'order_total', title: '订单总数', value: `${filteredOrders.value.length}` },
    { key: 'sales_total', title: '销售总额', value: `¥${salesTotal.toFixed(2)}` },
    { key: 'new_customers', title: '范围内新增客户数', value: `${rangeNewCustomers}` },
    { key: 'pending_orders', title: '待处理订单数', value: `${pendingOrders}` }
  ]
})

const lowStockProducts = computed(() =>
  products.value
    .filter((item) => Number(item.stock_qty || 0) < LOW_STOCK_THRESHOLD)
    .sort((a, b) => Number(a.stock_qty || 0) - Number(b.stock_qty || 0))
    .slice(0, 8)
)

const riskOrders = computed<RiskOrderItem[]>(() => {
  const runtimeMap = getOrderRuntimeStateMap()
  const now = Date.now()

  const rows = filteredOrders.value
    .map((item) => {
      const runtime = runtimeMap[item.id]
      const createdAt = toTimeMs(item.created_at)
      const overdueDays = createdAt ? Math.floor((now - createdAt) / (24 * 3600 * 1000)) : 0

      const reasons: string[] = []
      if (runtime?.risk_level === 'high') reasons.push('AI 高风险')
      if (runtime?.risk_level === 'medium') reasons.push('AI 中风险')
      if (item.status === 'draft' && overdueDays >= 3) reasons.push(`草稿超时 ${overdueDays} 天`)
      if (item.status === 'confirmed' && Number(item.total_amount || 0) >= 20000) reasons.push('高金额待完成')

      return {
        id: item.id,
        order_no: item.order_no,
        customer_name: item.customer_name,
        status: item.status,
        risk_reason: reasons.join('；')
      }
    })
    .filter((item) => item.risk_reason)
    .slice(0, 8)

  return rows
})

const pendingFollowCustomers = computed<PendingFollowCustomerItem[]>(() => {
  const now = Date.now()
  return filteredCustomers.value
    .map((item) => {
      const lastFollowAt = item.last_follow_at
      const lastTime = toTimeMs(lastFollowAt)
      const overdueDays = lastTime ? Math.floor((now - lastTime) / (24 * 3600 * 1000)) : 999
      return {
        id: item.id,
        name: item.name,
        owner_name: item.owner_name || '-',
        last_follow_at: item.last_follow_at || '-',
        overdue_days: overdueDays
      }
    })
    .filter((item) => item.overdue_days >= 7)
    .sort((a, b) => b.overdue_days - a.overdue_days)
    .slice(0, 8)
})

const lowStockColumns: DataTableColumns<ProductItem> = [
  { title: '商品名称', key: 'name', minWidth: 120 },
  { title: '库存', key: 'stock_qty', width: 70 },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: (row) =>
      h(
        NTag,
        { size: 'small', type: getProductStatusTagType(row.status) as any },
        { default: () => getProductStatusLabel(row.status) }
      )
  },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    render: () =>
      h(
        NButton,
        {
          size: 'tiny',
          tertiary: true,
          type: 'primary',
          onClick: () => {
            router.push({ name: 'Product' })
          }
        },
        { default: () => '查看' }
      )
  }
]

const riskOrderColumns: DataTableColumns<RiskOrderItem> = [
  { title: '订单编号', key: 'order_no', minWidth: 120 },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: (row) =>
      h(
        NTag,
        { size: 'small', type: getOrderStatusTagType(row.status) as any },
        { default: () => getOrderStatusLabel(row.status) }
      )
  },
  { title: '风险原因', key: 'risk_reason', minWidth: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    render: (row) =>
      h(
        NButton,
        {
          size: 'tiny',
          tertiary: true,
          type: 'primary',
          onClick: () => {
            router.push({ name: 'OrderDetail', params: { id: String(row.id) } })
          }
        },
        { default: () => '处理' }
      )
  }
]

const followCustomerColumns: DataTableColumns<PendingFollowCustomerItem> = [
  { title: '客户名称', key: 'name', minWidth: 110 },
  { title: '负责人', key: 'owner_name', width: 90 },
  { title: '最近跟进', key: 'last_follow_at', minWidth: 130 },
  {
    title: '超期天数',
    key: 'overdue_days',
    width: 80,
    render: (row) => `${row.overdue_days}`
  },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    render: (row) =>
      h(
        NButton,
        {
          size: 'tiny',
          tertiary: true,
          type: 'primary',
          onClick: () => {
            router.push({ name: 'CustomerDetail', params: { id: String(row.id) } })
          }
        },
        { default: () => '跟进' }
      )
  }
]

// 读取持久化 AI 结果。
const restorePersistedAIResults = () => {
  try {
    const raw = localStorage.getItem(DASHBOARD_AI_STORAGE_KEY)
    if (!raw) return
    const persisted = JSON.parse(raw) as DashboardPersistedAI

    ;(['sales', 'risk', 'customer', 'inventory'] as AIType[]).forEach((type) => {
      aiResults[type] = persisted.results?.[type] || null
      aiGeneratedAt[type] = persisted.generatedAt?.[type] || ''
    })
  } catch (_error) {
    // 忽略持久化读取异常，避免影响页面加载。
  }
}

// 持久化 AI 结果。
const persistAIResults = () => {
  const payload: DashboardPersistedAI = {
    results: {
      sales: aiResults.sales,
      risk: aiResults.risk,
      customer: aiResults.customer,
      inventory: aiResults.inventory
    },
    generatedAt: {
      sales: aiGeneratedAt.sales,
      risk: aiGeneratedAt.risk,
      customer: aiGeneratedAt.customer,
      inventory: aiGeneratedAt.inventory
    }
  }
  localStorage.setItem(DASHBOARD_AI_STORAGE_KEY, JSON.stringify(payload))
}

// 分页拉全量数据。
const fetchAllByPaging = async <T>(request: (page: number, pageSize: number) => Promise<T[]>): Promise<T[]> => {
  const list: T[] = []
  const pageSize = 100
  let page = 1
  let finished = false

  while (!finished) {
    const rows = await request(page, pageSize)
    list.push(...rows)
    if (rows.length < pageSize || page >= 30) {
      finished = true
    } else {
      page += 1
    }
  }

  return list
}

const fetchCustomers = async () => {
  const list = await fetchAllByPaging<CustomerItem>(async (page, pageSize) => {
    const res = await customerListApi({ page, page_size: pageSize })
    if (res.data.code !== 0) throw new Error(res.data.message || '客户数据加载失败')
    return (res.data?.data?.list || []) as CustomerItem[]
  })
  customers.value = list
}

const fetchProducts = async () => {
  const list = await fetchAllByPaging<ProductItem>(async (page, pageSize) => {
    const res = await productListApi({ page, page_size: pageSize })
    if (res.data.code !== 0) throw new Error(res.data.message || '商品数据加载失败')
    return (res.data?.data?.list || []) as ProductItem[]
  })
  products.value = list
}

const fetchOrders = async () => {
  const list = await fetchAllByPaging<OrderListItem>(async (page, pageSize) => {
    const res = await orderListApi({ page, page_size: pageSize })
    if (res.data.code !== 0) throw new Error(res.data.message || '订单数据加载失败')
    return (res.data?.data?.list || []) as OrderListItem[]
  })
  orders.value = list
}

// 聚合热销商品 Top5：读取近期订单详情进行聚合。
const buildTopProducts = async () => {
  const sourceOrders = [...filteredOrders.value]
    .sort((a, b) => toTimeMs(b.created_at) - toTimeMs(a.created_at))
    .slice(0, 20)
  const map = new Map<string, { product_name: string; quantity: number; amount: number }>()

  for (const order of sourceOrders) {
    try {
      const res = await orderDetailApi(order.id)
      if (res.data.code !== 0) continue
      const detail = res.data.data as OrderDetail
      ;(detail.items || []).forEach((item) => {
        const key = item.product_name || `商品-${item.product_id}`
        const prev = map.get(key) || { product_name: key, quantity: 0, amount: 0 }
        prev.quantity += Number(item.quantity || 0)
        prev.amount += Number(item.subtotal || 0)
        map.set(key, prev)
      })
    } catch (_error) {
      // 单条失败不影响整体演示
    }
  }

  topProductData.value = Array.from(map.values())
    .sort((a, b) => b.quantity - a.quantity)
    .slice(0, 5)
}

// 生成时间范围横轴标签：近7天、近30天、本月。
const getRangeDateLabels = () => {
  const labels: string[] = []
  const now = new Date()
  const days = timeRangePreset.value === '7d' ? 7 : timeRangePreset.value === '30d' ? 30 : now.getDate()
  for (let i = days - 1; i >= 0; i -= 1) {
    const d = new Date(now)
    d.setDate(now.getDate() - i)
    const m = `${d.getMonth() + 1}`.padStart(2, '0')
    const day = `${d.getDate()}`.padStart(2, '0')
    labels.push(`${m}-${day}`)
  }
  return labels
}

const renderCharts = async () => {
  await nextTick()

  if (salesTrendRef.value) {
    salesTrendChart?.dispose()
    salesTrendChart = echarts.init(salesTrendRef.value)
    const labels = getRangeDateLabels()
    const amountMap: Record<string, number> = {}
    labels.forEach((label) => {
      amountMap[label] = 0
    })
    filteredOrders.value.forEach((order) => {
      const datePart = (order.created_at || '').slice(5, 10)
      if (amountMap[datePart] !== undefined && order.status !== 'cancelled') {
        amountMap[datePart] += Number(order.total_amount || 0)
      }
    })

    salesTrendChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value' },
      series: [
        {
          name: '销售额',
          type: 'line',
          smooth: true,
          data: labels.map((label) => Number(amountMap[label].toFixed(2))),
          areaStyle: {}
        }
      ]
    })
  }

  if (orderStatusRef.value) {
    orderStatusChart?.dispose()
    orderStatusChart = echarts.init(orderStatusRef.value)
    const statusMap: Record<string, number> = {}
    filteredOrders.value.forEach((item) => {
      statusMap[item.status] = (statusMap[item.status] || 0) + 1
    })

    orderStatusChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['35%', '70%'],
          data: Object.keys(statusMap).map((status) => ({ name: getOrderStatusLabel(status), value: statusMap[status] }))
        }
      ]
    })
  }

  if (customerLevelRef.value) {
    customerLevelChart?.dispose()
    customerLevelChart = echarts.init(customerLevelRef.value)
    const levelMap: Record<string, number> = {}
    filteredCustomers.value.forEach((item) => {
      levelMap[item.level] = (levelMap[item.level] || 0) + 1
    })
    const labels = Object.keys(levelMap).map((level) => getCustomerLevelLabel(level))

    customerLevelChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: labels },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: {
          formatter: (value: number) => `${Math.round(value)}`
        }
      },
      series: [
        {
          name: '客户数',
          type: 'bar',
          data: Object.keys(levelMap).map((level) => levelMap[level]),
          barWidth: 28
        }
      ]
    })
  }

  if (topProductsRef.value) {
    topProductsChart?.dispose()
    topProductsChart = echarts.init(topProductsRef.value)
    const labels = topProductData.value.map((item) => item.product_name)
    const values = topProductData.value.map((item) => item.quantity)

    topProductsChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: labels, inverse: true },
      series: [
        {
          name: '销量',
          type: 'bar',
          data: values,
          barWidth: 16
        }
      ]
    })
  }
}

const resizeCharts = () => {
  salesTrendChart?.resize()
  orderStatusChart?.resize()
  customerLevelChart?.resize()
  topProductsChart?.resize()
}

// 构建 AI 结果（演示版结构化分析）。
const buildAIResult = (type: AIType): DashboardAIResult => {
  const salesTotal = filteredOrders.value
    .filter((item) => item.status !== 'cancelled')
    .reduce((sum, item) => sum + Number(item.total_amount || 0), 0)

  if (type === 'sales') {
    return {
      summary: `当前${currentRangeLabel.value}累计销售额 ¥${salesTotal.toFixed(2)}，订单共 ${filteredOrders.value.length} 笔。`,
      sections: [
        { title: '销售概况', points: [`有效订单销售额 ¥${salesTotal.toFixed(2)}`, `订单总量 ${filteredOrders.value.length} 笔`] },
        { title: '趋势判断', points: ['近 7 天销售呈波动趋势，建议关注高峰日前后的转化率变化。'] },
        {
          title: '热销商品结论',
          points: topProductData.value.length ? topProductData.value.map((item) => `${item.product_name}（销量 ${item.quantity}）`) : ['暂无热销商品数据']
        },
        { title: '原因分析', points: ['高客单商品驱动销售额贡献，长尾商品动销偏弱。'] },
        { title: '提升建议', points: ['对 Top 商品做组合销售', '对低动销商品做限时活动验证需求'] }
      ]
    }
  }

  if (type === 'risk') {
    return {
      summary: `当前识别风险订单 ${riskOrders.value.length} 笔，低库存商品 ${lowStockProducts.value.length} 个。`,
      sections: [
        { title: '风险订单情况', points: riskOrders.value.length ? riskOrders.value.map((item) => `${item.order_no}：${item.risk_reason}`) : ['暂无明显风险订单'] },
        { title: '库存风险', points: lowStockProducts.value.length ? lowStockProducts.value.map((item) => `${item.name} 库存 ${item.stock_qty}`) : ['暂无库存风险'] },
        {
          title: '客户风险',
          points: pendingFollowCustomers.value.length ? pendingFollowCustomers.value.map((item) => `${item.name} 已超期 ${item.overdue_days} 天未跟进`) : ['暂无明显客户风险']
        },
        { title: '优先处理建议', points: ['优先处理高风险订单与缺货商品', '对超期客户设定 24 小时内回访任务'] }
      ]
    }
  }

  if (type === 'customer') {
    const highValue = filteredCustomers.value.filter((item) => ['vip', 'strategic'].includes(item.level))
    return {
      summary: `高价值客户 ${highValue.length} 个，待跟进客户 ${pendingFollowCustomers.value.length} 个。`,
      sections: [
        {
          title: '待重点跟进客户',
          points: pendingFollowCustomers.value.length ? pendingFollowCustomers.value.map((item) => `${item.name}（超期 ${item.overdue_days} 天）`) : ['暂无待重点跟进客户']
        },
        {
          title: '高价值客户建议',
          points: highValue.length ? highValue.slice(0, 5).map((item) => `${item.name}：建议进行季度经营复盘`) : ['暂无高价值客户']
        },
        {
          title: '可能流失客户提醒',
          points: filteredCustomers.value.filter((item) => item.status === 'lost').slice(0, 5).map((item) => `${item.name}`) || ['暂无流失客户']
        },
        { title: '推荐动作', points: ['建立高价值客户周度触达机制', '对超期客户自动派发跟进任务'] }
      ]
    }
  }

  return {
    summary: `当前低库存商品 ${lowStockProducts.value.length} 个，缺货商品 ${products.value.filter((item) => item.stock_qty <= 0).length} 个。`,
    sections: [
      {
        title: '缺货商品',
        points: products.value.filter((item) => item.stock_qty <= 0).slice(0, 6).map((item) => `${item.name}`) || ['暂无缺货商品']
      },
      {
        title: '低库存商品',
        points: lowStockProducts.value.length ? lowStockProducts.value.map((item) => `${item.name}（库存 ${item.stock_qty}）`) : ['暂无低库存商品']
      },
      {
        title: '建议补货商品',
        points: topProductData.value.slice(0, 3).map((item) => `${item.product_name}（建议优先补货）`) || ['暂无建议补货商品']
      },
      { title: '处理建议', points: ['按销量 Top 商品优先补货', '设置低库存阈值自动提醒并联动采购'] }
    ]
  }
}

const generateAI = async (type: AIType) => {
  aiLoadingMap[type] = true
  try {
    await new Promise((resolve) => setTimeout(resolve, 350))
    aiResults[type] = buildAIResult(type)
    aiGeneratedAt[type] = new Date().toLocaleString('zh-CN')
    persistAIResults()
    message.success('AI 分析已更新')
  } catch (_error) {
    message.error('AI 分析生成失败')
  } finally {
    aiLoadingMap[type] = false
  }
}

const buildAIText = (type: AIType) => {
  const result = aiResults[type]
  if (!result) return ''
  const cardTitle = aiCards.find((item) => item.type === type)?.title || 'AI 结果'
  const sections = result.sections.flatMap((section) => [section.title, ...section.points.map((point, idx) => `${idx + 1}. ${point}`)])
  return [`【${cardTitle}】`, `分析时间：${aiGeneratedAt[type] || '-'}`, result.summary, ...sections].join('\n')
}

const copyAIResult = async (type: AIType) => {
  const text = buildAIText(type)
  if (!text) {
    message.warning('暂无可复制结果')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    message.success('AI 结果已复制')
  } catch (_error) {
    message.error('复制失败，请手动复制')
  }
}

// 时间范围切换：使用已加载数据快速重算，避免频繁请求接口。
const handleTimeRangeChange = async () => {
  pageLoading.value = true
  try {
    await buildTopProducts()
    await renderCharts()
    dashboardRefreshedAt.value = new Date().toLocaleString('zh-CN')
  } finally {
    pageLoading.value = false
  }
}

// 刷新看板：强制拉取最新业务数据并重新聚合。
const refreshDashboard = async () => {
  pageLoading.value = true
  try {
    await Promise.all([fetchCustomers(), fetchProducts(), fetchOrders()])
    await buildTopProducts()
    await renderCharts()
    dashboardRefreshedAt.value = new Date().toLocaleString('zh-CN')
    message.success('看板数据已刷新')
  } catch (_error) {
    message.error('看板数据加载失败，请稍后重试')
  } finally {
    pageLoading.value = false
  }
}

onMounted(async () => {
  restorePersistedAIResults()
  await refreshDashboard()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  salesTrendChart?.dispose()
  orderStatusChart?.dispose()
  customerLevelChart?.dispose()
  topProductsChart?.dispose()
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.refresh-meta {
  color: #999;
  font-size: 12px;
}

.metric-card :deep(.n-card__content) {
  min-height: 56px;
  display: flex;
  align-items: center;
}

.metric-card :deep(.n-card-header__main) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.2;
  color: #222;
  width: 100%;
  white-space: nowrap;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.ai-card {
  min-height: 280px;
}

.ai-meta {
  margin-bottom: 8px;
  color: #999;
  font-size: 12px;
}

.ai-summary {
  color: #333;
  line-height: 1.7;
}

.ai-section-title {
  margin-top: 4px;
  margin-bottom: 4px;
  font-weight: 600;
  color: #333;
}

.ai-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.7;
  color: #333;
}
</style>
