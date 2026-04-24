<template>
  <div class="order-detail-page">
    <n-card title="订单详情" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button type="primary" tertiary @click="goEdit">编辑订单</n-button>
          <n-button @click="goList">返回列表</n-button>
        </n-space>
      </template>

      <n-spin :show="pageLoading">
        <template v-if="detailData">
          <div class="status-flow-section">
            <n-card size="small" title="订单状态流转" :bordered="false" class="inner-card">
              <template #header-extra>
                <n-tag :type="getOrderStatusTagType(detailData.status)" size="small">
                  {{ getOrderStatusLabel(detailData.status) }}
                </n-tag>
              </template>

              <n-steps :current="currentStatusStep" :status="statusStepStatus" size="small">
                <n-step
                  v-for="step in statusSteps"
                  :key="step.title"
                  :title="step.title"
                  :description="step.description"
                />
              </n-steps>

              <div class="transition-action-row">
                <n-space>
                  <n-popconfirm
                    v-for="action in transitionActions"
                    :key="action.target"
                    @positive-click="handleStatusTransition(action.target)"
                  >
                    <template #trigger>
                      <n-button tertiary :type="action.type" :loading="statusUpdating">
                        {{ action.label }}
                      </n-button>
                    </template>
                    {{ getTransitionConfirmText(action.target) }}
                  </n-popconfirm>

                  <n-tag v-if="!transitionActions.length" type="default">当前状态无可执行流转操作</n-tag>
                </n-space>
              </div>
            </n-card>
          </div>

          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="订单编号">{{ detailData.order_no }}</n-descriptions-item>
            <n-descriptions-item label="客户名称">{{ detailData.customer_name }}</n-descriptions-item>
            <n-descriptions-item label="订单状态">
              <n-tag :type="getOrderStatusTagType(detailData.status)" size="small">
                {{ getOrderStatusLabel(detailData.status) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="订单总金额">¥{{ Number(detailData.total_amount || 0).toFixed(2) }}</n-descriptions-item>
            <n-descriptions-item label="创建时间">{{ detailData.created_at || '-' }}</n-descriptions-item>
            <n-descriptions-item label="更新时间">{{ detailData.updated_at || '-' }}</n-descriptions-item>
            <n-descriptions-item label="备注" :span="2">{{ detailData.remark || '-' }}</n-descriptions-item>
          </n-descriptions>

          <n-grid :cols="24" :x-gap="12" :y-gap="12" class="fulfillment-grid">
            <n-gi :span="8">
              <n-card size="small" title="支付信息">
                <n-descriptions :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="支付方式">{{ paymentInfo.method || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="支付状态">{{ paymentInfo.status || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="交易单号">{{ paymentInfo.transaction_no || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="支付时间">{{ paymentInfo.paid_at || '-' }}</n-descriptions-item>
                </n-descriptions>
              </n-card>
            </n-gi>

            <n-gi :span="8">
              <n-card size="small" title="发货信息">
                <n-descriptions :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="发货状态">{{ shippingInfo.status || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="物流公司">{{ shippingInfo.company || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="物流单号">{{ shippingInfo.tracking_no || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="发货时间">{{ shippingInfo.shipped_at || '-' }}</n-descriptions-item>
                </n-descriptions>
              </n-card>
            </n-gi>

            <n-gi :span="8">
              <n-card size="small" title="收货信息">
                <n-descriptions :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="收货人">{{ receiverInfo.receiver_name || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="联系电话">{{ receiverInfo.receiver_phone || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="收货地址">{{ receiverInfo.receiver_address || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="签收状态">{{ receiverInfo.receive_status || '-' }}</n-descriptions-item>
                </n-descriptions>
              </n-card>
            </n-gi>
          </n-grid>
        </template>

        <n-empty v-else description="暂无订单信息" />
      </n-spin>
    </n-card>

    <n-card title="AI 多Agent订单分析（主流程）" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button :loading="multiAgentLoading" @click="handleRunOrderMultiAgentAnalysis">{{ multiAgentButtonText }}</n-button>
        </n-space>
      </template>
      <AiAnalysisPanel
        scene-type="order"
        :loading="multiAgentLoading"
        :result="multiAgentResult"
        :error="multiAgentError"
        @retry="handleRunOrderMultiAgentAnalysis"
      />
    </n-card>

    <n-card title="订单明细" :bordered="false">
      <n-data-table
        :columns="itemColumns"
        :data="detailData?.items || []"
        :pagination="false"
        :loading="pageLoading"
        :row-key="(row: OrderItem) => `${row.product_id}-${row.id || 0}`"
      />

      <n-grid :cols="24" :x-gap="12" :y-gap="12" class="summary-grid">
        <n-gi :span="4">
          <n-statistic label="商品总数" :value="summaryInfo.productCount" />
        </n-gi>
        <n-gi :span="4">
          <n-statistic label="商品总件数" :value="summaryInfo.totalQuantity" />
        </n-gi>
        <n-gi :span="5">
          <n-statistic label="订单总额" :value="summaryInfo.totalAmount" prefix="¥" :precision="2" />
        </n-gi>
        <n-gi :span="5">
          <n-statistic label="优惠金额" :value="summaryInfo.discountAmount" prefix="¥" :precision="2" />
        </n-gi>
        <n-gi :span="6">
          <n-statistic label="实付金额" :value="summaryInfo.paidAmount" prefix="¥" :precision="2" />
        </n-gi>
      </n-grid>
    </n-card>

    <n-card title="操作记录" :bordered="false">
      <n-data-table
        :columns="operationColumns"
        :data="displayOperationLogs"
        :pagination="false"
        :row-key="(row: OrderOperationLog) => `${row.operated_at}-${row.content}`"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 订单详情页：展示订单基础信息、状态流转、AI 分析、订单明细、汇总信息与操作记录。
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NGi,
  NGrid,
  NPopconfirm,
  NSpace,
  NSpin,
  NStatistic,
  NStep,
  NSteps,
  NTag,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import {
  orderDetailApi,
  orderStatusUpdateApi,
  type OrderDetail,
  type OrderItem,
  type OrderOperationLog,
  type OrderPaymentInfo,
  type OrderReceiverInfo,
  type OrderShippingInfo
} from '@/api/order'
import { aiChatApi } from '@/api/ai'
import AiAnalysisPanel from '@/components/ai/AiAnalysisPanel.vue'
import { getOrderStatusLabel, getOrderStatusTagType, getProductUnitLabel } from '@/constants/enums'
import type { AIChatResult } from '@/types/ai'
import { getOrderRuntimeState, patchOrderRuntimeState } from '@/utils/order-runtime-state'

type OrderTransitionStatus = 'confirmed' | 'completed' | 'cancelled'
type NaiveTagType = 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error'

// 订单详情页本地持久化结构：按订单维度保存 AI 结果与前端追加日志。
type OrderDetailPersistedState = {
  // 旧版基础 AI 结果已从订单详情页移除，当前仅保留本地操作日志。
  localOperationLogs: OrderOperationLog[]
}

const ORDER_DETAIL_STORAGE_KEY = 'ai_erp_order_detail_persist_v1'
const FALLBACK_LOGISTICS_COMPANY = '顺丰速运'
const FALLBACK_RECEIVER_PHONE = '13800000000'
const FALLBACK_RECEIVER_ADDRESS = '上海市浦东新区张江高科技园区'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 页面加载、状态流转按钮加载状态
const pageLoading = ref(false)
const statusUpdating = ref(false)
// 订单详情数据
const detailData = ref<OrderDetail | null>(null)
// 操作记录数据：区分“接口/回退日志”与“前端追加日志”，避免来源混淆。
const serverOperationLogs = ref<OrderOperationLog[]>([])
const localOperationLogs = ref<OrderOperationLog[]>([])

const multiAgentLoading = ref(false)
const multiAgentResult = ref<AIChatResult | null>(null)
const multiAgentError = ref('')

const orderId = computed(() => Number(route.params.id) || 0)
const multiAgentButtonText = computed(() => (multiAgentResult.value ? '重新多Agent分析' : 'AI 多Agent分析'))

// 读取本地持久化映射。
const getPersistedMap = (): Record<number, OrderDetailPersistedState> => {
  try {
    const raw = localStorage.getItem(ORDER_DETAIL_STORAGE_KEY)
    if (!raw) return {}
    return JSON.parse(raw) as Record<number, OrderDetailPersistedState>
  } catch (_error) {
    return {}
  }
}

// 写入本地持久化映射。
const setPersistedMap = (map: Record<number, OrderDetailPersistedState>) => {
  localStorage.setItem(ORDER_DETAIL_STORAGE_KEY, JSON.stringify(map))
}

// 持久化当前订单详情页演示日志；旧版基础 AI 结果已清理。
const persistCurrentOrderDetailState = () => {
  if (!orderId.value) return
  const map = getPersistedMap()
  map[orderId.value] = {
    // 只保留多 Agent 分析和状态流转产生的本地操作日志。
    localOperationLogs: localOperationLogs.value
  }
  setPersistedMap(map)
}

// 恢复当前订单本地持久化状态（刷新后回显）。
const restorePersistedOrderDetailState = () => {
  if (!orderId.value) return
  const map = getPersistedMap()
  const persisted = map[orderId.value]
  if (!persisted) return

  // 旧版基础 AI 状态已移除，刷新时只恢复演示操作日志。
  localOperationLogs.value = Array.isArray(persisted.localOperationLogs) ? persisted.localOperationLogs : []
}

// 追加前端演示日志：用于记录详情页本地操作并持久化。
const appendLocalOperationLog = (log: OrderOperationLog) => {
  localOperationLogs.value.unshift(log)
  localOperationLogs.value = localOperationLogs.value.slice(0, 200)
  persistCurrentOrderDetailState()
}

// 展示日志：前端追加日志优先，其后展示接口/回退日志，并做轻量去重。
const displayOperationLogs = computed<OrderOperationLog[]>(() => {
  const map = new Map<string, OrderOperationLog>()
  ;[...localOperationLogs.value, ...serverOperationLogs.value].forEach((log) => {
    const key = `${log.action_type}-${log.operated_at}-${log.content}`
    if (!map.has(key)) map.set(key, log)
  })
  return Array.from(map.values())
})

// 根据订单状态生成可执行按钮
const transitionActions = computed<Array<{ label: string; target: OrderTransitionStatus; type: 'info' | 'success' | 'warning' }>>(() => {
  const status = detailData.value?.status || ''
  if (status === 'draft') {
    return [
      { label: '确认订单', target: 'confirmed', type: 'info' },
      { label: '取消订单', target: 'cancelled', type: 'warning' }
    ]
  }
  if (status === 'confirmed') {
    return [
      { label: '标记完成', target: 'completed', type: 'success' },
      { label: '取消订单', target: 'cancelled', type: 'warning' }
    ]
  }
  return []
})

// 状态步骤条当前步骤
const currentStatusStep = computed(() => {
  const status = detailData.value?.status
  if (status === 'draft') return 1
  if (status === 'confirmed') return 2
  if (status === 'completed') return 3
  if (status === 'cancelled') return statusSteps.value.length
  return 1
})

// 状态步骤条的视觉状态：取消场景标记为错误，其余走正常流程
const statusStepStatus = computed<'process' | 'finish' | 'error'>(() => {
  const status = detailData.value?.status
  if (status === 'cancelled') return 'error'
  if (status === 'completed') return 'finish'
  return 'process'
})

// 状态步骤配置：取消单走“取消终态”分支，避免展示为“已完成异常”
const statusSteps = computed<Array<{ title: string; description: string }>>(() => {
  const status = detailData.value?.status
  if (status === 'cancelled') {
    return [
      { title: '草稿', description: '订单创建' },
      { title: '已取消', description: '订单终止' }
    ]
  }
  return [
    { title: '草稿', description: '订单创建' },
    { title: '已确认', description: '订单已确认' },
    { title: '已完成', description: '订单履约完成' }
  ]
})

// 统一构建演示回退展示，减少支付/发货/收货区块重复硬编码。
const getOrderBaseTime = (data: OrderDetail) => data.updated_at || data.created_at || '-'
const buildFallbackTransactionNo = (id: number) => `PAY-${id}`
const buildFallbackTrackingNo = (id: number) => `SF${String(id).padStart(8, '0')}`

// 支付信息回退构建器：后端字段缺失时用于演示展示，后续应由真实支付接口替换。
const buildFallbackPaymentInfo = (data: OrderDetail): OrderPaymentInfo => {
  const runtime = getOrderRuntimeState(data.id)
  if (runtime?.payment_status === 'paid') {
    return {
      method: '对公转账',
      status: '已支付',
      transaction_no: buildFallbackTransactionNo(data.id),
      paid_at: runtime.payment_time || getOrderBaseTime(data)
    }
  }
  if (runtime?.payment_status === 'closed') {
    return { method: '未支付', status: '交易关闭', transaction_no: '-', paid_at: '-' }
  }
  if (data.status === 'completed') {
    return { method: '对公转账', status: '已支付', transaction_no: buildFallbackTransactionNo(data.id), paid_at: getOrderBaseTime(data) }
  }
  if (data.status === 'confirmed') {
    return { method: '对公转账', status: '待支付', transaction_no: '-', paid_at: '-' }
  }
  if (data.status === 'cancelled') {
    return { method: '未支付', status: '交易关闭', transaction_no: '-', paid_at: '-' }
  }
  return { method: '未支付', status: '待支付', transaction_no: '-', paid_at: '-' }
}

// 发货信息回退构建器：后端字段缺失时用于演示展示，后续应由真实物流接口替换。
const buildFallbackShippingInfo = (data: OrderDetail): OrderShippingInfo => {
  const runtime = getOrderRuntimeState(data.id)
  if (runtime?.shipping_status === 'shipped') {
    return {
      status: '已发货',
      company: FALLBACK_LOGISTICS_COMPANY,
      tracking_no: buildFallbackTrackingNo(data.id),
      shipped_at: runtime.shipping_time || getOrderBaseTime(data)
    }
  }
  if (data.status === 'completed') {
    return {
      status: '已发货',
      company: FALLBACK_LOGISTICS_COMPANY,
      tracking_no: buildFallbackTrackingNo(data.id),
      shipped_at: getOrderBaseTime(data)
    }
  }
  if (data.status === 'confirmed') {
    return { status: '待发货', company: '-', tracking_no: '-', shipped_at: '-' }
  }
  return { status: '未发货', company: '-', tracking_no: '-', shipped_at: '-' }
}

// 收货信息回退构建器：后端字段缺失时用于演示展示，后续应由真实收货信息接口替换。
const buildFallbackReceiverInfo = (data: OrderDetail): OrderReceiverInfo => ({
  receiver_name: data.customer_name || '-',
  receiver_phone: FALLBACK_RECEIVER_PHONE,
  receiver_address: FALLBACK_RECEIVER_ADDRESS,
  receive_status: data.status === 'completed' ? '已签收' : '待签收'
})

// 支付信息：优先用后端返回，缺失时按订单状态回退 mock 数据
const paymentInfo = computed<OrderPaymentInfo>(() => {
  const data = detailData.value
  if (!data) return {}
  if (data.payment_info) return data.payment_info
  return buildFallbackPaymentInfo(data)
})

// 发货信息：优先用后端返回，缺失时按状态回退 mock 数据
const shippingInfo = computed<OrderShippingInfo>(() => {
  const data = detailData.value
  if (!data) return {}
  if (data.shipping_info) return data.shipping_info
  return buildFallbackShippingInfo(data)
})

// 收货信息：优先用后端返回，缺失时按状态回退 mock 数据
const receiverInfo = computed<OrderReceiverInfo>(() => {
  const data = detailData.value
  if (!data) return {}
  if (data.receiver_info) return data.receiver_info
  return buildFallbackReceiverInfo(data)
})

// 订单汇总信息：缺失字段通过明细和总额推导
const summaryInfo = computed(() => {
  const items = detailData.value?.items || []
  const productCount = items.length
  const totalQuantity = items.reduce((sum, item) => sum + Number(item.quantity || 0), 0)
  const totalAmount = Number(detailData.value?.total_amount || 0)
  const discountAmount = Number(detailData.value?.discount_amount ?? 0)
  const paidAmount = Number(detailData.value?.paid_amount ?? Math.max(totalAmount - discountAmount, 0))

  return {
    productCount,
    totalQuantity,
    totalAmount,
    discountAmount,
    paidAmount
  }
})

// 操作记录表格列定义
const operationColumns: DataTableColumns<OrderOperationLog> = [
  {
    title: '操作类型',
    key: 'action_type',
    width: 120,
    render: (row) => {
      const typeMap: Record<string, { label: string; tagType: NaiveTagType }> = {
        create: { label: '创建订单', tagType: 'info' },
        update: { label: '编辑订单', tagType: 'warning' },
        transition: { label: '状态流转', tagType: 'success' },
        ai_analysis: { label: 'AI 分析', tagType: 'primary' }
      }
      const target = typeMap[row.action_type] || { label: row.action_type, tagType: 'default' }
      return `${target.label}`
    }
  },
  { title: '操作内容', key: 'content', minWidth: 220 },
  { title: '操作人', key: 'operator', width: 120 },
  { title: '操作时间', key: 'operated_at', width: 180 },
  { title: '备注', key: 'remark', minWidth: 180, render: (row) => row.remark || '-' }
]

const itemColumns: DataTableColumns<OrderItem> = [
  { title: '商品名称', key: 'product_name', minWidth: 180 },
  { title: '商品编码', key: 'product_code', minWidth: 140 },
  {
    title: '单价',
    key: 'unit_price',
    width: 120,
    render: (row) => `¥${Number(row.unit_price || 0).toFixed(2)}`
  },
  { title: '数量', key: 'quantity', width: 90 },
  { title: '单位', key: 'unit', width: 90, render: (row) => getProductUnitLabel(String(row.unit || '')) },
  {
    title: '小计',
    key: 'subtotal',
    width: 120,
    render: (row) => `¥${Number(row.subtotal || 0).toFixed(2)}`
  }
]

// 状态流转确认文案
const getTransitionConfirmText = (target: OrderTransitionStatus): string => {
  if (target === 'confirmed') return '确认将该订单状态更新为“已确认”吗？'
  if (target === 'completed') return '确认将该订单状态更新为“已完成”吗？'
  return '确认将该订单状态更新为“已取消”吗？'
}

// 根据订单详情生成 mock 操作记录
const buildMockOperationLogs = (detail: OrderDetail): OrderOperationLog[] => {
  const logs: OrderOperationLog[] = [
    {
      action_type: 'create',
      content: `创建订单 ${detail.order_no}`,
      operator: '系统管理员',
      operated_at: detail.created_at || '-',
      remark: '订单初始化'
    }
  ]

  if (detail.updated_at && detail.updated_at !== detail.created_at) {
    logs.push({
      action_type: 'update',
      content: '更新订单信息',
      operator: '系统管理员',
      operated_at: detail.updated_at,
      remark: detail.remark || '-'
    })
  }

  return logs
}

// 返回订单列表页
const goList = () => {
  router.push('/order')
}

// 跳转订单编辑页（附带来源标记）
const goEdit = () => {
  const id = Number(route.params.id) || 0
  if (!id) return
  router.push({ path: `/order/edit/${id}`, query: { from: 'detail' } })
}

// 拉取订单详情数据
const fetchDetail = async () => {
  if (!orderId.value) {
    message.error('订单编号无效')
    return
  }

  pageLoading.value = true
  try {
    const res = await orderDetailApi(orderId.value)
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单详情加载失败')
      return
    }
    const detail = res.data.data as OrderDetail
    detailData.value = detail
    // 接口日志优先；缺失时回退演示日志。前端追加日志由 localOperationLogs 单独维护。
    serverOperationLogs.value = detail.operation_logs?.length ? detail.operation_logs : buildMockOperationLogs(detail)
  } catch (_error) {
    message.error('订单详情请求失败')
  } finally {
    pageLoading.value = false
  }
}

// 执行状态流转并刷新当前详情
const handleStatusTransition = async (targetStatus: OrderTransitionStatus) => {
  if (!orderId.value) return

  statusUpdating.value = true
  try {
    const res = await orderStatusUpdateApi({ id: orderId.value, status: targetStatus })
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单状态流转失败')
      return
    }

    message.success('订单状态已更新')
    detailData.value = res.data.data
    if (targetStatus === 'cancelled') {
      patchOrderRuntimeState(orderId.value, { payment_status: 'closed', shipping_status: 'unshipped' })
    }
    if (targetStatus === 'completed') {
      patchOrderRuntimeState(orderId.value, { payment_status: 'paid', shipping_status: 'shipped' })
    }
    appendLocalOperationLog({
      action_type: 'transition',
      content: `订单状态更新为${getOrderStatusLabel(targetStatus)}`,
      operator: '当前用户',
      operated_at: new Date().toLocaleString('zh-CN'),
      remark: '详情页状态流转操作'
    })
  } catch (_error) {
    message.error('订单状态流转请求失败')
  } finally {
    statusUpdating.value = false
  }
}

// 调用多 Agent 订单分析接口：返回统一 plan、summary 与 Agent 结果。
const handleRunOrderMultiAgentAnalysis = async () => {
  if (!orderId.value) {
    message.error('订单编号无效')
    return
  }
  multiAgentLoading.value = true
  multiAgentError.value = ''
  try {
    const res = await aiChatApi({
      scene: 'order_detail',
      user_message: '分析当前订单风险并给出建议',
      context: {
        order_id: orderId.value
      }
    })
    if (res.data.code !== 0) {
      multiAgentResult.value = null
      multiAgentError.value = res.data.message || '多 Agent 订单分析失败'
      message.error(multiAgentError.value)
      return
    }
    multiAgentResult.value = res.data.data as AIChatResult
    appendLocalOperationLog({
      action_type: 'ai_analysis',
      content: '执行 AI 多Agent订单分析',
      operator: '当前用户',
      operated_at: new Date().toLocaleString('zh-CN'),
      remark: '基于 /api/ai/chat'
    })
    message.success('AI 多Agent订单分析完成')
  } catch (_error) {
    multiAgentResult.value = null
    multiAgentError.value = '多 Agent 订单分析请求失败'
    message.error(multiAgentError.value)
  } finally {
    multiAgentLoading.value = false
  }
}

onMounted(async () => {
  await fetchDetail()
  restorePersistedOrderDetailState()
})
</script>

<style scoped>
.order-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 状态流转区域：与基础信息同卡片内，减少页面跳跃感 */
.status-flow-section {
  margin-bottom: 12px;
}

.inner-card {
  background: #fafafa;
}

.transition-action-row {
  margin-top: 12px;
}

.fulfillment-grid {
  margin-top: 12px;
}

.summary-grid {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
