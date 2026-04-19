<template>
  <div class="customer-detail-page">
    <n-card title="客户详情" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button :loading="aiAdviceLoading" @click="handleGenerateAdvice">AI 生成跟进建议</n-button>
          <n-button :loading="aiSummaryLoading" @click="handleGenerateSummary">AI 总结跟进记录</n-button>
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
        />
      </n-card>

      <n-card title="基础 AI 能力（兼容）" :bordered="true" class="ai-panel-card legacy-ai-card">
        <n-collapse>
          <n-collapse-item title="AI 跟进建议（旧模块）" name="legacy-advice">
            <n-card :bordered="false" class="legacy-inner-card">
              <template #header-extra>
                <n-space size="small" align="center">
                  <n-tag size="small" :type="aiAdviceResult ? 'success' : 'default'">{{ aiAdviceResult ? '已生成' : '未生成' }}</n-tag>
                  <n-button size="tiny" :loading="aiAdviceLoading" @click="handleGenerateAdvice">{{ adviceGenerateButtonText }}</n-button>
                  <n-button size="tiny" :disabled="!aiAdviceResult" @click="handleCopyAdvice">复制结果</n-button>
                </n-space>
              </template>
              <n-spin :show="aiAdviceLoading">
                <div class="ai-meta-row">分析时间：{{ aiAdviceGeneratedAt || '-' }}</div>
                <n-empty v-if="!aiAdviceResult" description="暂无 AI 跟进建议，请点击生成建议" />
                <n-space v-else vertical :size="14">
                  <div class="ai-row">
                    <span class="ai-label">客户状态判断：</span>
                    <span class="ai-value">{{ adviceStatusJudgement }}</span>
                  </div>
                  <div class="ai-row">
                    <span class="ai-label">推荐下一步动作：</span>
                  </div>
                  <ul class="ai-list">
                    <li v-for="(item, index) in adviceNextStepPoints" :key="`advice-${index}`">{{ item }}</li>
                  </ul>
                  <div class="ai-row">
                    <span class="ai-label">推荐跟进时间：</span>
                    <span class="ai-value">{{ aiAdviceResult.suggested_next_follow_time || '-' }}</span>
                  </div>
                  <div class="ai-row">
                    <span class="ai-label">推荐沟通话术：</span>
                  </div>
                  <div class="ai-talk-track">{{ aiAdviceResult.recommended_talk_track || '-' }}</div>
                  <div class="ai-row">
                    <span class="ai-label">风险提醒：</span>
                  </div>
                  <ul class="ai-list">
                    <li v-for="(item, index) in adviceRiskWarnings" :key="`advice-risk-${index}`">{{ item }}</li>
                  </ul>
                </n-space>
              </n-spin>
            </n-card>
          </n-collapse-item>

          <n-collapse-item title="AI 跟进总结（旧模块）" name="legacy-summary">
            <n-card :bordered="false" class="legacy-inner-card">
              <template #header-extra>
                <n-space size="small" align="center">
                  <n-tag size="small" :type="aiSummaryResult ? 'success' : 'default'">{{ aiSummaryResult ? '已生成' : '未生成' }}</n-tag>
                  <n-button size="tiny" :loading="aiSummaryLoading" @click="handleGenerateSummary">{{ summaryGenerateButtonText }}</n-button>
                  <n-button size="tiny" :disabled="!aiSummaryResult" @click="handleCopySummary">复制结果</n-button>
                </n-space>
              </template>
              <n-spin :show="aiSummaryLoading">
                <div class="ai-meta-row">分析时间：{{ aiSummaryGeneratedAt || '-' }}</div>
                <n-empty v-if="!aiSummaryResult" description="暂无 AI 跟进总结，请点击生成总结" />
                <n-space v-else vertical :size="14">
                  <div class="ai-row">
                    <span class="ai-label">历史跟进摘要：</span>
                  </div>
                  <ul class="ai-list">
                    <li v-for="(item, index) in summaryHistoryPoints" :key="`point-${index}`">{{ item }}</li>
                  </ul>
                  <div class="ai-row">
                    <span class="ai-label">客户关注点：</span>
                    <span class="ai-value">{{ summaryCurrentFocus }}</span>
                  </div>
                  <div class="ai-row">
                    <span class="ai-label">成交可能性判断：</span>
                    <span class="ai-value">{{ dealProbabilityText }}</span>
                  </div>
                  <div class="ai-row">
                    <span class="ai-label">当前阻塞点：</span>
                  </div>
                  <ul class="ai-list">
                    <li v-for="(item, index) in summaryRiskPoints" :key="`risk-${index}`">{{ item }}</li>
                  </ul>
                  <div class="ai-row">
                    <span class="ai-label">后续建议：</span>
                  </div>
                  <ul class="ai-list">
                    <li v-for="(item, index) in summaryFollowUpAdvice" :key="`summary-advice-${index}`">{{ item }}</li>
                  </ul>
                </n-space>
              </n-spin>
            </n-card>
          </n-collapse-item>
        </n-collapse>
      </n-card>
    </div>

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
  NCollapse,
  NCollapseItem,
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
  customerAIFollowAdviceApi,
  customerAIFollowSummaryApi,
  customerDetailApi,
  customerFollowRecordCreateApi,
  customerFollowRecordDeleteApi,
  customerFollowRecordListApi,
  customerFollowRecordUpdateApi,
  type CustomerAIFollowAdvice,
  type CustomerAIFollowSummary,
  type CustomerFollowRecordItem,
  type CustomerFollowRecordPayload,
  type CustomerItem
} from '@/api/customer'
import { aiChatApi } from '@/api/ai'
import AiAnalysisPanel from '@/components/ai/AiAnalysisPanel.vue'
import { orderListApi, type OrderListItem } from '@/api/order'
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
  aiAdviceResult: CustomerAIFollowAdvice | null
  aiSummaryResult: CustomerAIFollowSummary | null
  aiAdviceGeneratedAt: string
  aiSummaryGeneratedAt: string
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
const aiAdviceLoading = ref(false)
const aiSummaryLoading = ref(false)
const multiAgentLoading = ref(false)
const relatedOrderLoading = ref(false)

// 客户详情与跟进记录列表数据
const detail = ref<CustomerItem | null>(null)
const followList = ref<CustomerFollowRecordItem[]>([])
const aiAdviceResult = ref<CustomerAIFollowAdvice | null>(null)
const aiSummaryResult = ref<CustomerAIFollowSummary | null>(null)
const multiAgentResult = ref<AIChatResult | null>(null)
const multiAgentError = ref('')
const aiAdviceGeneratedAt = ref('')
const aiSummaryGeneratedAt = ref('')

// 关联订单与操作记录
const relatedOrders = ref<OrderListItem[]>([])
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

const adviceStatusJudgement = computed(() => {
  const intent = aiAdviceResult.value?.intent_level?.label || '中意向'
  const status = detail.value ? getCustomerStatusLabel(detail.value.status) : '-'
  return `当前客户处于“${status}”，AI 判断意向等级为“${intent}”。`
})

// AI 按钮文案：未生成时提示“生成”，已生成时提示“重新生成”。
const adviceGenerateButtonText = computed(() => (aiAdviceResult.value ? '重新生成' : '生成建议'))
const summaryGenerateButtonText = computed(() => (aiSummaryResult.value ? '重新生成' : '生成总结'))
const multiAgentButtonText = computed(() => (multiAgentResult.value ? '重新多Agent分析' : 'AI 多Agent分析'))

// 建议区动作兜底，避免接口返回空数组时出现空白区域。
const adviceNextStepPoints = computed(() => {
  const points = aiAdviceResult.value?.next_step_advice || []
  return points.length ? points : ['建议先补充关键决策信息，再推进下一步跟进动作。']
})

// 总结区历史摘要兜底：优先用总结结果，缺失时给出占位提示。
const summaryHistoryPoints = computed(() => {
  const points = aiSummaryResult.value?.history_key_points || []
  return points.length ? points : ['暂无历史跟进摘要，建议先补充最近一次沟通记录。']
})

// 总结区阻塞点兜底：优先用总结结果中的潜在风险。
const summaryRiskPoints = computed(() => {
  const points = aiSummaryResult.value?.potential_risks || []
  return points.length ? points : ['暂无明显阻塞点，可继续推进需求确认与商务沟通。']
})
const hasSummaryRiskData = computed(() => (aiSummaryResult.value?.potential_risks || []).length > 0)

// 总结区客户关注点：优先使用总结 current_progress，再回退到建议中的 current_focus。
const summaryCurrentFocus = computed(() => {
  const fromSummary = aiSummaryResult.value?.current_progress?.trim()
  if (fromSummary) return fromSummary
  const fromAdvice = aiAdviceResult.value?.current_focus?.trim()
  if (fromAdvice) return fromAdvice
  return '暂无关注点数据'
})

const adviceRiskWarnings = computed(() => {
  if (hasSummaryRiskData.value) return aiSummaryResult.value?.potential_risks || []
  const intentCode = aiAdviceResult.value?.intent_level?.code
  if (intentCode === 'high') return ['风险可控，建议持续推进采购与决策流程。']
  if (intentCode === 'low') return ['客户意向偏低，需防止沟通中断或需求降级。']
  return ['当前信息量有限，建议补充一次需求澄清会议后再评估风险。']
})

const dealProbabilityText = computed(() => {
  // 总结优先：先根据总结内容粗略判断，再回退建议意向等级。
  const progress = (aiSummaryResult.value?.current_progress || '').toLowerCase()
  if (progress.includes('已下单') || progress.includes('推进') || progress.includes('意向高')) {
    return '较高（建议推进方案评审与商务确认）'
  }
  if (progress.includes('观望') || progress.includes('暂停') || progress.includes('预算不足') || progress.includes('意向低')) {
    return '较低（建议先重新确认预算与需求优先级）'
  }

  const code = aiAdviceResult.value?.intent_level?.code
  if (code === 'high') return '较高（建议推进方案评审与商务确认）'
  if (code === 'low') return '较低（建议先重新确认预算与需求优先级）'
  return '中等（建议补齐关键决策信息后推进）'
})

const summaryFollowUpAdvice = computed(() => {
  // 优先复用建议结果；若仅有总结结果，则按总结风险给出演示级建议。
  if (aiAdviceResult.value?.next_step_advice?.length) return aiAdviceResult.value.next_step_advice
  if (hasSummaryRiskData.value) {
    return [
      '建议围绕当前阻塞点安排一次专项沟通，明确责任人与截止时间。',
      '对高风险事项设置下一次跟进节点，并在 48 小时内复盘进展。'
    ]
  }
  return ['建议先安排一次需求澄清沟通，明确预算、决策人与上线时间。']
})

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

// 保存当前客户详情页可持久化数据。
const persistCurrentCustomerDetailState = () => {
  if (!customerId.value) return
  const map = getPersistedMap()
  map[customerId.value] = {
    aiAdviceResult: aiAdviceResult.value,
    aiSummaryResult: aiSummaryResult.value,
    aiAdviceGeneratedAt: aiAdviceGeneratedAt.value,
    aiSummaryGeneratedAt: aiSummaryGeneratedAt.value,
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

  aiAdviceResult.value = persisted.aiAdviceResult || null
  aiSummaryResult.value = persisted.aiSummaryResult || null
  aiAdviceGeneratedAt.value = persisted.aiAdviceGeneratedAt || ''
  aiSummaryGeneratedAt.value = persisted.aiSummaryGeneratedAt || ''
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

// 构建 AI 建议复制文本。
const buildAdviceCopyText = () => {
  if (!aiAdviceResult.value) return ''
  return [
    '【AI 跟进建议】',
    `分析时间：${aiAdviceGeneratedAt.value || '-'}`,
    `客户状态判断：${adviceStatusJudgement.value}`,
    `推荐跟进时间：${aiAdviceResult.value.suggested_next_follow_time || '-'}`,
    '推荐下一步动作：',
    ...adviceNextStepPoints.value.map((item, idx) => `${idx + 1}. ${item}`),
    '推荐沟通话术：',
    aiAdviceResult.value.recommended_talk_track || '-',
    '风险提醒：',
    ...adviceRiskWarnings.value.map((item, idx) => `${idx + 1}. ${item}`)
  ].join('\n')
}

// 构建 AI 总结复制文本。
const buildSummaryCopyText = () => {
  if (!aiSummaryResult.value) return ''
  return [
    '【AI 跟进总结】',
    `分析时间：${aiSummaryGeneratedAt.value || '-'}`,
    '历史跟进摘要：',
    ...summaryHistoryPoints.value.map((item, idx) => `${idx + 1}. ${item}`),
    `客户关注点：${summaryCurrentFocus.value}`,
    `成交可能性判断：${dealProbabilityText.value}`,
    '当前阻塞点：',
    ...summaryRiskPoints.value.map((item, idx) => `${idx + 1}. ${item}`),
    '后续建议：',
    ...summaryFollowUpAdvice.value.map((item, idx) => `${idx + 1}. ${item}`)
  ].join('\n')
}

// 复制 AI 建议。
const handleCopyAdvice = async () => {
  const text = buildAdviceCopyText()
  if (!text) {
    message.warning('暂无可复制的 AI 建议')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    message.success('AI 建议已复制')
  } catch (_error) {
    message.error('复制失败，请手动复制')
  }
}

// 复制 AI 总结。
const handleCopySummary = async () => {
  const text = buildSummaryCopyText()
  if (!text) {
    message.warning('暂无可复制的 AI 总结')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    message.success('AI 总结已复制')
  } catch (_error) {
    message.error('复制失败，请手动复制')
  }
}

// 调用 AI 跟进建议接口并展示结果。
const handleGenerateAdvice = async () => {
  if (!customerId.value) {
    message.error('客户编号无效')
    return
  }
  aiAdviceLoading.value = true
  try {
    const res = await customerAIFollowAdviceApi(customerId.value)
    if (res.data.code !== 0) {
      message.error(res.data.message || 'AI 跟进建议生成失败')
      return
    }
    aiAdviceResult.value = res.data.data
    aiAdviceGeneratedAt.value = new Date().toLocaleString('zh-CN')
    appendOperationLog('AI', '生成了 AI 跟进建议')
    // 生成完成后滚动到 AI 结果区域，便于用户直接查看内容。
    await nextTick()
    aiPanelsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    message.success('AI 跟进建议生成成功')
  } catch (_error) {
    message.error('AI 跟进建议请求失败')
  } finally {
    aiAdviceLoading.value = false
  }
}

// 调用 AI 跟进总结接口并展示结果。
const handleGenerateSummary = async () => {
  if (!customerId.value) {
    message.error('客户编号无效')
    return
  }
  aiSummaryLoading.value = true
  try {
    const res = await customerAIFollowSummaryApi(customerId.value)
    if (res.data.code !== 0) {
      message.error(res.data.message || 'AI 跟进总结生成失败')
      return
    }
    aiSummaryResult.value = res.data.data
    aiSummaryGeneratedAt.value = new Date().toLocaleString('zh-CN')
    appendOperationLog('AI', '生成了 AI 跟进总结')
    // 生成完成后滚动到 AI 结果区域，便于用户直接查看内容。
    await nextTick()
    aiPanelsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    message.success('AI 跟进总结生成成功')
  } catch (_error) {
    message.error('AI 跟进总结请求失败')
  } finally {
    aiSummaryLoading.value = false
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
      user_message: '分析当前客户状态，并给出下一步跟进建议',
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
  } catch (_error) {
    multiAgentResult.value = null
    multiAgentError.value = '多 Agent 分析请求失败'
    message.error(multiAgentError.value)
  } finally {
    multiAgentLoading.value = false
  }
}

const goBack = () => {
  router.push('/customer')
}

const handleRefresh = async () => {
  await fetchDetail()
  await fetchFollowList()
  await fetchRelatedOrders()
  // 刷新后显式恢复当前客户的本地持久化状态，避免展示态与缓存态不一致。
  restorePersistedCustomerDetailState()
  message.success('客户详情已刷新')
}

onMounted(async () => {
  await fetchDetail()
  await fetchFollowList()
  await fetchRelatedOrders()
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

.ai-panel-card {
  border: 1px solid #d9e1ec;
  border-radius: 10px;
}

.legacy-ai-card :deep(.n-collapse-item__header) {
  font-weight: 600;
}

.legacy-inner-card {
  background: #fafafa;
}

.ai-meta-row {
  margin-bottom: 8px;
  color: #999;
  font-size: 12px;
}

.ai-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-label {
  color: #666;
  min-width: 110px;
}

.ai-value {
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-list {
  margin: 0 0 0 2px;
  padding-left: 18px;
  color: #333;
  line-height: 1.7;
}

.ai-talk-track {
  border: 1px solid #eceff5;
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 12px;
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
