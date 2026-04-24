<template>
  <div class="ai-call-log-page">
    <n-grid :cols="24" :x-gap="12" :y-gap="12">
      <n-gi v-for="card in summaryCards" :key="card.title" :span="4">
        <n-card size="small" :bordered="false" class="summary-card">
          <n-spin :show="summaryLoading">
            <div class="summary-title">{{ card.title }}</div>
            <div class="summary-value">{{ card.value }}</div>
            <div class="summary-desc">{{ card.desc }}</div>
          </n-spin>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card title="AI 调用日志" :bordered="false">
      <div class="search-area">
        <n-form class="search-form" :model="searchForm" label-placement="left" label-width="86">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="5" label="调用模块">
              <n-select v-model:value="searchForm.module" :options="AI_CALL_MODULE_OPTIONS" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="5" label="调用状态">
              <n-select v-model:value="searchForm.status" :options="AI_CALL_STATUS_OPTIONS" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="8" label="关键词">
              <n-input
                v-model:value="searchForm.keyword"
                placeholder="搜索提示词 / 响应 / 错误信息"
                clearable
                @keyup.enter="handleSearch"
              />
            </n-form-item-gi>
            <n-form-item-gi :span="6">
              <n-space justify="end" style="width: 100%">
                <n-button type="primary" @click="handleSearch">搜索</n-button>
                <n-button @click="handleReset">重置</n-button>
                <n-button @click="handleRefresh">刷新</n-button>
              </n-space>
            </n-form-item-gi>
          </n-grid>
        </n-form>
      </div>

      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="tableLoading"
        :row-key="(row: AiCallLogItem) => row.id"
        :locale="{ emptyText: '暂无 AI 调用日志，请调整筛选条件后重试' }"
      />

      <div class="pagination-area">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          show-size-picker
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </n-card>

    <n-modal v-model:show="detailVisible" preset="card" title="AI 调用日志详情" style="width: 920px">
      <n-spin :show="detailLoading">
        <template v-if="detailData">
          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="调用模块">
              <n-tag :type="getAiCallModuleTagType(detailData.module || '')" size="small">
                {{ getAiCallModuleLabel(detailData.module || '') }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="任务类型">
              <n-tag :type="getAiCallTaskTypeTagType(detailData.task_type || '')" size="small">
                {{ getAiCallTaskTypeLabel(detailData.task_type || '') }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="Prompt模板">{{ detailData.prompt_template_key || '-' }}</n-descriptions-item>
            <n-descriptions-item label="模板版本">{{ detailData.prompt_version || '-' }}</n-descriptions-item>
            <n-descriptions-item label="调用状态">
              <n-tag :type="getAiCallStatusTagType(detailData.status)" size="small">
                {{ getAiCallStatusLabel(detailData.status) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="模型名称">{{ detailData.model_name || '-' }}</n-descriptions-item>
            <n-descriptions-item label="调用耗时">{{ formatLatency(detailData.latency_ms) }}</n-descriptions-item>
            <n-descriptions-item label="创建时间">{{ detailData.created_at || '-' }}</n-descriptions-item>
          </n-descriptions>

          <n-divider title-placement="left">调用复盘</n-divider>
          <n-alert :type="reviewResult.alertType" :show-icon="false" class="review-alert">
            <n-descriptions label-placement="left" :column="1" size="small">
              <n-descriptions-item label="复盘结论">{{ reviewResult.conclusion }}</n-descriptions-item>
              <n-descriptions-item label="可能原因">{{ reviewResult.reason }}</n-descriptions-item>
              <n-descriptions-item label="建议处理">{{ reviewResult.suggestion }}</n-descriptions-item>
            </n-descriptions>
          </n-alert>

          <n-divider title-placement="left">提示词</n-divider>
          <pre class="detail-text">{{ detailData.prompt || '-' }}</pre>

          <n-divider title-placement="left">模型响应</n-divider>
          <pre class="detail-text">{{ detailData.response || '-' }}</pre>

          <n-divider title-placement="left">错误信息</n-divider>
          <pre class="detail-text error-text">{{ detailData.error_message || '-' }}</pre>
        </template>

        <n-empty v-else description="暂无日志详情" />
      </n-spin>
      <template #footer>
        <n-space justify="end">
          <n-button @click="detailVisible = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
/**
 * AI 调用日志页面：展示模型调用记录，支持模块/状态筛选、关键词搜索、分页和详情查看。
 */
import { computed, h, onMounted, reactive, ref, type VNodeChild } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NEmpty,
  NForm,
  NFormItemGi,
  NGi,
  NGrid,
  NInput,
  NModal,
  NPagination,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  NTooltip,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import {
  aiCallLogDetailApi,
  aiCallLogListApi,
  aiCallLogSummaryApi,
  type AiCallLogDetail,
  type AiCallLogItem,
  type AiCallLogSummary
} from '@/api/ai-call-log'
import {
  AI_CALL_MODULE_OPTIONS,
  AI_CALL_STATUS_OPTIONS,
  getAiCallModuleLabel,
  getAiCallModuleTagType,
  getAiCallStatusLabel,
  getAiCallStatusTagType,
  getAiCallTaskTypeLabel,
  getAiCallTaskTypeTagType
} from '@/constants/enums'

const message = useMessage()

// 搜索表单状态：仅保留本页面需要的筛选项。
const searchForm = reactive({
  module: null as string | null,
  status: null as string | null,
  keyword: ''
})

// 分页状态：与后端 page/page_size 参数保持一致。
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const tableLoading = ref(false)
const summaryLoading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const tableData = ref<AiCallLogItem[]>([])
const detailData = ref<AiCallLogDetail | null>(null)
const summaryData = ref<AiCallLogSummary>({
  total_calls: 0,
  success_calls: 0,
  failed_calls: 0,
  success_rate: 0,
  avg_latency_ms: 0,
  customer_follow_advice_calls: 0,
  customer_ai_adopted_count: 0,
  customer_ai_adoption_rate: 0
})

// 顶部统计卡片数据：当前为全局统计，不跟随列表筛选联动。
const summaryCards = computed(() => [
  { title: 'AI 调用总次数', value: String(summaryData.value.total_calls), desc: `成功 ${summaryData.value.success_calls} 次` },
  { title: '成功率', value: `${summaryData.value.success_rate}%`, desc: '成功调用 / 总调用' },
  { title: '失败次数', value: String(summaryData.value.failed_calls), desc: 'status = failed' },
  { title: '平均耗时', value: formatLatency(summaryData.value.avg_latency_ms), desc: 'latency_ms 平均值' },
  { title: '客户 AI 采纳次数', value: String(summaryData.value.customer_ai_adopted_count), desc: '跟进记录来源为 AI 采纳' },
  { title: '客户 AI 采纳率', value: `${summaryData.value.customer_ai_adoption_rate}%`, desc: '采纳次数 / 跟进建议成功次数' }
])

type ReviewAlertType = 'success' | 'warning' | 'error' | 'info'

// 调用复盘结果：基于日志状态、响应和错误信息做前端规则诊断。
const reviewResult = computed((): { alertType: ReviewAlertType; conclusion: string; reason: string; suggestion: string } => {
  const detail = detailData.value
  if (!detail) {
    return {
      alertType: 'info',
      conclusion: '暂无日志',
      reason: '当前未加载日志详情',
      suggestion: '请选择一条 AI 调用日志查看详情'
    }
  }

  const errorText = String(detail.error_message || '')
  const responseText = String(detail.response || '')
  const normalizedError = errorText.toLowerCase()

  if (detail.status === 'success' && responseText.trim()) {
    return {
      alertType: 'success',
      conclusion: '调用成功',
      reason: '模型返回了有效内容',
      suggestion: '可结合业务结果判断是否需要优化 Prompt'
    }
  }

  if (!responseText.trim()) {
    return {
      alertType: detail.status === 'failed' ? 'error' : 'warning',
      conclusion: detail.status === 'failed' ? '调用失败' : '响应为空',
      reason: '模型没有返回有效内容',
      suggestion: '检查 prompt、模型响应和 fallback'
    }
  }

  if (errorText.includes('DEEPSEEK_API_KEY')) {
    return {
      alertType: 'error',
      conclusion: '调用失败',
      reason: '未配置 DeepSeek API Key',
      suggestion: '检查环境变量 DEEPSEEK_API_KEY'
    }
  }

  if (errorText.includes('JSON') || errorText.includes('不是 JSON 对象')) {
    return {
      alertType: 'warning',
      conclusion: '解析失败',
      reason: '模型返回格式不符合 JSON 要求',
      suggestion: '加强 system prompt 或输出格式约束'
    }
  }

  if (normalizedError.includes('timeout') || normalizedError.includes('timed out')) {
    return {
      alertType: 'warning',
      conclusion: '调用超时',
      reason: '模型接口响应超时或网络不稳定',
      suggestion: '增加超时重试或优化 prompt 长度'
    }
  }

  if (normalizedError.includes('rate limit') || normalizedError.includes('429')) {
    return {
      alertType: 'warning',
      conclusion: '接口限流',
      reason: '模型服务触发 rate limit 或 429 限流',
      suggestion: '增加重试、降频或切换模型'
    }
  }

  return {
    alertType: detail.status === 'failed' ? 'error' : 'warning',
    conclusion: detail.status === 'failed' ? '调用失败' : '需要复核',
    reason: '模型调用异常或服务端处理异常',
    suggestion: '查看 error_message 和后端日志'
  }
})

// 渲染单行省略文本，避免日志字段撑开表格。
const renderEllipsisCell = (text: string | null | undefined): VNodeChild =>
  h(
    NTooltip,
    { trigger: 'hover' },
    {
      trigger: () => h('div', { class: 'text-ellipsis' }, text || '-'),
      default: () => text || '-'
    }
  )

// 格式化耗时，空值统一展示为占位符。
const formatLatency = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return `${value} ms`
}

const columns: DataTableColumns<AiCallLogItem> = [
  { title: 'ID', key: 'id', width: 80 },
  {
    title: '调用模块',
    key: 'module',
    width: 120,
    render: (row) =>
      h(NTag, { type: getAiCallModuleTagType(row.module || ''), size: 'small' }, { default: () => getAiCallModuleLabel(row.module || '') })
  },
  {
    title: '任务类型',
    key: 'task_type',
    minWidth: 130,
    render: (row) =>
      h(NTag, { type: getAiCallTaskTypeTagType(row.task_type || ''), size: 'small' }, { default: () => getAiCallTaskTypeLabel(row.task_type || '') })
  },
  { title: 'Prompt模板', key: 'prompt_template_key', minWidth: 180, render: (row) => renderEllipsisCell(row.prompt_template_key) },
  { title: '版本', key: 'prompt_version', width: 90, render: (row) => row.prompt_version || '-' },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) =>
      h(NTag, { type: getAiCallStatusTagType(row.status), size: 'small' }, { default: () => getAiCallStatusLabel(row.status) })
  },
  { title: '模型', key: 'model_name', minWidth: 140, render: (row) => renderEllipsisCell(row.model_name) },
  { title: '耗时', key: 'latency_ms', width: 100, render: (row) => formatLatency(row.latency_ms) },
  { title: '创建时间', key: 'created_at', minWidth: 170 },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    fixed: 'right',
    render: (row) =>
      h(NButton, { size: 'small', tertiary: true, type: 'primary', onClick: () => openDetail(row.id) }, { default: () => '详情' })
  }
]

// 获取日志列表数据。
const fetchList = async () => {
  tableLoading.value = true
  try {
    const res = await aiCallLogListApi({
      module: searchForm.module || '',
      status: searchForm.status || '',
      keyword: searchForm.keyword.trim(),
      page: pagination.page,
      page_size: pagination.pageSize
    })

    if (res.data.code !== 0) {
      message.error(res.data.message || 'AI 调用日志加载失败')
      return
    }

    tableData.value = res.data.data?.items || []
    pagination.total = res.data.data?.total || 0
  } catch (_error) {
    message.error('AI 调用日志请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 获取 AI 效果统计数据。
const fetchSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await aiCallLogSummaryApi()
    if (res.data.code !== 0) {
      message.error(res.data.message || 'AI 效果统计加载失败')
      return
    }
    summaryData.value = res.data.data
  } catch (_error) {
    message.error('AI 效果统计请求失败')
  } finally {
    summaryLoading.value = false
  }
}

// 执行搜索并回到第一页。
const handleSearch = async () => {
  pagination.page = 1
  await fetchList()
}

// 重置筛选条件并重新加载。
const handleReset = async () => {
  searchForm.module = null
  searchForm.status = null
  searchForm.keyword = ''
  pagination.page = 1
  await fetchList()
}

// 刷新列表，保留当前筛选与分页。
const handleRefresh = async () => {
  await Promise.all([fetchSummary(), fetchList()])
  message.success('日志列表已刷新')
}

// 切换页码后加载对应页数据。
const handlePageChange = async (page: number) => {
  pagination.page = page
  await fetchList()
}

// 切换分页大小后回到第一页。
const handlePageSizeChange = async (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  await fetchList()
}

// 打开详情弹窗并加载完整日志内容。
const openDetail = async (id: number) => {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await aiCallLogDetailApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || 'AI 调用日志详情加载失败')
      return
    }
    detailData.value = res.data.data
  } catch (_error) {
    message.error('AI 调用日志详情请求失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  fetchSummary()
  fetchList()
})
</script>

<style scoped>
/* AI 调用日志页面根容器 */
.ai-call-log-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 搜索区域：与其他后台列表页保持一致的上下间距。 */
.search-area {
  margin-bottom: 12px;
}

/* 统计卡片：展示 AI 调用和采纳效果核心指标。 */
.summary-card {
  height: 100%;
  background: #fbfdff;
}

.summary-title {
  color: #6b7280;
  font-size: 13px;
}

.summary-value {
  margin-top: 8px;
  color: #1f2329;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
}

.summary-desc {
  margin-top: 6px;
  color: #8b95a1;
  font-size: 12px;
  line-height: 1.4;
}

/* 调用复盘区域：将规则诊断结果放在长文本前，便于先看结论再查明细。 */
.review-alert {
  margin-bottom: 4px;
}

/* 分页区域：固定在表格下方右侧。 */
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 表格省略文本：用于模型名称等短文本兜底。 */
.text-ellipsis {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 详情长文本：保留换行并限制最大高度，避免弹窗过高。 */
.detail-text {
  max-height: 260px;
  overflow: auto;
  padding: 12px;
  margin: 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f8fafc;
  color: #1f2329;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 错误信息文本：使用轻量红色背景突出失败原因。 */
.error-text {
  background: #fff7f7;
  border-color: #f3caca;
}
</style>
