<template>
  <div class="customer-detail-page">
    <n-card title="客户详情" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button :loading="multiAgentLoading" @click="handleRunMultiAgentAnalysis">{{ multiAgentButtonText }}</n-button>
          <n-button @click="handleRefresh">刷新</n-button>
          <n-button tertiary @click="goBack">返回</n-button>
        </n-space>
      </template>

      <n-spin :show="detailLoading">
        <template v-if="detail">
          <n-grid :cols="24" :x-gap="12" :y-gap="12" class="overview-grid">
            <n-gi :span="6">
              <n-card size="small" title="客户等级">
                <n-tag :type="getCustomerLevelTagType(detail.level)">{{ getCustomerLevelLabel(detail.level) }}</n-tag>
              </n-card>
            </n-gi>
            <n-gi :span="6">
              <n-card size="small" title="跟进状态">
                <n-tag :type="getCustomerStatusTagType(detail.status)">{{ getCustomerStatusLabel(detail.status) }}</n-tag>
              </n-card>
            </n-gi>
            <n-gi :span="6">
              <n-card size="small" title="最近跟进时间">
                <div class="overview-text">{{ detail.last_follow_at || '-' }}</div>
              </n-card>
            </n-gi>
            <n-gi :span="3">
              <n-card size="small" title="跟进次数">
                <n-statistic :value="followCountValue" />
              </n-card>
            </n-gi>
            <n-gi :span="3">
              <n-card size="small" title="重点客户">
                <n-tag :type="isKeyCustomer ? 'warning' : 'default'">{{ isKeyCustomer ? '是' : '否' }}</n-tag>
              </n-card>
            </n-gi>
          </n-grid>

          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="客户编号">{{ detail.id }}</n-descriptions-item>
            <n-descriptions-item label="客户名称">{{ detail.name }}</n-descriptions-item>
            <n-descriptions-item label="联系人">{{ detail.contact_name || '-' }}</n-descriptions-item>
            <n-descriptions-item label="负责人">{{ detail.owner_name || '-' }}</n-descriptions-item>
            <n-descriptions-item label="手机号">{{ detail.phone }}</n-descriptions-item>
            <n-descriptions-item label="邮箱">{{ detail.email || '-' }}</n-descriptions-item>
            <n-descriptions-item label="公司">{{ detail.company || '-' }}</n-descriptions-item>
            <n-descriptions-item label="来源">{{ getCustomerSourceLabel(detail.source) }}</n-descriptions-item>
            <n-descriptions-item label="创建时间">{{ detail.created_at }}</n-descriptions-item>
            <n-descriptions-item label="更新时间">{{ detail.updated_at }}</n-descriptions-item>
            <n-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</n-descriptions-item>
          </n-descriptions>
        </template>
        <n-empty v-else description="暂无客户信息" />
      </n-spin>
    </n-card>

    <n-card title="客户关联订单" :bordered="false">
      <template #header-extra>
        <n-tag size="small" type="info">轻量联动展示</n-tag>
      </template>

      <n-spin :show="relatedOrderLoading">
        <n-grid :cols="24" :x-gap="12" :y-gap="12" class="order-overview-grid">
          <n-gi :span="6">
            <n-card size="small" title="关联订单数">
              <div class="summary-text">{{ relatedOrderSummary.count }}</div>
            </n-card>
          </n-gi>
          <n-gi :span="6">
            <n-card size="small" title="累计消费金额">
              <div class="summary-text">¥{{ Number(relatedOrderSummary.totalAmount || 0).toFixed(2) }}</div>
            </n-card>
          </n-gi>
          <n-gi :span="6">
            <n-card size="small" title="最近下单时间">
              <div class="overview-text">{{ relatedOrderSummary.latestOrderAt || '-' }}</div>
            </n-card>
          </n-gi>
          <n-gi :span="6">
            <n-card size="small" title="已完成订单数">
              <div class="summary-text">{{ relatedOrderSummary.completedCount }}</div>
            </n-card>
          </n-gi>
        </n-grid>

        <n-data-table
          :columns="relatedOrderColumns"
          :data="recentRelatedOrders"
          :pagination="false"
          :locale="{ emptyText: '暂无关联订单' }"
        />
      </n-spin>
    </n-card>

    <n-card title="跟进记录" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-input
            v-model:value="followFilters.keyword"
            placeholder="请输入跟进内容/结果关键词"
            clearable
            @keyup.enter="handleFollowSearch"
          />
          <n-select
            v-model:value="followFilters.follow_type"
            :options="followTypeOptions"
            placeholder="跟进类型"
            clearable
            style="width: 150px"
          />
          <n-button @click="handleFollowSearch">搜索</n-button>
          <n-button type="primary" @click="openCreateFollow">新增跟进记录</n-button>
        </n-space>
      </template>

      <n-spin :show="followLoading">
        <n-empty v-if="!followList.length" description="暂无跟进记录，点击右上角新增跟进记录" />
        <n-timeline v-else>
          <n-timeline-item v-for="item in followList" :key="item.id" :time="safeText(item.created_at)" type="info">
            <div class="timeline-card">
              <div class="timeline-head">
                <n-space align="center" :size="8">
                  <n-tag size="small" :type="getFollowTypeTagType(item.follow_type || '')">
                    {{ getFollowTypeLabel(item.follow_type || '') }}
                  </n-tag>
                  <n-tag v-if="item.source_type === 'ai_adopted'" size="small" type="success">AI采纳</n-tag>
                  <span class="timeline-user">跟进人：{{ item.follow_user_name || '-' }}</span>
                </n-space>
                <n-space>
                  <n-button size="small" tertiary type="primary" @click="openEditFollow(item)">编辑</n-button>
                  <n-popconfirm @positive-click="handleDeleteFollow(item.id)">
                    <template #trigger>
                      <n-button size="small" tertiary type="error">删除</n-button>
                    </template>
                    确认删除该跟进记录吗？
                  </n-popconfirm>
                </n-space>
              </div>

              <div class="timeline-line"><span class="line-label">跟进时间：</span>{{ safeText(item.created_at) }}</div>
              <div class="timeline-line"><span class="line-label">跟进内容：</span>{{ safeText(item.content) }}</div>
              <div class="timeline-line"><span class="line-label">跟进结果：</span>{{ safeText(item.result) }}</div>
              <div class="timeline-line"><span class="line-label">下次跟进时间：</span>{{ safeText(item.next_follow_time) }}</div>
            </div>
          </n-timeline-item>
        </n-timeline>
      </n-spin>

      <div class="pagination-area" v-if="followPagination.total > 0">
        <n-pagination
          v-model:page="followPagination.page"
          v-model:page-size="followPagination.pageSize"
          :item-count="followPagination.total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          @update:page="fetchFollowList"
          @update:page-size="handleFollowPageSizeChange"
        />
      </div>
    </n-card>

    <div ref="aiPanelsRef" class="ai-panels">
      <n-card title="AI 多Agent分析（主流程）" :bordered="true" class="ai-panel-card">
        <AiAnalysisPanel
          scene-type="customer"
          :loading="multiAgentLoading"
          :result="multiAgentResult"
          :error="multiAgentError"
          @retry="handleRunMultiAgentAnalysis"
          @task-created="handleTaskCreated"
        />
        <div v-if="hasFollowAdvice" class="ai-adopt-area">
          <n-button
            type="primary"
            :loading="adoptingFollowAdvice"
            :disabled="adoptingFollowAdvice || isCurrentAdviceAdopted"
            @click="handleAdoptFollowAdvice"
          >
            {{ isCurrentAdviceAdopted ? '已采纳' : '采纳为跟进记录' }}
          </n-button>
        </div>
      </n-card>

    </div>

    <n-card title="关联任务" :bordered="false">
      <template #header-extra>
        <n-tag size="small" type="info">AI 确认任务闭环</n-tag>
      </template>
      <n-spin :show="taskLoading">
        <n-empty v-if="!customerTasks.length" description="暂无关联任务" />
        <n-data-table
          v-else
          :columns="taskColumns"
          :data="customerTasks"
          :pagination="false"
          :locale="{ emptyText: '暂无关联任务' }"
        />
      </n-spin>
    </n-card>

    <n-card title="操作记录" :bordered="false">
      <n-data-table
        :columns="operationLogColumns"
        :data="operationLogs"
        :pagination="false"
        :locale="{ emptyText: '暂无操作记录' }"
        :row-key="(row: OperationLogItem) => `${row.type}-${row.time}-${row.content}`"
      />
    </n-card>

    <n-modal v-model:show="followModalVisible" preset="card" :title="followModalTitle" style="width: 680px">
      <n-form ref="followFormRef" :model="followForm" :rules="followRules" label-placement="left" label-width="100">
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="跟进类型" path="follow_type">
            <n-select v-model:value="followForm.follow_type" :options="followTypeOptions" placeholder="请选择跟进类型" />
          </n-form-item-gi>
          <n-form-item-gi label="下次跟进时间" path="next_follow_time">
            <n-date-picker
              v-model:value="nextFollowTimeValue"
              type="datetime"
              format="yyyy-MM-dd HH:mm"
              :time-picker-props="followTimePickerProps"
              clearable
              style="width: 100%"
            />
          </n-form-item-gi>
          <n-form-item-gi label="跟进结果" path="result" :span="2">
            <n-input v-model:value="followForm.result" placeholder="请输入跟进结果" />
          </n-form-item-gi>
          <n-form-item-gi label="跟进内容" path="content" :span="2">
            <n-input v-model:value="followForm.content" type="textarea" :rows="4" placeholder="请输入跟进内容" />
          </n-form-item-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="followModalVisible = false">取消</n-button>
          <n-button type="primary" :loading="followSubmitLoading" @click="handleSubmitFollow">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
// 客户详情页：增强客户概览、跟进闭环、AI 结构化结果和订单联动展示。
import { computed, h, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NForm,
  NFormItemGi,
  NGi,
  NGrid,
  NInput,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NStatistic,
  NTag,
  NTimeline,
  NTimelineItem,
  useMessage,
  type DataTableColumns,
  type FormInst,
  type FormRules
} from 'naive-ui'
import {
  customerDetailApi,
  customerFollowRecordCreateApi,
  customerFollowRecordDeleteApi,
  customerFollowRecordListApi,
  customerFollowRecordUpdateApi,
  type CustomerFollowRecordItem,
  type CustomerFollowRecordPayload,
  type CustomerItem
} from '@/api/customer'
import { aiChatApi, getAiRequestErrorMessage } from '@/api/ai'
import AiAnalysisPanel from '@/components/ai/AiAnalysisPanel.vue'
import { orderListApi, type OrderListItem } from '@/api/order'
import { taskListApi, type TaskDetail } from '@/api/task'
import type { AIChatResult } from '@/types/ai'
import {
  FOLLOW_TYPE_OPTIONS,
  getCustomerLevelLabel,
  getCustomerLevelTagType,
  getCustomerSourceLabel,
  getCustomerStatusLabel,
  getCustomerStatusTagType,
  getFollowTypeLabel,
  getFollowTypeTagType,
  getOrderStatusLabel,
  getOrderStatusTagType
} from '@/constants/enums'

type OperationLogItem = {
  type: string
  content: string
  operator: string
  time: string
}

// 客户详情页本地持久化结构：按客户维度保存 AI 结果与操作记录。
type CustomerDetailPersistedState = {
  // 旧版基础 AI 结果已清理，当前仅保留详情页演示操作日志的本地持久化。
  operationLogs: OperationLogItem[]
}

const CUSTOMER_DETAIL_STORAGE_KEY = 'ai_erp_customer_detail_persist_v1'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 页面加载与提交加载状态
const detailLoading = ref(false)
const followLoading = ref(false)
const followSubmitLoading = ref(false)
const multiAgentLoading = ref(false)
const adoptingFollowAdvice = ref(false)
const relatedOrderLoading = ref(false)
const taskLoading = ref(false)

// 客户详情与跟进记录列表数据
const detail = ref<CustomerItem | null>(null)
const followList = ref<CustomerFollowRecordItem[]>([])
const multiAgentResult = ref<AIChatResult | null>(null)
const multiAgentError = ref('')
const adoptedFollowAdviceKeys = ref<string[]>([])

// 关联订单与操作记录
const relatedOrders = ref<OrderListItem[]>([])
const customerTasks = ref<TaskDetail[]>([])
const operationLogs = ref<OperationLogItem[]>([])

// 读取本地持久化映射。
const getPersistedMap = (): Record<number, CustomerDetailPersistedState> => {
  try {
    const raw = localStorage.getItem(CUSTOMER_DETAIL_STORAGE_KEY)
    if (!raw) return {}
    return JSON.parse(raw) as Record<number, CustomerDetailPersistedState>
  } catch (_error) {
    return {}
  }
}

// 写入本地持久化映射。
const setPersistedMap = (map: Record<number, CustomerDetailPersistedState>) => {
  localStorage.setItem(CUSTOMER_DETAIL_STORAGE_KEY, JSON.stringify(map))
}

// 跟进记录表单与弹窗状态
const followFormRef = ref<FormInst | null>(null)
const followModalVisible = ref(false)
const editingFollowId = ref<number | null>(null)
const nextFollowTimeValue = ref<number | null>(null)
const aiPanelsRef = ref<HTMLElement | null>(null)

const followTypeOptions = FOLLOW_TYPE_OPTIONS
const followTimePickerProps = {
  format: 'HH:mm'
}

const followFilters = reactive({
  keyword: '',
  follow_type: null as string | null
})

const followPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 跟进记录表单状态
const followForm = reactive<CustomerFollowRecordPayload>({
  customer_id: 0,
  follow_type: 'call',
  content: '',
  result: '',
  next_follow_time: null
})

const followRules: FormRules = {
  follow_type: [{ required: true, message: '请选择跟进类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入跟进内容', trigger: 'blur' }]
}

const followModalTitle = computed(() => (editingFollowId.value ? '编辑跟进记录' : '新增跟进记录'))
const customerId = computed(() => Number(route.params.id) || 0)
// 跟进次数展示：优先使用接口总数，缺失时回退当前列表长度。
const followCountValue = computed(() => Number(followPagination.total || 0) || followList.value.length || 0)

// 重点客户判断：VIP 与战略客户视为重点客户。
const isKeyCustomer = computed(() => detail.value?.level === 'vip' || detail.value?.level === 'strategic')

// 从 AI 结果中提取客户洞察数据，用于拼装“AI 建议采纳”跟进记录。
const customerInsightData = computed<Record<string, any>>(() => {
  const data = multiAgentResult.value?.agent_outputs?.customer_insight_agent
  return data && typeof data === 'object' ? (data as Record<string, any>) : {}
})

// 从 AI 结果中提取跟进策略数据，作为采纳为跟进记录的核心来源。
const followAdviceData = computed<Record<string, any>>(() => {
  const data = multiAgentResult.value?.agent_outputs?.followup_strategy_agent
  return data && typeof data === 'object' ? (data as Record<string, any>) : {}
})

// 判断当前 AI 结果是否包含可采纳的跟进建议。
const hasFollowAdvice = computed(() => {
  const data = followAdviceData.value
  return !!(data.strategy_summary || data.next_action || data.communication_script || data.recommended_follow_up_time)
})

// 当前 AI 建议指纹：用于防止同一条建议被重复采纳。
const currentFollowAdviceKey = computed(() => {
  if (!hasFollowAdvice.value) return ''
  return JSON.stringify({
    customer_id: customerId.value,
    intent_level: customerInsightData.value.intent_level || '',
    main_concerns: customerInsightData.value.main_concerns || '',
    next_action: followAdviceData.value.next_action || '',
    communication_script: followAdviceData.value.communication_script || '',
    recommended_follow_up_time: followAdviceData.value.recommended_follow_up_time || ''
  })
})

// 当前 AI 建议是否已经采纳成功。
const isCurrentAdviceAdopted = computed(() => {
  const key = currentFollowAdviceKey.value
  return !!key && adoptedFollowAdviceKeys.value.includes(key)
})

// 关联订单统计信息。
const relatedOrderSummary = computed(() => {
  const list = relatedOrders.value
  const totalAmount = list.reduce((sum, item) => sum + Number(item.total_amount || 0), 0)
  const completedCount = list.filter((item) => item.status === 'completed').length
  const latestOrderAt = list.length ? list[0].created_at : ''
  return {
    count: list.length,
    totalAmount,
    completedCount,
    latestOrderAt
  }
})

const recentRelatedOrders = computed(() => relatedOrders.value.slice(0, 5))

const getTaskStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return map[status] || status || '-'
}

const getTaskStatusTagType = (status: string): 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error' => {
  if (status === 'pending') return 'warning'
  if (status === 'processing') return 'info'
  if (status === 'completed') return 'success'
  if (status === 'cancelled') return 'default'
  return 'default'
}

const getTaskPriorityTagType = (priority: string): 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error' => {
  if (priority === '高') return 'error'
  if (priority === '中') return 'warning'
  if (priority === '低') return 'success'
  return 'default'
}

// 多 Agent 按钮文案：清理旧版基础 AI 后，详情页只保留新版统一分析入口。
const multiAgentButtonText = computed(() => (multiAgentResult.value ? '重新多Agent分析' : 'AI 多Agent分析'))

const relatedOrderColumns: DataTableColumns<OrderListItem> = [
  { title: '订单编号', key: 'order_no', minWidth: 180 },
  {
    title: '状态',
    key: 'status',
    width: 110,
    render: (row) => h(NTag, { size: 'small', type: getOrderStatusTagType(row.status) }, { default: () => getOrderStatusLabel(row.status) })
  },
  {
    title: '金额',
    key: 'total_amount',
    width: 120,
    render: (row) => `¥${Number(row.total_amount || 0).toFixed(2)}`
  },
  { title: '下单时间', key: 'created_at', minWidth: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 90,
    render: (row) =>
      h(
        NButton,
        { size: 'small', tertiary: true, type: 'primary', onClick: () => router.push(`/order/detail/${row.id}`) },
        { default: () => '查看' }
      )
  }
]

const operationLogColumns: DataTableColumns<OperationLogItem> = [
  { title: '操作类型', key: 'type', width: 120 },
  { title: '操作内容', key: 'content', minWidth: 240 },
  { title: '操作人', key: 'operator', width: 120 },
  { title: '操作时间', key: 'time', width: 180 }
]

const taskColumns: DataTableColumns<TaskDetail> = [
  { title: '任务标题', key: 'title', minWidth: 180 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => h(NTag, { size: 'small', type: getTaskStatusTagType(row.status) }, { default: () => getTaskStatusLabel(row.status) })
  },
  {
    title: '优先级',
    key: 'priority',
    width: 100,
    render: (row) => h(NTag, { size: 'small', type: getTaskPriorityTagType(row.priority) }, { default: () => row.priority || '-' })
  },
  { title: '负责人', key: 'owner', width: 120 },
  { title: '截止时间', key: 'due_time', minWidth: 160 },
  { title: '创建时间', key: 'created_at', minWidth: 160 }
]

// 保存当前客户详情页可持久化数据。
const persistCurrentCustomerDetailState = () => {
  if (!customerId.value) return
  const map = getPersistedMap()
  map[customerId.value] = {
    // 旧版基础 AI 状态已移除，本地只保存操作日志。
    operationLogs: operationLogs.value
  }
  setPersistedMap(map)
}

// 按客户编号恢复持久化数据（刷新后回显）。
const restorePersistedCustomerDetailState = () => {
  if (!customerId.value) return
  const map = getPersistedMap()
  const persisted = map[customerId.value]
  if (!persisted) return

  // 旧版基础 AI 状态已移除，刷新时只恢复演示操作日志。
  operationLogs.value = Array.isArray(persisted.operationLogs) ? persisted.operationLogs : []
}

// 追加操作日志（演示版轻量审计）：统一记录关键操作并立即持久化。
const appendOperationLog = (type: string, content: string) => {
  operationLogs.value.unshift({
    type,
    content,
    operator: '当前用户',
    time: new Date().toLocaleString('zh-CN')
  })
  // 控制日志数量，避免本地存储无限增长。
  operationLogs.value = operationLogs.value.slice(0, 200)
  persistCurrentCustomerDetailState()
}

// 将空字符串和 null 统一展示为 '-'
const safeText = (value?: string | null): string => {
  if (!value) return '-'
  const text = String(value).trim()
  return text || '-'
}

// 将 AI 返回的字符串、数组或对象统一转成可读文本，供跟进记录内容复用。
const aiValueToText = (value: unknown): string => {
  if (value == null || value === '') return '-'
  if (typeof value === 'string') return value.trim() || '-'
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) {
    const list = value.map((item) => aiValueToText(item)).filter((item) => item && item !== '-')
    return list.length ? list.join('；') : '-'
  }
  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>
    if (obj.label) return aiValueToText(obj.label)
    if (obj.name) return aiValueToText(obj.name)
    const list = Object.values(obj).map((item) => aiValueToText(item)).filter((item) => item && item !== '-')
    return list.length ? list.join('；') : '-'
  }
  return String(value)
}

// 将后端日期字符串解析为时间戳，供日期组件使用。
const parseDateTimeToTimestamp = (value?: string | null): number | null => {
  if (!value) return null
  const normalized = value.replace(' ', 'T')
  const timestamp = new Date(normalized).getTime()
  return Number.isNaN(timestamp) ? null : timestamp
}

// 将时间戳格式化为 yyyy-MM-dd HH:mm:ss，秒固定为 00。
const formatTimestampToDateTimeMinute = (value: number | null): string | null => {
  if (!value) return null
  const d = new Date(value)
  const y = d.getFullYear()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  const hh = `${d.getHours()}`.padStart(2, '0')
  const mm = `${d.getMinutes()}`.padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}:00`
}

// 尝试将 AI 建议的下次跟进时间规范化为后端可接收的日期时间字符串。
const normalizeAiNextFollowTime = (value: unknown): string | null => {
  const text = aiValueToText(value)
  if (!text || text === '-') return null
  const directTimestamp = parseDateTimeToTimestamp(text)
  if (directTimestamp) return formatTimestampToDateTimeMinute(directTimestamp)
  const matched = text.match(/\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?/)
  if (!matched) return null
  return formatTimestampToDateTimeMinute(parseDateTimeToTimestamp(matched[0]))
}

// 将当前 AI 跟进建议拼装成跟进记录内容，确保格式稳定便于面试演示。
const buildAiAdoptFollowContent = (): string => {
  const insight = customerInsightData.value
  const advice = followAdviceData.value
  return [
    '【AI 建议采纳】',
    `客户意向判断：${aiValueToText(insight.intent_level || insight.customer_stage)}`,
    `当前关注点：${aiValueToText(insight.main_concerns || insight.risks)}`,
    `下一步跟进建议：${aiValueToText(advice.next_action || advice.strategy_summary)}`,
    `推荐沟通话术：${aiValueToText(advice.communication_script)}`,
    `建议下次跟进时间：${aiValueToText(advice.recommended_follow_up_time)}`
  ].join('\n')
}

// 重置跟进表单，避免新增/编辑状态串扰。
const resetFollowForm = () => {
  editingFollowId.value = null
  followForm.customer_id = customerId.value
  followForm.follow_type = 'call'
  followForm.content = ''
  followForm.result = ''
  followForm.next_follow_time = null
  nextFollowTimeValue.value = null
}

// 获取客户详情
const fetchDetail = async () => {
  if (!customerId.value) {
    message.error('客户编号无效')
    return
  }

  detailLoading.value = true
  try {
    const res = await customerDetailApi(customerId.value)
    if (res.data.code !== 0) {
      message.error(res.data.message || '获取客户详情失败')
      return
    }
    detail.value = res.data.data
  } catch (_error) {
    message.error('客户详情请求失败')
  } finally {
    detailLoading.value = false
  }
}

// 获取当前客户的跟进记录列表
const fetchFollowList = async () => {
  if (!customerId.value) return

  followLoading.value = true
  try {
    const res = await customerFollowRecordListApi({
      customer_id: customerId.value,
      keyword: followFilters.keyword.trim(),
      follow_type: followFilters.follow_type || '',
      page: followPagination.page,
      page_size: followPagination.pageSize
    })

    if (res.data.code !== 0) {
      message.error(res.data.message || '获取跟进记录失败')
      return
    }

    const list = res.data?.data?.list
    followList.value = Array.isArray(list) ? list : []
    followPagination.total = Number(res.data?.data?.total || 0)
  } catch (_error) {
    message.error('跟进记录请求失败')
  } finally {
    followLoading.value = false
  }
}

// 获取客户关联订单信息：当前后端未提供按客户过滤接口，先以前端过滤演示。
const fetchRelatedOrders = async () => {
  if (!customerId.value) return

  relatedOrderLoading.value = true
  try {
    const pageSize = 100
    let page = 1
    let finished = false
    const orders: OrderListItem[] = []

    while (!finished) {
      const res = await orderListApi({ keyword: '', status: '', page, page_size: pageSize })
      if (res.data.code !== 0) {
        message.error(res.data.message || '关联订单加载失败')
        break
      }

      const rows = (res.data?.data?.list || []) as OrderListItem[]
      orders.push(...rows.filter((item) => item.customer_id === customerId.value))
      if (rows.length < pageSize || page >= 10) {
        finished = true
      } else {
        page += 1
      }
    }

    relatedOrders.value = orders.sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))
  } catch (_error) {
    message.error('关联订单请求失败')
  } finally {
    relatedOrderLoading.value = false
  }
}

// 获取当前客户关联任务列表：展示 AI 确认创建后的真实任务。
const fetchCustomerTasks = async () => {
  if (!customerId.value) return

  taskLoading.value = true
  try {
    const res = await taskListApi({ customer_id: customerId.value })
    if (res.data.code !== 0) {
      message.error(res.data.message || '关联任务加载失败')
      return
    }
    customerTasks.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (_error) {
    message.error('关联任务请求失败')
  } finally {
    taskLoading.value = false
  }
}

const handleFollowSearch = async () => {
  followPagination.page = 1
  await fetchFollowList()
}

const handleFollowPageSizeChange = async (size: number) => {
  followPagination.pageSize = size
  followPagination.page = 1
  await fetchFollowList()
}

const openCreateFollow = () => {
  resetFollowForm()
  followModalVisible.value = true
}

// 打开编辑弹窗并回填当前记录
const openEditFollow = (item: CustomerFollowRecordItem) => {
  editingFollowId.value = item.id
  followForm.customer_id = item.customer_id
  followForm.follow_type = item.follow_type || 'call'
  followForm.content = item.content || ''
  followForm.result = item.result || ''
  followForm.next_follow_time = item.next_follow_time || null
  nextFollowTimeValue.value = parseDateTimeToTimestamp(item.next_follow_time)
  followModalVisible.value = true
}

// 提交新增/编辑跟进记录
const handleSubmitFollow = async () => {
  await followFormRef.value?.validate()

  followSubmitLoading.value = true
  try {
    const payload: CustomerFollowRecordPayload = {
      customer_id: customerId.value,
      follow_type: followForm.follow_type,
      content: followForm.content,
      result: followForm.result,
      next_follow_time: formatTimestampToDateTimeMinute(nextFollowTimeValue.value)
    }

    const res = editingFollowId.value
      ? await customerFollowRecordUpdateApi({ ...payload, id: editingFollowId.value })
      : await customerFollowRecordCreateApi(payload)

    if (res.data.code !== 0) {
      message.error(res.data.message || '保存跟进记录失败')
      return
    }

    message.success(editingFollowId.value ? '更新跟进记录成功' : '新增跟进记录成功')
    appendOperationLog('跟进记录', editingFollowId.value ? '编辑了一条跟进记录' : '新增了一条跟进记录')
    followModalVisible.value = false
    await fetchFollowList()
    await fetchDetail()
  } catch (_error) {
    message.error('保存跟进记录请求失败')
  } finally {
    followSubmitLoading.value = false
  }
}

// 将当前 AI 跟进建议一键采纳为客户跟进记录。
const handleAdoptFollowAdvice = async () => {
  if (!customerId.value || !hasFollowAdvice.value || isCurrentAdviceAdopted.value || adoptingFollowAdvice.value) return

  adoptingFollowAdvice.value = true
  try {
    const payload: CustomerFollowRecordPayload = {
      customer_id: customerId.value,
      follow_type: 'other',
      content: buildAiAdoptFollowContent(),
      result: '已采纳 AI 跟进建议',
      next_follow_time: normalizeAiNextFollowTime(followAdviceData.value.recommended_follow_up_time),
      // AI 采纳闭环显式标记来源，便于后续统计与审计区分手动跟进记录。
      source_type: 'ai_adopted',
      source_module: 'customer_ai'
    }
    const res = await customerFollowRecordCreateApi(payload)
    if (res.data.code !== 0) {
      message.error(res.data.message || '采纳 AI 跟进建议失败')
      return
    }

    if (currentFollowAdviceKey.value) {
      adoptedFollowAdviceKeys.value = [...adoptedFollowAdviceKeys.value, currentFollowAdviceKey.value]
    }
    message.success('已采纳为跟进记录')
    appendOperationLog('AI', '采纳 AI 跟进建议为跟进记录')
    followPagination.page = 1
    await fetchFollowList()
    await fetchDetail()
  } catch (_error) {
    message.error('采纳 AI 跟进建议请求失败')
  } finally {
    adoptingFollowAdvice.value = false
  }
}

// 删除跟进记录
const handleDeleteFollow = async (id: number) => {
  try {
    const res = await customerFollowRecordDeleteApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || '删除跟进记录失败')
      return
    }

    message.success('删除跟进记录成功')
    appendOperationLog('跟进记录', '删除了一条跟进记录')
    if (followList.value.length === 1 && followPagination.page > 1) {
      followPagination.page -= 1
    }
    await fetchFollowList()
    await fetchDetail()
  } catch (_error) {
    message.error('删除跟进记录请求失败')
  }
}

// 调用多 Agent 统一分析接口：用于展示可演示的计划与分步结果。
const handleRunMultiAgentAnalysis = async () => {
  if (!customerId.value) {
    message.error('客户编号无效')
    return
  }
  multiAgentLoading.value = true
  multiAgentError.value = ''
  try {
    const res = await aiChatApi({
      scene: 'customer_detail',
      // 默认演示链路需要包含“生成待办”，确保后端会执行 task_execution_agent 并返回任务草稿。
      user_message: '请分析当前客户状态，给出下一步跟进建议，并生成待办',
      context: {
        customer_id: customerId.value
      }
    })
    if (res.data.code !== 0) {
      multiAgentResult.value = null
      multiAgentError.value = res.data.message || '多 Agent 分析失败'
      message.error(multiAgentError.value)
      return
    }
    multiAgentResult.value = res.data.data as AIChatResult
    appendOperationLog('AI', '执行了 AI 多Agent分析')
    await nextTick()
    aiPanelsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    message.success('AI 多Agent分析完成')
  } catch (error) {
    multiAgentResult.value = null
    // 请求异常时展示后端返回的真实 message，便于定位鉴权、模型和服务端错误。
    multiAgentError.value = getAiRequestErrorMessage(error, '多 Agent 分析请求失败')
    message.error(multiAgentError.value)
  } finally {
    multiAgentLoading.value = false
  }
}

// AI 任务草稿确认创建成功后，刷新客户关联任务列表并记录演示操作日志。
const handleTaskCreated = async () => {
  appendOperationLog('任务', '确认创建了一条 AI 跟进任务')
  await fetchCustomerTasks()
}

const goBack = () => {
  router.push('/customer')
}

const handleRefresh = async () => {
  await fetchDetail()
  await fetchFollowList()
  await fetchRelatedOrders()
  await fetchCustomerTasks()
  // 刷新后显式恢复当前客户的本地持久化状态，避免展示态与缓存态不一致。
  restorePersistedCustomerDetailState()
  message.success('客户详情已刷新')
}

onMounted(async () => {
  await fetchDetail()
  await fetchFollowList()
  await fetchRelatedOrders()
  await fetchCustomerTasks()
  restorePersistedCustomerDetailState()

  // 支持从客户列表页“新增跟进”按钮直达详情并自动打开弹窗。
  if (route.query.action === 'create-follow') {
    openCreateFollow()
  }
})
</script>

<style scoped>
.customer-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overview-grid {
  margin-bottom: 12px;
}

.overview-grid :deep(.n-card) {
  height: 100%;
}

.overview-grid :deep(.n-card__content) {
  min-height: 56px;
  display: flex;
  align-items: center;
}

.overview-text {
  line-height: 34px;
}

.order-overview-grid {
  margin-bottom: 12px;
}

.order-overview-grid :deep(.n-card) {
  height: 100%;
}

.order-overview-grid :deep(.n-card__content) {
  min-height: 56px;
  display: flex;
  align-items: center;
}

.summary-text {
  line-height: 24px;
  font-size: 28px;
}

.timeline-card {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 12px;
  background: #fafafa;
}

.timeline-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.timeline-user {
  color: #666;
  font-size: 13px;
}

.timeline-line {
  margin-top: 6px;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.line-label {
  color: #666;
}

.pagination-area {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.ai-panels {
  display: flex;
  gap: 16px;
  /* 与下方“操作记录”卡片内容区对齐 */
  padding: 0 16px;
  box-sizing: border-box;
}

.ai-panels > * {
  flex: 1 1 0;
  min-width: 0;
}

.ai-adopt-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #edf0f5;
}

.ai-panel-card {
  border: 1px solid #d9e1ec;
  border-radius: 10px;
}

</style>
