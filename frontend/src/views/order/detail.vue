<template>
  <div class="order-detail-page">
    <n-card title="订单详情" :bordered="false">
      <template #header-extra>
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
          <n-button type="primary" tertiary @click="goEdit">编辑订单</n-button>
          <n-button @click="goList">返回列表</n-button>
        </n-space>
      </template>

      <n-spin :show="pageLoading">
        <n-descriptions v-if="detailData" label-placement="left" bordered :column="2">
          <n-descriptions-item label="订单编号">{{ detailData.order_no }}</n-descriptions-item>
          <n-descriptions-item label="客户名称">{{ detailData.customer_name }}</n-descriptions-item>
          <n-descriptions-item label="订单状态">
            <n-tag :type="getOrderStatusTagType(detailData.status)" size="small">
              {{ getOrderStatusLabel(detailData.status) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="订单总金额">¥{{ Number(detailData.total_amount || 0).toFixed(2) }}</n-descriptions-item>
          <n-descriptions-item label="创建时间">{{ detailData.created_at }}</n-descriptions-item>
          <n-descriptions-item label="更新时间">{{ detailData.updated_at }}</n-descriptions-item>
          <n-descriptions-item label="备注" :span="2">{{ detailData.remark || '-' }}</n-descriptions-item>
        </n-descriptions>
        <n-empty v-else description="暂无订单信息" />
      </n-spin>
    </n-card>

    <n-card title="AI 分析模块" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button :loading="aiLoadingType === 'analysis'" @click="handleAIAnalyze('analysis')">AI 分析订单</n-button>
          <n-button :loading="aiLoadingType === 'risk'" @click="handleAIAnalyze('risk')">AI 风险检测</n-button>
          <n-button :loading="aiLoadingType === 'advice'" @click="handleAIAnalyze('advice')">AI 销售建议</n-button>
        </n-space>
      </template>

      <n-grid :cols="3" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-card size="small" title="订单分析结果">
            <n-empty v-if="!aiResults.analysis" description="暂无结果，请点击“AI 分析订单”" />
            <div v-else class="ai-result-block">
              <div class="ai-summary">{{ aiResults.analysis.summary }}</div>
              <div class="ai-subtitle">分析要点</div>
              <ul class="ai-list">
                <li v-for="(item, idx) in aiResults.analysis.highlights" :key="`a-h-${idx}`">{{ item }}</li>
              </ul>
              <div class="ai-subtitle">建议动作</div>
              <ul class="ai-list">
                <li v-for="(item, idx) in aiResults.analysis.suggestions" :key="`a-s-${idx}`">{{ item }}</li>
              </ul>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small" title="风险检测结果">
            <n-empty v-if="!aiResults.risk" description="暂无结果，请点击“AI 风险检测”" />
            <div v-else class="ai-result-block">
              <div class="ai-summary">{{ aiResults.risk.summary }}</div>
              <div class="ai-subtitle">风险点</div>
              <ul class="ai-list">
                <li v-for="(item, idx) in aiResults.risk.risks" :key="`r-r-${idx}`">{{ item }}</li>
              </ul>
              <div class="ai-subtitle">缓解建议</div>
              <ul class="ai-list">
                <li v-for="(item, idx) in aiResults.risk.suggestions" :key="`r-s-${idx}`">{{ item }}</li>
              </ul>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small" title="销售建议结果">
            <n-empty v-if="!aiResults.advice" description="暂无结果，请点击“AI 销售建议”" />
            <div v-else class="ai-result-block">
              <div class="ai-summary">{{ aiResults.advice.summary }}</div>
              <div class="ai-subtitle">机会点</div>
              <ul class="ai-list">
                <li v-for="(item, idx) in aiResults.advice.highlights" :key="`s-h-${idx}`">{{ item }}</li>
              </ul>
              <div class="ai-subtitle">销售动作</div>
              <ul class="ai-list">
                <li v-for="(item, idx) in aiResults.advice.suggestions" :key="`s-s-${idx}`">{{ item }}</li>
              </ul>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-card>

    <n-card title="订单明细" :bordered="false">
      <n-data-table
        :columns="itemColumns"
        :data="detailData?.items || []"
        :pagination="false"
        :loading="pageLoading"
        :row-key="(row: OrderItem) => `${row.product_id}-${row.id || 0}`"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 订单详情页：展示订单信息、明细，并提供订单 AI 分析功能。
import { computed, h, onMounted, reactive, ref } from 'vue'
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
  NTag,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import { orderAIAnalysisApi, orderDetailApi, orderStatusUpdateApi, type OrderAIAnalysisResult, type OrderDetail, type OrderItem } from '@/api/order'
import { getOrderStatusLabel, getOrderStatusTagType, getProductUnitLabel } from '@/constants/enums'

type OrderTransitionStatus = 'confirmed' | 'completed' | 'cancelled'
type AIType = 'analysis' | 'risk' | 'advice'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 页面加载与状态更新加载状态
const pageLoading = ref(false)
const statusUpdating = ref(false)
const aiLoadingType = ref<AIType | null>(null)
// 订单详情数据
const detailData = ref<OrderDetail | null>(null)

// 三类 AI 结果分别缓存，便于反复查看。
const aiResults = reactive<{
  analysis: OrderAIAnalysisResult | null
  risk: OrderAIAnalysisResult | null
  advice: OrderAIAnalysisResult | null
}>({
  analysis: null,
  risk: null,
  advice: null
})

// 根据订单状态生成可执行按钮。
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

// 状态流转确认文案。
const getTransitionConfirmText = (target: OrderTransitionStatus): string => {
  if (target === 'confirmed') return '确认将该订单状态更新为“已确认”吗？'
  if (target === 'completed') return '确认将该订单状态更新为“已完成”吗？'
  return '确认将该订单状态更新为“已取消”吗？'
}

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

// 返回订单列表页。
const goList = () => {
  router.push('/order')
}

// 跳转订单编辑页（附带来源标记）。
const goEdit = () => {
  const id = Number(route.params.id) || 0
  if (!id) return
  router.push({ path: `/order/edit/${id}`, query: { from: 'detail' } })
}

// 拉取订单详情数据。
const fetchDetail = async () => {
  const id = Number(route.params.id) || 0
  if (!id) {
    message.error('订单编号无效')
    return
  }
  pageLoading.value = true
  try {
    const res = await orderDetailApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单详情加载失败')
      return
    }
    detailData.value = res.data.data
  } catch (_error) {
    message.error('订单详情请求失败')
  } finally {
    pageLoading.value = false
  }
}

// 执行状态流转并刷新详情。
const handleStatusTransition = async (targetStatus: OrderTransitionStatus) => {
  const id = Number(route.params.id) || 0
  if (!id) return

  statusUpdating.value = true
  try {
    const res = await orderStatusUpdateApi({ id, status: targetStatus })
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单状态流转失败')
      return
    }
    message.success('订单状态已更新')
    detailData.value = res.data.data
  } catch (_error) {
    message.error('订单状态流转请求失败')
  } finally {
    statusUpdating.value = false
  }
}

// 调用订单 AI 分析接口，并将结果写入对应模块。
const handleAIAnalyze = async (analysisType: AIType) => {
  const id = Number(route.params.id) || 0
  if (!id) {
    message.error('订单编号无效')
    return
  }

  aiLoadingType.value = analysisType
  try {
    const res = await orderAIAnalysisApi(id, { analysis_type: analysisType })
    if (res.data.code !== 0) {
      message.error(res.data.message || 'AI 分析失败')
      return
    }
    aiResults[analysisType] = res.data.data as OrderAIAnalysisResult
    message.success('AI 分析完成')
  } catch (_error) {
    message.error('AI 分析请求失败')
  } finally {
    aiLoadingType.value = null
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped>
.order-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-result-block {
  line-height: 1.7;
  color: #333;
}

.ai-summary {
  margin-bottom: 8px;
}

.ai-subtitle {
  font-weight: 600;
  margin-top: 8px;
  margin-bottom: 4px;
}

.ai-list {
  margin: 0;
  padding-left: 18px;
}
</style>

