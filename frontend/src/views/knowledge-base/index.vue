<template>
  <div class="kb-page">
    <n-card title="知识库助手" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-tag size="small" :type="indexInfo?.index_loaded ? 'success' : 'warning'">
            {{ indexInfo?.index_loaded ? '索引已加载' : '索引未加载' }}
          </n-tag>
          <n-button :loading="rebuilding" @click="handleRebuildIndex">重建索引</n-button>
        </n-space>
      </template>

      <div class="index-info-bar">
        <n-space align="center" :size="10" wrap>
          <span>索引状态：{{ indexInfo?.index_exists ? '已构建' : '未构建' }}</span>
          <span>文档数：{{ indexInfo?.document_count ?? 0 }}</span>
          <span>片段数：{{ indexInfo?.chunk_count ?? 0 }}</span>
          <span>索引体积：{{ formatBytes(indexInfo?.index_size_bytes || 0) }}</span>
          <span>构建时间：{{ indexInfo?.saved_at || '-' }}</span>
          <span>检索后端：{{ indexInfo?.index_backend || '-' }}</span>
          <span>Embedding：{{ indexInfo?.embedding_backend || '-' }}</span>
        </n-space>
      </div>

      <n-form label-placement="left" label-width="80">
        <n-grid :cols="24" :x-gap="12" :y-gap="10">
          <n-form-item-gi :span="20" label="问题">
            <n-input
              v-model:value="question"
              type="textarea"
              :rows="3"
              placeholder="请输入业务问题，例如：已确认订单迟迟未付款应如何处理？"
              @keydown.ctrl.enter.prevent="handleAsk"
            />
          </n-form-item-gi>
          <n-form-item-gi :span="4" label="TopK">
            <n-input-number v-model:value="topK" :min="1" :max="10" :precision="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi :span="24">
            <n-space justify="end" style="width: 100%">
              <n-button type="primary" :loading="asking" @click="handleAsk">提问</n-button>
              <n-button @click="handleReset">清空</n-button>
            </n-space>
          </n-form-item-gi>
        </n-grid>
      </n-form>
    </n-card>

    <n-grid :cols="24" :x-gap="16" :y-gap="16">
      <n-gi :span="17">
        <n-card title="回答结果（RAG）" :bordered="false" class="answer-card">
          <n-spin :show="asking">
            <n-empty v-if="!result" description="请输入问题并点击提问" />
            <template v-else>
              <div class="answer-meta-grid">
                <div class="meta-item"><span class="meta-label">本次问题：</span>{{ result.question || '-' }}</div>
                <div class="meta-item"><span class="meta-label">回答时间：</span>{{ askedAtText }}</div>
                <div class="meta-item"><span class="meta-label">命中文档数：</span>{{ hitDocCount }}</div>
                <div class="meta-item"><span class="meta-label">命中片段数：</span>{{ allHitChunkCount }}</div>
                <div class="meta-item"><span class="meta-label">当前 TopK：</span>{{ lastTopK }}</div>
              </div>

              <div class="section-title">简要答案</div>
              <div class="answer-text">{{ result.answer || '-' }}</div>

              <div class="section-title">依据说明</div>
              <div class="source-clarify">
                <div v-if="primarySourceText">
                  <span class="source-label">核心依据文档：</span>{{ primarySourceText }}
                </div>
                <div v-if="secondarySourceText">
                  <span class="source-label">其他命中文档：</span>{{ secondarySourceText }}
                </div>
                <div>
                  <span class="source-label">命中片段数：</span>{{ allHitChunkCount }}
                </div>
                <div>
                  <span class="source-label">最高相关度：</span>{{ maxScoreText }}
                </div>
              </div>
              <ul v-if="basisDisplayList.length" class="basis-list">
                <li v-for="(item, index) in basisDisplayList" :key="`basis-${index}`">{{ item }}</li>
              </ul>
              <n-empty v-else size="small" description="暂无依据摘要" />
            </template>
          </n-spin>
        </n-card>
      </n-gi>

      <n-gi :span="7">
        <n-card title="命中文档（点击可筛选片段）" :bordered="false" class="side-card">
          <n-empty v-if="!result?.sources?.length" description="暂无命中文档" />
          <n-space v-else vertical :size="8">
            <n-tag
              v-for="item in result.sources"
              :key="item.source"
              :type="selectedSource === item.source ? 'success' : 'info'"
              style="cursor: pointer"
              @click="handleToggleSourceFilter(item.source)"
            >
              {{ item.source }}（命中 {{ item.hit_count }}）
            </n-tag>
          </n-space>
        </n-card>

        <n-card title="知识库文档" :bordered="false" class="doc-card side-card">
          <n-spin :show="docLoading">
            <n-empty v-if="!documents.length" description="知识库目录暂无文档" />
            <n-data-table
              v-else
              :columns="docColumns"
              :data="documents"
              :pagination="false"
              :max-height="260"
              :row-key="(row: KnowledgeDocumentItem) => row.source"
            />
          </n-spin>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card :title="chunkCardTitle" :bordered="false">
      <template #header-extra>
        <n-space v-if="selectedSource" align="center" :size="8">
          <span class="filter-tip">已按文档过滤：{{ selectedSource }}</span>
          <n-button text type="primary" @click="clearSourceFilter">清除筛选</n-button>
        </n-space>
      </template>
      <n-empty v-if="!result?.retrieved_chunks?.length" description="暂无命中片段" />
      <n-data-table
        v-else
        :columns="chunkColumns"
        :data="filteredChunks"
        :pagination="false"
        :row-key="(row: KnowledgeChunkItem) => row.chunk_id"
        :max-height="360"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识库助手页面：提供结构化问答结果、依据摘要、命中片段与来源文档展示。
 */
import { computed, h, onMounted, ref, type VNodeChild } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
  NEmpty,
  NForm,
  NFormItemGi,
  NGi,
  NGrid,
  NInput,
  NInputNumber,
  NSpace,
  NSpin,
  NTag,
  NTooltip,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import {
  knowledgeAskApi,
  knowledgeDocumentsApi,
  knowledgeIndexInfoApi,
  knowledgeRebuildApi,
  type KnowledgeAskResult,
  type KnowledgeChunkItem,
  type KnowledgeDocumentItem,
  type KnowledgeIndexInfo
} from '@/api/knowledge-base'

const message = useMessage()

// 页面核心状态
const asking = ref(false)
const rebuilding = ref(false)
const docLoading = ref(false)
const question = ref('')
const topK = ref<number | null>(4)
const lastTopK = ref(4)
const askedAtText = ref('-')
const result = ref<KnowledgeAskResult | null>(null)
const documents = ref<KnowledgeDocumentItem[]>([])
const indexInfo = ref<KnowledgeIndexInfo | null>(null)
const selectedSource = ref('')
const expandedChunkMap = ref<Record<string, boolean>>({})

const formatBytes = (size: number) => {
  const n = Number(size || 0)
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

const renderEllipsisCell = (text: string, widthClass = 'cell-ellipsis'): VNodeChild =>
  h(
    NTooltip,
    { trigger: 'hover' },
    {
      trigger: () => h('div', { class: widthClass }, text || '-'),
      default: () => text || '-'
    }
  )

const docColumns: DataTableColumns<KnowledgeDocumentItem> = [
  { title: '文档', key: 'source', minWidth: 180, render: (row) => renderEllipsisCell(row.source) },
  { title: '大小', key: 'size', width: 90, render: (row) => formatBytes(row.size) },
  { title: '更新时间', key: 'updated_at', minWidth: 140 }
]

const chunkColumns: DataTableColumns<KnowledgeChunkItem> = [
  { title: '来源文档', key: 'source', width: 220, render: (row) => renderEllipsisCell(row.source) },
  { title: '相关度', key: 'score', width: 90, render: (row) => row.score.toFixed(4) },
  {
    title: '命中片段',
    key: 'content',
    minWidth: 520,
    // 轻量 Markdown 渲染 + 折叠展开。
    render: (row) => renderChunkContentCell(row)
  }
]

const trimBasisText = (text: string, maxLen = 80) => {
  const normalized = (text || '').replace(/\s+/g, ' ').trim()
  if (!normalized) return ''
  if (normalized.length <= maxLen) return normalized
  return `${normalized.slice(0, maxLen).trimEnd()}...`
}

const uniqueKeepOrder = (items: string[]) => {
  const seen = new Set<string>()
  const list: string[] = []
  for (const item of items) {
    const value = (item || '').trim()
    if (!value || seen.has(value)) continue
    seen.add(value)
    list.push(value)
  }
  return list
}

const dedupeSourceInBasisText = (text: string) => {
  const normalized = (text || '').trim()
  if (!normalized) return ''
  // 仅处理“来源类”文案，避免误改普通依据内容。
  if (!/(来源|依据文档|命中文档)/.test(normalized)) {
    return normalized
  }
  const parts = normalized.split('：')
  if (parts.length < 2) return normalized
  const head = parts[0]
  const sourceText = parts.slice(1).join('：')
  const sourceItems = sourceText
    .split(/[、,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
  const deduped = uniqueKeepOrder(sourceItems)
  return deduped.length ? `${head}：${deduped.join('、')}` : normalized
}

const escapeHtml = (raw: string) =>
  raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

/**
 * 轻量 Markdown 渲染：
 * - 支持 #/##/### 标题
 * - 支持 -/* 无序列表
 * - 支持 1. 2. 有序列表
 * - 其余按普通段落展示
 */
const renderLightMarkdown = (raw: string) => {
  const lines = (raw || '').split(/\r?\n/)
  const html: string[] = []
  let inUl = false
  let inOl = false

  const closeLists = () => {
    if (inUl) {
      html.push('</ul>')
      inUl = false
    }
    if (inOl) {
      html.push('</ol>')
      inOl = false
    }
  }

  for (const lineRaw of lines) {
    const line = lineRaw.trim()
    if (!line) {
      closeLists()
      continue
    }

    const h3 = line.match(/^###\s+(.+)$/)
    const h2 = line.match(/^##\s+(.+)$/)
    const h1 = line.match(/^#\s+(.+)$/)
    const ul = line.match(/^[-*]\s+(.+)$/)
    const ol = line.match(/^\d+\.\s+(.+)$/)

    if (h3 || h2 || h1) {
      closeLists()
      const content = escapeHtml((h3?.[1] || h2?.[1] || h1?.[1] || '').trim())
      const tag = h3 ? 'h6' : h2 ? 'h5' : 'h4'
      html.push(`<${tag}>${content}</${tag}>`)
      continue
    }

    if (ul) {
      if (inOl) {
        html.push('</ol>')
        inOl = false
      }
      if (!inUl) {
        html.push('<ul>')
        inUl = true
      }
      html.push(`<li>${escapeHtml(ul[1].trim())}</li>`)
      continue
    }

    if (ol) {
      if (inUl) {
        html.push('</ul>')
        inUl = false
      }
      if (!inOl) {
        html.push('<ol>')
        inOl = true
      }
      html.push(`<li>${escapeHtml(ol[1].trim())}</li>`)
      continue
    }

    closeLists()
    html.push(`<p>${escapeHtml(line)}</p>`)
  }

  closeLists()
  return html.join('')
}

/**
 * 依据说明展示层兜底：
 * 1. 限制单条长度，避免长段复述；
 * 2. 去重，减少和命中片段区域重复。
 */
const basisDisplayList = computed(() => {
  const rawList = result.value?.basis || []
  const seen = new Set<string>()
  const list: string[] = []
  for (const raw of rawList) {
    const text = trimBasisText(dedupeSourceInBasisText(String(raw || '')), 90)
    if (!text || seen.has(text)) continue
    seen.add(text)
    list.push(text)
    if (list.length >= 4) break
  }
  return list
})

// 依据说明中的来源分层：避免用户误解为仅一个文档参与回答。
const primarySources = computed(() => {
  const explicit = uniqueKeepOrder(result.value?.primary_sources || [])
  if (explicit.length) return explicit
  const all = uniqueKeepOrder((result.value?.sources || []).map((item) => item.source))
  return all.slice(0, 2)
})

const secondarySources = computed(() => {
  const explicit = uniqueKeepOrder(result.value?.secondary_sources || [])
  if (explicit.length) return explicit
  const all = uniqueKeepOrder((result.value?.sources || []).map((item) => item.source))
  const primarySet = new Set(primarySources.value)
  return all.filter((source) => !primarySet.has(source))
})

const allHitChunks = computed(() => result.value?.retrieved_chunks || [])
const filteredChunks = computed(() => {
  if (!selectedSource.value) return allHitChunks.value
  return allHitChunks.value.filter((item) => item.source === selectedSource.value)
})

const allHitChunkCount = computed(() => allHitChunks.value.length)
const hitDocCount = computed(() => (result.value?.sources || []).length)
const maxScore = computed(() => {
  if (!allHitChunks.value.length) return 0
  return allHitChunks.value.reduce((max, item) => Math.max(max, Number(item.score || 0)), 0)
})
const maxScoreText = computed(() => (maxScore.value > 0 ? maxScore.value.toFixed(4) : '-'))

const primarySourceText = computed(() => primarySources.value.join('、'))
const secondarySourceText = computed(() => secondarySources.value.join('、'))

const chunkCardTitle = computed(() => {
  if (!selectedSource.value) return '命中知识片段'
  return `命中知识片段（${filteredChunks.value.length} 条）`
})

const isChunkExpanded = (chunkId: string) => Boolean(expandedChunkMap.value[chunkId])
const toggleChunkExpanded = (chunkId: string) => {
  expandedChunkMap.value[chunkId] = !expandedChunkMap.value[chunkId]
}

const getChunkDisplayContent = (row: KnowledgeChunkItem) => {
  const raw = String(row.content || '')
  if (isChunkExpanded(row.chunk_id)) return raw
  if (raw.length <= 220) return raw
  return `${raw.slice(0, 220)}...`
}

const renderChunkContentCell = (row: KnowledgeChunkItem): VNodeChild => {
  const raw = String(row.content || '')
  const display = getChunkDisplayContent(row)
  const needToggle = raw.length > 220
  return h('div', { class: 'chunk-cell' }, [
    h('div', { class: 'chunk-markdown', innerHTML: renderLightMarkdown(display) }),
    needToggle
      ? h(
          NButton,
          {
            text: true,
            size: 'tiny',
            type: 'primary',
            onClick: () => toggleChunkExpanded(row.chunk_id)
          },
          { default: () => (isChunkExpanded(row.chunk_id) ? '收起' : '展开') }
        )
      : null
  ])
}

const handleToggleSourceFilter = (source: string) => {
  selectedSource.value = selectedSource.value === source ? '' : source
}

const clearSourceFilter = () => {
  selectedSource.value = ''
}

const nowDateTimeText = () => {
  const now = new Date()
  const y = now.getFullYear()
  const m = `${now.getMonth() + 1}`.padStart(2, '0')
  const d = `${now.getDate()}`.padStart(2, '0')
  const hh = `${now.getHours()}`.padStart(2, '0')
  const mm = `${now.getMinutes()}`.padStart(2, '0')
  const ss = `${now.getSeconds()}`.padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}

const fetchDocuments = async () => {
  docLoading.value = true
  try {
    const res = await knowledgeDocumentsApi()
    if (res.data.code !== 0) {
      message.error(res.data.message || '知识库文档加载失败')
      return
    }
    documents.value = (res.data?.data?.documents || []) as KnowledgeDocumentItem[]
  } catch (_error) {
    message.error('知识库文档请求失败')
  } finally {
    docLoading.value = false
  }
}

// 获取索引状态信息：用于展示索引加载状态与构建时间。
const fetchIndexInfo = async () => {
  try {
    const res = await knowledgeIndexInfoApi()
    if (res.data.code !== 0) {
      message.error(res.data.message || '索引状态加载失败')
      return
    }
    indexInfo.value = (res.data?.data || null) as KnowledgeIndexInfo | null
  } catch (_error) {
    message.error('索引状态请求失败')
  }
}

const handleRebuildIndex = async () => {
  rebuilding.value = true
  try {
    const res = await knowledgeRebuildApi()
    if (res.data.code !== 0) {
      message.error(res.data.message || '重建索引失败')
      return
    }
    await fetchDocuments()
    await fetchIndexInfo()
    const data = res.data?.data || {}
    message.success(`索引重建完成：文档 ${data.document_count || 0}，片段 ${data.chunk_count || 0}`)
  } catch (_error) {
    message.error('重建索引请求失败')
  } finally {
    rebuilding.value = false
  }
}

const handleAsk = async () => {
  const q = question.value.trim()
  if (!q) {
    message.warning('请输入问题')
    return
  }

  asking.value = true
  try {
    const res = await knowledgeAskApi({ question: q, top_k: Number(topK.value || 4) })
    if (res.data.code !== 0) {
      message.error(res.data.message || '知识库问答失败')
      return
    }
    result.value = res.data.data as KnowledgeAskResult
    askedAtText.value = nowDateTimeText()
    lastTopK.value = Number(topK.value || 4)
    selectedSource.value = ''
    expandedChunkMap.value = {}
  } catch (_error) {
    message.error('知识库问答请求失败')
  } finally {
    asking.value = false
  }
}

const handleReset = () => {
  question.value = ''
  topK.value = 4
  lastTopK.value = 4
  askedAtText.value = '-'
  selectedSource.value = ''
  expandedChunkMap.value = {}
  result.value = null
}

onMounted(() => {
  fetchDocuments()
  fetchIndexInfo()
})
</script>

<style scoped>
.kb-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.answer-card {
  border-left: 2px solid #18a058;
}

.side-card {
  opacity: 0.97;
}

.index-info-bar {
  margin-bottom: 12px;
  padding: 8px 10px;
  border: 1px solid #eef2f6;
  border-radius: 6px;
  color: #666;
  font-size: 12px;
  background: #fafcfe;
}

.answer-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 12px;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #f8fafc;
  border: 1px solid #eef2f6;
  border-radius: 6px;
}

.meta-item {
  color: #333;
  line-height: 1.6;
}

.meta-label {
  color: #666;
}

.section-title {
  margin-top: 8px;
  margin-bottom: 6px;
  font-weight: 600;
  color: #333;
}

.answer-text {
  line-height: 1.8;
  white-space: pre-wrap;
  color: #222;
}

.basis-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.7;
}

.source-clarify {
  margin-bottom: 6px;
  line-height: 1.8;
  color: #444;
}

.source-label {
  color: #666;
}

.doc-card {
  margin-top: 16px;
}

.filter-tip {
  color: #666;
  font-size: 12px;
}

.cell-ellipsis {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chunk-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chunk-markdown {
  line-height: 1.6;
  color: #333;
}

.chunk-markdown :deep(h4),
.chunk-markdown :deep(h5),
.chunk-markdown :deep(h6) {
  margin: 4px 0;
  font-weight: 600;
}

.chunk-markdown :deep(p) {
  margin: 4px 0;
}

.chunk-markdown :deep(ul),
.chunk-markdown :deep(ol) {
  margin: 4px 0 4px 18px;
  padding: 0;
}
</style>
