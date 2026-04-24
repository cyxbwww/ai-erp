<template>
  <div class="prompt-template-page">
    <n-card title="Prompt 模板" :bordered="false">
      <div class="search-area">
        <n-form :model="searchForm" label-placement="left" label-width="86">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="5" label="所属模块">
              <n-select v-model:value="searchForm.module" :options="moduleOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="5" label="任务类型">
              <n-select v-model:value="searchForm.task_type" :options="taskTypeOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="8" label="关键词">
              <n-input
                v-model:value="searchForm.keyword"
                placeholder="搜索模板 Key / 名称 / 描述"
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
        :data="filteredTemplates"
        :loading="tableLoading"
        :pagination="false"
        :row-key="(row: PromptTemplateItem) => row.template_key"
        :locale="{ emptyText: '暂无 Prompt 模板，请调整筛选条件后重试' }"
      />
    </n-card>

    <n-card title="模板效果统计" :bordered="false">
      <n-data-table
        :columns="summaryColumns"
        :data="promptSummaryList"
        :loading="summaryLoading"
        :pagination="false"
        :row-key="(row: PromptTemplateSummaryItem) => `${row.prompt_template_key}-${row.prompt_version || 'none'}-${row.module || 'none'}-${row.task_type || 'none'}`"
        :locale="{ emptyText: '暂无模板效果统计数据' }"
      />
    </n-card>

    <n-modal v-model:show="detailVisible" preset="card" title="Prompt 模板详情" style="width: 920px">
      <n-spin :show="detailLoading">
        <template v-if="detailData">
          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="模板 Key">{{ detailData.template_key }}</n-descriptions-item>
            <n-descriptions-item label="模板名称">{{ detailData.name }}</n-descriptions-item>
            <n-descriptions-item label="所属模块">
              <n-tag :type="getAiCallModuleTagType(detailData.module)" size="small">
                {{ getAiCallModuleLabel(detailData.module) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="任务类型">
              <n-tag :type="getAiCallTaskTypeTagType(detailData.task_type)" size="small">
                {{ getAiCallTaskTypeLabel(detailData.task_type) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="版本">{{ detailData.version || '-' }}</n-descriptions-item>
            <n-descriptions-item label="描述">{{ detailData.description || '-' }}</n-descriptions-item>
          </n-descriptions>

          <n-divider title-placement="left">System Prompt</n-divider>
          <pre class="prompt-code">{{ detailData.system_prompt || '-' }}</pre>

          <n-divider title-placement="left">User Prompt Template</n-divider>
          <pre class="prompt-code">{{ detailData.user_prompt_template || '-' }}</pre>
        </template>
        <n-empty v-else description="暂无模板详情" />
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
 * Prompt 模板只读页面：用于查看后端内存模板列表和模板正文，不提供编辑保存能力。
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
  NGrid,
  NInput,
  NModal,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  NTooltip,
  useMessage,
  type DataTableColumns,
  type SelectOption
} from 'naive-ui'
import {
  promptTemplateDetailApi,
  promptTemplateListApi,
  type PromptTemplateDetail,
  type PromptTemplateItem
} from '@/api/prompt-template'
import {
  aiCallLogPromptSummaryApi,
  type PromptTemplateSummaryItem
} from '@/api/ai-call-log'
import {
  getAiCallModuleLabel,
  getAiCallModuleTagType,
  getAiCallTaskTypeLabel,
  getAiCallTaskTypeTagType
} from '@/constants/enums'

const message = useMessage()

// 筛选表单状态：列表数据较少，筛选在前端本地完成。
const searchForm = reactive({
  module: null as string | null,
  task_type: null as string | null,
  keyword: ''
})

const tableLoading = ref(false)
const summaryLoading = ref(false)
const detailLoading = ref(false)
const detailVisible = ref(false)
const templateList = ref<PromptTemplateItem[]>([])
const promptSummaryList = ref<PromptTemplateSummaryItem[]>([])
const detailData = ref<PromptTemplateDetail | null>(null)

// 模块筛选选项：根据后端返回模板动态生成，避免写死不完整枚举。
const moduleOptions = computed<SelectOption[]>(() => {
  const modules = Array.from(new Set(templateList.value.map((item) => item.module).filter(Boolean)))
  return modules.map((value) => ({ label: getAiCallModuleLabel(value), value }))
})

// 任务类型筛选选项：根据后端返回模板动态生成。
const taskTypeOptions = computed<SelectOption[]>(() => {
  const taskTypes = Array.from(new Set(templateList.value.map((item) => item.task_type).filter(Boolean)))
  return taskTypes.map((value) => ({ label: getAiCallTaskTypeLabel(value), value }))
})

// 本地筛选后的模板列表。
const filteredTemplates = computed(() => {
  const keyword = searchForm.keyword.trim().toLowerCase()
  return templateList.value.filter((item) => {
    const matchModule = !searchForm.module || item.module === searchForm.module
    const matchTaskType = !searchForm.task_type || item.task_type === searchForm.task_type
    const matchKeyword = !keyword || [item.template_key, item.name, item.description]
      .some((text) => String(text || '').toLowerCase().includes(keyword))
    return matchModule && matchTaskType && matchKeyword
  })
})

// 渲染省略文本并提供悬浮完整内容。
const renderEllipsisCell = (text: string | null | undefined, maxWidth = 220): VNodeChild =>
  h(
    NTooltip,
    { trigger: 'hover' },
    {
      trigger: () => h('div', { class: 'text-ellipsis', style: { maxWidth: `${maxWidth}px` } }, text || '-'),
      default: () => text || '-'
    }
  )

const columns: DataTableColumns<PromptTemplateItem> = [
  { title: '模板 Key', key: 'template_key', minWidth: 220, render: (row) => renderEllipsisCell(row.template_key, 260) },
  { title: '模板名称', key: 'name', minWidth: 140, render: (row) => renderEllipsisCell(row.name, 180) },
  {
    title: '模块',
    key: 'module',
    width: 110,
    render: (row) =>
      h(NTag, { type: getAiCallModuleTagType(row.module), size: 'small' }, { default: () => getAiCallModuleLabel(row.module) })
  },
  {
    title: '任务类型',
    key: 'task_type',
    minWidth: 150,
    render: (row) =>
      h(NTag, { type: getAiCallTaskTypeTagType(row.task_type), size: 'small' }, { default: () => getAiCallTaskTypeLabel(row.task_type) })
  },
  { title: '版本', key: 'version', width: 90 },
  { title: '描述', key: 'description', minWidth: 260, render: (row) => renderEllipsisCell(row.description, 360) },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    fixed: 'right',
    render: (row) =>
      h(NButton, { size: 'small', tertiary: true, type: 'primary', onClick: () => openDetail(row.template_key) }, { default: () => '详情' })
  }
]

const summaryColumns: DataTableColumns<PromptTemplateSummaryItem> = [
  { title: 'Prompt模板', key: 'prompt_template_key', minWidth: 220, render: (row) => renderEllipsisCell(row.prompt_template_key, 260) },
  { title: '版本', key: 'prompt_version', width: 90, render: (row) => row.prompt_version || '-' },
  {
    title: '模块',
    key: 'module',
    width: 110,
    render: (row) =>
      h(NTag, { type: getAiCallModuleTagType(row.module || ''), size: 'small' }, { default: () => getAiCallModuleLabel(row.module || '') })
  },
  {
    title: '任务类型',
    key: 'task_type',
    minWidth: 150,
    render: (row) =>
      h(NTag, { type: getAiCallTaskTypeTagType(row.task_type || ''), size: 'small' }, { default: () => getAiCallTaskTypeLabel(row.task_type || '') })
  },
  { title: '调用次数', key: 'total_calls', width: 100 },
  { title: '成功率', key: 'success_rate', width: 100, render: (row) => `${row.success_rate}%` },
  { title: '失败次数', key: 'failed_calls', width: 100 },
  { title: '平均耗时', key: 'avg_latency_ms', width: 120, render: (row) => `${row.avg_latency_ms} ms` }
]

// 获取模板列表。
const fetchTemplates = async () => {
  tableLoading.value = true
  try {
    const res = await promptTemplateListApi()
    if (res.data.code !== 0) {
      message.error(res.data.message || 'Prompt 模板列表加载失败')
      return
    }
    templateList.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (_error) {
    message.error('Prompt 模板列表请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 获取 Prompt 模板效果统计。
const fetchPromptSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await aiCallLogPromptSummaryApi()
    if (res.data.code !== 0) {
      message.error(res.data.message || '模板效果统计加载失败')
      return
    }
    promptSummaryList.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (_error) {
    message.error('模板效果统计请求失败')
  } finally {
    summaryLoading.value = false
  }
}

// 搜索操作：本地筛选由 computed 自动完成，这里保留入口保持列表页交互一致。
const handleSearch = () => {
  if (!filteredTemplates.value.length) {
    message.info('未匹配到模板')
  }
}

// 重置筛选条件。
const handleReset = () => {
  searchForm.module = null
  searchForm.task_type = null
  searchForm.keyword = ''
}

// 刷新模板列表并保留当前筛选条件。
const handleRefresh = async () => {
  await Promise.all([fetchTemplates(), fetchPromptSummary()])
  message.success('Prompt 模板已刷新')
}

// 打开模板详情弹窗。
const openDetail = async (templateKey: string) => {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await promptTemplateDetailApi(templateKey)
    if (res.data.code !== 0) {
      message.error(res.data.message || 'Prompt 模板详情加载失败')
      return
    }
    detailData.value = res.data.data
  } catch (_error) {
    message.error('Prompt 模板详情请求失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  fetchTemplates()
  fetchPromptSummary()
})
</script>

<style scoped>
/* Prompt 模板页面根容器 */
.prompt-template-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 搜索区域：保持和其他后台列表页一致的间距。 */
.search-area {
  margin-bottom: 12px;
}

/* 表格单元格省略展示，避免长模板描述撑宽页面。 */
.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Prompt 代码块：保留换行并便于复制查看。 */
.prompt-code {
  max-height: 320px;
  overflow: auto;
  padding: 12px;
  margin: 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
