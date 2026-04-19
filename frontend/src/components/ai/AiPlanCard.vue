<template>
  <n-card title="执行计划" size="small" :bordered="true" class="plan-card">
    <n-space vertical :size="10">
      <n-space align="center" wrap>
        <n-tag type="info" size="small">任务类型：{{ plan?.task_type || '-' }}</n-tag>
        <n-tag :type="plan?.need_rag ? 'warning' : 'success'" size="small">
          {{ plan?.need_rag ? '含知识检索' : '无需知识检索' }}
        </n-tag>
      </n-space>

      <n-steps size="small" :current="planAgents.length">
        <n-step v-for="agent in planAgents" :key="agent" :title="agent" />
      </n-steps>

      <n-descriptions :column="1" size="small" label-placement="left" bordered>
        <n-descriptions-item label="执行 Agent">
          <n-space v-if="planAgents.length" size="small" wrap>
            <n-tag v-for="agent in planAgents" :key="`tag-${agent}`" size="small" type="default">
              {{ agent }}
            </n-tag>
          </n-space>
          <span v-else>-</span>
        </n-descriptions-item>
        <n-descriptions-item label="规划原因">{{ plan?.reason || '-' }}</n-descriptions-item>
      </n-descriptions>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
// 执行计划卡片：使用步骤条和标签展示 Agent 编排计划，便于演示工作流。
import { computed } from 'vue'
import { NCard, NDescriptions, NDescriptionsItem, NSpace, NStep, NSteps, NTag } from 'naive-ui'
import type { AIPlan } from '@/types/ai'

const props = defineProps<{
  plan?: AIPlan | null
}>()

const planAgents = computed(() => props.plan?.agents || [])
</script>

<style scoped>
.plan-card {
  width: 100%;
}
</style>
