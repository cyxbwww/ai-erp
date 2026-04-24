<template>
  <n-space vertical :size="12" class="ai-analysis-panel">
    <n-card size="small" :bordered="true" class="summary-card">
      <template #header>
        <div class="summary-header">
          <span class="summary-title">AI 综合分析</span>
          <n-space :size="8" align="center">
            <n-tag type="info" size="small">{{ result?.task_type || '-' }}</n-tag>
            <n-button size="tiny" tertiary @click="copySummary" :disabled="!summaryText">复制结论</n-button>
            <n-button size="tiny" type="primary" @click="emit('retry')" :loading="loading">重新分析</n-button>
          </n-space>
        </div>
      </template>

      <n-alert v-if="error" type="error" :show-icon="false" style="margin-bottom: 8px">
        {{ error }}
      </n-alert>

      <template v-if="loading">
        <n-space vertical :size="8">
          <n-skeleton text :repeat="3" />
        </n-space>
      </template>

      <template v-else>
        <n-grid v-if="highlightCards.length" :cols="24" :x-gap="12" :y-gap="12" class="highlight-grid">
          <n-gi v-for="card in highlightCards" :key="card.title" :span="6">
            <n-card size="small" :bordered="true" class="highlight-item">
              <div class="highlight-title">{{ card.title }}</div>
              <div class="highlight-value">{{ card.value }}</div>
            </n-card>
          </n-gi>
        </n-grid>

        <div v-if="summaryText" class="summary-text">{{ summaryText }}</div>
        <n-empty v-else description="暂无分析结果" />
      </template>
    </n-card>

    <template v-if="loading">
      <n-card title="执行计划" size="small" :bordered="true">
        <n-skeleton text :repeat="4" />
      </n-card>
      <n-card title="Agent 结果" size="small" :bordered="true">
        <n-space vertical :size="10">
          <n-skeleton text :repeat="5" />
          <n-skeleton text :repeat="5" />
        </n-space>
      </n-card>
    </template>

    <template v-else>
      <AiPlanCard :plan="result?.plan" />

      <n-card title="Agent 结果" size="small" :bordered="true">
        <n-space vertical :size="10">
          <AiBlockRenderer
            v-for="(block, index) in agentBlocks"
            :key="`agent-block-${index}-${block.agent_name || 'unknown'}`"
            :block="block"
            :default-collapsed="shouldDefaultCollapse(block.agent_name)"
            @task-created="emit('task-created', $event)"
          />
          <n-empty v-if="!agentBlocks.length" description="暂无 Agent 结果" />
        </n-space>
      </n-card>
    </template>
  </n-space>
</template>

<script setup lang="ts">
// AI 工作流面板：按“概览-计划-结果”三区域展示多 Agent 执行过程。
import { computed } from 'vue'
import { NAlert, NButton, NCard, NEmpty, NGi, NGrid, NSkeleton, NSpace, NTag, useMessage } from 'naive-ui'
import AiBlockRenderer from './AiBlockRenderer.vue'
import AiPlanCard from './AiPlanCard.vue'
import type { AIChatResult, UIBlock } from '@/types/ai'

type SceneType = 'customer' | 'order' | 'auto'

type HighlightCard = {
  title: string
  value: string
}

const props = withDefaults(
  defineProps<{
    loading?: boolean
    result?: AIChatResult | null
    error?: string
    sceneType?: SceneType
  }>(),
  {
    loading: false,
    result: null,
    error: '',
    sceneType: 'auto'
  }
)

const emit = defineEmits<{
  (event: 'retry'): void
  // 透传任务创建成功事件，由业务页面决定是否刷新关联数据。
  (event: 'task-created', task: Record<string, any>): void
}>()

const message = useMessage()

// 综合结论优先取 ui_blocks 的 summary，再回退 result.summary。
const summaryText = computed(() => {
  const blocks = props.result?.ui_blocks || []
  const summaryBlock = blocks.find((item) => item.type === 'summary')
  return summaryBlock?.content || props.result?.summary || ''
})

// 当后端未返回 ui_blocks 时，从 agent_outputs 组装兜底块。
const getFallbackBlocks = (result: AIChatResult): UIBlock[] => {
  const outputs = result.agent_outputs || {}
  return Object.entries(outputs).map(([agentName, data]) => ({
    type: 'agent_result',
    title: agentName,
    agent_name: agentName,
    data: (data || {}) as Record<string, any>
  }))
}

// 结果区只渲染 agent_result，summary 已在概览区单独高亮。
const agentBlocks = computed<UIBlock[]>(() => {
  const result = props.result
  if (!result) return []

  const uiBlocks = (result.ui_blocks || []).filter((item) => item.type === 'agent_result')
  if (uiBlocks.length) return uiBlocks
  return getFallbackBlocks(result)
})

// 聚合 Agent 数据，便于提取顶部关键结论卡片。
const agentDataMap = computed<Record<string, Record<string, any>>>(() => {
  const map: Record<string, Record<string, any>> = {}
  agentBlocks.value.forEach((block) => {
    if (block.agent_name) map[block.agent_name] = (block.data || {}) as Record<string, any>
  })
  const fallbackOutputs = props.result?.agent_outputs || {}
  Object.entries(fallbackOutputs).forEach(([agentName, data]) => {
    if (!map[agentName] && data && typeof data === 'object') {
      map[agentName] = data as Record<string, any>
    }
  })
  return map
})

const toText = (value: unknown): string => {
  if (value == null) return '-'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return value.map((item) => toText(item)).join('；') || '-'
  if (typeof value === 'object') {
    const obj = value as Record<string, any>
    if (obj.label) return String(obj.label)
    if (obj.name) return String(obj.name)
    return Object.values(obj)
      .map((item) => toText(item))
      .filter(Boolean)
      .join('；') || '-'
  }
  return String(value)
}

const getFirstListText = (value: unknown): string => {
  if (Array.isArray(value) && value.length) return toText(value[0])
  return toText(value)
}

const isCustomerScene = computed(() => {
  if (props.sceneType === 'customer') return true
  if (props.sceneType === 'order') return false
  return (props.result?.task_type || '').includes('customer')
})

const customerHighlightCards = computed<HighlightCard[]>(() => {
  const customerInsight = agentDataMap.value.customer_insight_agent || {}
  const followup = agentDataMap.value.followup_strategy_agent || {}
  const task = agentDataMap.value.task_execution_agent || {}

  return [
    {
      title: '客户阶段',
      value: toText(customerInsight.customer_stage || customerInsight.stage || '-')
    },
    {
      title: '意向等级',
      value: toText(customerInsight.intent_level || '-')
    },
    {
      title: '风险提示',
      value: getFirstListText(customerInsight.risks || followup.risk_alert || '-')
    },
    {
      title: '下一步动作',
      value: toText(followup.next_action || task.title || '-')
    }
  ]
})

const orderHighlightCards = computed<HighlightCard[]>(() => {
  const orderAnalysis = agentDataMap.value.order_analysis_agent || {}

  return [
    {
      title: '风险评分',
      value: toText(orderAnalysis.risk_score ?? '-')
    },
    {
      title: '风险等级',
      value: toText(orderAnalysis.risk_level || '-')
    },
    {
      title: '核心风险点',
      value: getFirstListText(orderAnalysis.risk_factors || orderAnalysis.risk_points || '-')
    },
    {
      title: '建议动作',
      value: getFirstListText(orderAnalysis.recommendations || '-')
    }
  ]
})

const highlightCards = computed(() => (isCustomerScene.value ? customerHighlightCards.value : orderHighlightCards.value))

// 默认折叠知识检索与客户洞察，默认展开策略、任务执行和订单分析。
const shouldDefaultCollapse = (agentName?: string): boolean => {
  if (!agentName) return false
  if (['followup_strategy_agent', 'task_execution_agent', 'order_analysis_agent'].includes(agentName)) return false
  return ['knowledge_rag_agent', 'customer_insight_agent'].includes(agentName)
}

// 复制综合结论，便于演示和汇报复用。
const copySummary = async () => {
  if (!summaryText.value) {
    message.warning('暂无可复制的综合结论')
    return
  }
  try {
    await navigator.clipboard.writeText(summaryText.value)
    message.success('综合结论已复制')
  } catch (_error) {
    message.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
.ai-analysis-panel {
  width: 100%;
}

.summary-card {
  background: linear-gradient(180deg, #f7fbff 0%, #ffffff 100%);
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.summary-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2d3d;
}

.highlight-grid {
  margin-bottom: 10px;
}

.highlight-item :deep(.n-card__content) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.highlight-title {
  color: #6b7280;
  font-size: 12px;
}

.highlight-value {
  margin-top: 6px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.6;
  word-break: break-word;
}

.summary-text {
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}
</style>
