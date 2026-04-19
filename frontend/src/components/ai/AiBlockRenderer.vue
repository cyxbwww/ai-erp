<template>
  <n-card size="small" :title="cardTitle" :bordered="true" class="ai-block-card" :class="`agent-${agentName || 'unknown'}`">
    <template #header-extra>
      <n-space size="small" align="center">
        <n-tag v-if="agentName" size="small" :type="getAgentTagType(agentName)">{{ agentName }}</n-tag>
        <n-button size="tiny" tertiary @click="copyBlockJson">复制 JSON</n-button>
      </n-space>
    </template>

    <n-collapse :default-expanded-names="defaultCollapsed ? [] : ['business']">
      <n-collapse-item name="business" title="业务结果">
        <template v-if="agentName === 'customer_insight_agent'">
          <n-space vertical :size="8">
            <div class="business-row"><span class="label">客户阶段：</span><span>{{ getText(data.customer_stage) }}</span></div>
            <div class="business-row"><span class="label">意向等级：</span><span>{{ getText(data.intent_level) }}</span></div>
            <div class="business-row"><span class="label">主要关注点：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.main_concerns)" :key="`concern-${idx}`">{{ item }}</li>
            </ul>
            <div class="business-row"><span class="label">风险提示：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.risks)" :key="`risk-${idx}`">{{ item }}</li>
            </ul>
            <div class="business-summary">{{ getText(data.analysis_summary) }}</div>
          </n-space>
        </template>

        <template v-else-if="agentName === 'followup_strategy_agent'">
          <n-space vertical :size="8">
            <div class="business-row"><span class="label">优先级：</span><span>{{ getText(data.priority) }}</span></div>
            <div class="business-row"><span class="label">下一步动作：</span><span>{{ getText(data.next_action) }}</span></div>
            <div class="business-row"><span class="label">建议跟进时间：</span><span>{{ getText(data.recommended_follow_up_time) }}</span></div>
            <div class="business-row"><span class="label">沟通话术：</span></div>
            <div class="long-text">{{ getLongText('script', data.communication_script) }}</div>
            <n-button v-if="shouldCollapseText(data.communication_script)" text size="tiny" type="primary" @click="toggleExpand('script')">
              {{ isExpanded('script') ? '收起' : '展开' }}
            </n-button>
            <div class="business-row"><span class="label">风险提醒：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.risk_alert)" :key="`alert-${idx}`">{{ item }}</li>
            </ul>
            <div class="business-summary">{{ getText(data.strategy_summary) }}</div>
          </n-space>
        </template>

        <template v-else-if="agentName === 'order_analysis_agent'">
          <n-space vertical :size="8">
            <div class="business-row"><span class="label">风险评分：</span><span>{{ getText(data.risk_score) }}</span></div>
            <div class="business-row"><span class="label">风险等级：</span><span>{{ getText(data.risk_level) }}</span></div>
            <div class="business-row"><span class="label">订单状态：</span><span>{{ getText(data.order_status) }}</span></div>
            <div class="business-row"><span class="label">核心风险：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.risk_factors || data.risk_points)" :key="`order-risk-${idx}`">{{ item }}</li>
            </ul>
            <div class="business-row"><span class="label">建议动作：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.recommendations)" :key="`order-rec-${idx}`">{{ item }}</li>
            </ul>
            <div class="business-summary">{{ getText(data.analysis_summary) }}</div>
          </n-space>
        </template>

        <template v-else-if="agentName === 'knowledge_rag_agent'">
          <n-space vertical :size="8">
            <div class="business-row"><span class="label">检索问题：</span><span>{{ getText(data.query) }}</span></div>
            <div class="business-row"><span class="label">知识摘要：</span><span>{{ getText(data.summary) }}</span></div>
            <div class="business-row"><span class="label">引用来源：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.references)" :key="`ref-${idx}`">{{ item }}</li>
            </ul>
            <div class="business-row"><span class="label">召回片段：</span></div>
            <ul class="biz-list">
              <li v-for="(item, idx) in getList(data.hits)" :key="`hit-${idx}`">{{ item }}</li>
            </ul>
          </n-space>
        </template>

        <template v-else-if="agentName === 'task_execution_agent'">
          <n-space vertical :size="8">
            <div class="business-row"><span class="label">任务类型：</span><span>{{ getText(data.task_type) }}</span></div>
            <div class="business-row"><span class="label">任务标题：</span><span>{{ getText(data.title) }}</span></div>
            <div class="business-row"><span class="label">负责人建议：</span><span>{{ getText(data.suggested_owner) }}</span></div>
            <div class="business-row"><span class="label">截止时间建议：</span><span>{{ getText(data.suggested_due_time) }}</span></div>
            <div class="business-row"><span class="label">任务描述：</span></div>
            <div class="long-text">{{ getLongText('task_desc', data.description) }}</div>
            <n-button v-if="shouldCollapseText(data.description)" text size="tiny" type="primary" @click="toggleExpand('task_desc')">
              {{ isExpanded('task_desc') ? '收起' : '展开' }}
            </n-button>
            <div class="business-row"><span class="label">提醒文案：</span><span>{{ getText(data.reminder_text) }}</span></div>
          </n-space>
        </template>

        <template v-else>
          <n-space vertical :size="8">
            <div v-for="item in genericEntries" :key="item.key" class="business-row">
              <span class="label">{{ item.key }}：</span>
              <span>{{ item.value }}</span>
            </div>
          </n-space>
        </template>
      </n-collapse-item>

      <n-collapse-item name="json" title="查看原始 JSON">
        <pre class="json-block">{{ jsonPreview }}</pre>
      </n-collapse-item>
    </n-collapse>
  </n-card>
</template>

<script setup lang="ts">
// Agent 结果块渲染器：优先业务化展示，保留原始 JSON 折叠区用于调试。
import { computed, reactive } from 'vue'
import { NButton, NCard, NCollapse, NCollapseItem, NSpace, NTag, useMessage } from 'naive-ui'
import type { UIBlock } from '@/types/ai'

const MAX_TEXT_LENGTH = 200

const props = withDefaults(
  defineProps<{
    block: UIBlock
    defaultCollapsed?: boolean
  }>(),
  {
    defaultCollapsed: false
  }
)

const message = useMessage()
const expandedMap = reactive<Record<string, boolean>>({})

const agentName = computed(() => props.block.agent_name || '')
const data = computed<Record<string, any>>(() => (props.block.data || {}) as Record<string, any>)

const titleMap: Record<string, string> = {
  customer_insight_agent: '客户洞察卡片',
  followup_strategy_agent: '跟进策略卡片',
  order_analysis_agent: '订单分析卡片',
  knowledge_rag_agent: '知识支持卡片',
  task_execution_agent: '任务执行卡片'
}

const cardTitle = computed(() => {
  if (props.block.title) return props.block.title
  if (titleMap[agentName.value]) return titleMap[agentName.value]
  return agentName.value || 'Agent 结果'
})

const toText = (value: unknown): string => {
  if (value == null) return '-'
  if (typeof value === 'string') return value || '-'
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return value.map((item) => toText(item)).join('；') || '-'
  if (typeof value === 'object') {
    const obj = value as Record<string, any>
    if (obj.label) return String(obj.label)
    if (obj.name) return String(obj.name)
    return Object.entries(obj)
      .map(([k, v]) => `${k}:${toText(v)}`)
      .join('；')
  }
  return String(value)
}

const getText = (value: unknown): string => toText(value)

const getList = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    if (!value.length) return ['-']
    return value.map((item) => toText(item))
  }
  if (value == null || value === '') return ['-']
  return [toText(value)]
}

const isExpanded = (key: string): boolean => !!expandedMap[key]

const toggleExpand = (key: string) => {
  expandedMap[key] = !expandedMap[key]
}

const getLongText = (key: string, value: unknown): string => {
  const text = toText(value)
  if (text.length <= MAX_TEXT_LENGTH) return text
  if (isExpanded(key)) return text
  return `${text.slice(0, MAX_TEXT_LENGTH)}...`
}

const shouldCollapseText = (value: unknown): boolean => toText(value).length > MAX_TEXT_LENGTH

const genericEntries = computed(() => {
  return Object.entries(data.value).map(([key, value]) => ({
    key,
    value: toText(value)
  }))
})

const jsonPreview = computed(() => JSON.stringify(data.value, null, 2))

const getAgentTagType = (name: string): 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error' => {
  if (name === 'followup_strategy_agent') return 'success'
  if (name === 'task_execution_agent') return 'primary'
  if (name === 'knowledge_rag_agent') return 'warning'
  if (name === 'order_analysis_agent') return 'error'
  if (name === 'customer_insight_agent') return 'info'
  return 'default'
}

// 复制当前 Agent 结构化结果，便于演示时快速粘贴。
const copyBlockJson = async () => {
  try {
    await navigator.clipboard.writeText(jsonPreview.value)
    message.success('Agent JSON 已复制')
  } catch (_error) {
    message.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
.ai-block-card {
  width: 100%;
}

.business-row {
  line-height: 1.8;
  color: #374151;
  word-break: break-word;
}

.label {
  color: #6b7280;
  font-weight: 500;
}

.biz-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.7;
  color: #374151;
}

.long-text {
  border: 1px solid #eceff5;
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 12px;
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
}

.business-summary {
  margin-top: 4px;
  border-left: 3px solid #dbeafe;
  padding-left: 10px;
  color: #1f2d3d;
  line-height: 1.7;
}

.json-block {
  margin: 0;
  padding: 10px;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  line-height: 1.5;
  font-size: 12px;
  overflow: auto;
}
</style>
