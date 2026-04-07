<template>
  <div class="customer-detail-page">
    <n-card title="客户详情" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button :loading="aiAdviceLoading" @click="handleGenerateAdvice">AI 生成跟进建议</n-button>
          <n-button :loading="aiSummaryLoading" @click="handleGenerateSummary">AI 总结跟进记录</n-button>
          <n-button tertiary @click="goBack">返回</n-button>
        </n-space>
      </template>

      <n-spin :show="detailLoading">
        <n-descriptions v-if="detail" label-placement="left" bordered :column="2">
          <n-descriptions-item label="客户编号">{{ detail.id }}</n-descriptions-item>
          <n-descriptions-item label="客户名称">{{ detail.name }}</n-descriptions-item>
          <n-descriptions-item label="联系人">{{ detail.contact_name || '-' }}</n-descriptions-item>
          <n-descriptions-item label="负责人">{{ detail.owner_name || '-' }}</n-descriptions-item>
          <n-descriptions-item label="手机号">{{ detail.phone }}</n-descriptions-item>
          <n-descriptions-item label="邮箱">{{ detail.email || '-' }}</n-descriptions-item>
          <n-descriptions-item label="公司">{{ detail.company || '-' }}</n-descriptions-item>
          <n-descriptions-item label="等级">{{ getCustomerLevelLabel(detail.level) }}</n-descriptions-item>
          <n-descriptions-item label="状态">{{ getCustomerStatusLabel(detail.status) }}</n-descriptions-item>
          <n-descriptions-item label="来源">{{ getCustomerSourceLabel(detail.source) }}</n-descriptions-item>
          <n-descriptions-item label="最近跟进时间">{{ detail.last_follow_at || '-' }}</n-descriptions-item>
          <n-descriptions-item label="创建时间">{{ detail.created_at }}</n-descriptions-item>
          <n-descriptions-item label="更新时间">{{ detail.updated_at }}</n-descriptions-item>
          <n-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</n-descriptions-item>
        </n-descriptions>
        <n-empty v-else description="暂无客户信息" />
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
        <n-empty v-if="!followList.length" description="暂无跟进记录" />
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
      <n-card title="AI 跟进建议" :bordered="true" class="ai-panel-card">
        <template #header-extra>
          <n-button :loading="aiAdviceLoading" @click="handleGenerateAdvice">重新生成</n-button>
        </template>
        <n-spin :show="aiAdviceLoading">
          <n-empty v-if="!aiAdviceResult" description="暂无 AI 跟进建议，请点击重新生成" />
          <n-space v-else vertical :size="14">
            <div class="ai-row">
              <span class="ai-label">客户意向：</span>
              <n-tag :type="getIntentTagType(aiAdviceResult.intent_level.code)">
                {{ aiAdviceResult.intent_level.label }}
              </n-tag>
            </div>
            <div class="ai-row">
              <span class="ai-label">当前关注点：</span>
              <span class="ai-value">{{ aiAdviceResult.current_focus || '-' }}</span>
            </div>
            <div class="ai-row">
              <span class="ai-label">下一步建议：</span>
            </div>
            <ul class="ai-list">
              <li v-for="(item, index) in aiAdviceResult.next_step_advice" :key="`advice-${index}`">{{ item }}</li>
            </ul>
            <div class="ai-row">
              <span class="ai-label">推荐沟通话术：</span>
            </div>
            <div class="ai-talk-track">{{ aiAdviceResult.recommended_talk_track || '-' }}</div>
            <div class="ai-row">
              <span class="ai-label">建议下次跟进时间：</span>
              <span class="ai-value">{{ aiAdviceResult.suggested_next_follow_time || '-' }}</span>
            </div>
          </n-space>
        </n-spin>
      </n-card>

      <n-card title="AI 跟进总结" :bordered="true" class="ai-panel-card">
        <template #header-extra>
          <n-button :loading="aiSummaryLoading" @click="handleGenerateSummary">重新生成</n-button>
        </template>
        <n-spin :show="aiSummaryLoading">
          <n-empty v-if="!aiSummaryResult" description="暂无 AI 跟进总结，请点击重新生成" />
          <n-space v-else vertical :size="14">
            <div class="ai-row">
              <span class="ai-label">当前进展：</span>
              <span class="ai-value">{{ aiSummaryResult.current_progress || '-' }}</span>
            </div>
            <div class="ai-row">
              <span class="ai-label">历史沟通重点：</span>
            </div>
            <ul class="ai-list">
              <li v-for="(item, index) in aiSummaryResult.history_key_points" :key="`point-${index}`">{{ item }}</li>
            </ul>
            <div class="ai-row">
              <span class="ai-label">潜在风险：</span>
            </div>
            <ul class="ai-list">
              <li v-for="(item, index) in aiSummaryResult.potential_risks" :key="`risk-${index}`">{{ item }}</li>
            </ul>
          </n-space>
        </n-spin>
      </n-card>
    </div>

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
// 客户详情页：展示客户基本信息、跟进记录，并提供 AI 跟进分析能力。
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDatePicker,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NForm,
  NFormItemGi,
  NInput,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  NTimeline,
  NTimelineItem,
  useMessage,
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
import {
  FOLLOW_TYPE_OPTIONS,
  getCustomerLevelLabel,
  getCustomerSourceLabel,
  getCustomerStatusLabel,
  getFollowTypeLabel,
  getFollowTypeTagType
} from '@/constants/enums'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 页面加载与提交加载状态
const detailLoading = ref(false)
const followLoading = ref(false)
const followSubmitLoading = ref(false)
const aiAdviceLoading = ref(false)
const aiSummaryLoading = ref(false)

// 客户详情与跟进记录列表数据
const detail = ref<CustomerItem | null>(null)
const followList = ref<CustomerFollowRecordItem[]>([])
const aiAdviceResult = ref<CustomerAIFollowAdvice | null>(null)
const aiSummaryResult = ref<CustomerAIFollowSummary | null>(null)

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

// 将空字符串和 null 统一展示为 '-'。
const safeText = (value?: string | null): string => {
  if (!value) return '-'
  const text = String(value).trim()
  return text || '-'
}

// 根据意向等级返回标签颜色，便于快速识别客户优先级。
const getIntentTagType = (code: string) => {
  if (code === 'high') return 'error'
  if (code === 'medium') return 'warning'
  return 'info'
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
    if (followList.value.length === 1 && followPagination.page > 1) {
      followPagination.page -= 1
    }
    await fetchFollowList()
    await fetchDetail()
  } catch (_error) {
    message.error('删除跟进记录请求失败')
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

const goBack = () => {
  router.push('/customer')
}

onMounted(async () => {
  await fetchDetail()
  await fetchFollowList()
})
</script>

<style scoped>
.customer-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
}

.ai-panels > * {
  flex: 1 1 0;
  min-width: 0;
}

.ai-panel-card {
  border: 1px solid #d9e1ec;
  border-radius: 10px;
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
