<template>
  <div class="order-page">
    <n-card title="订单管理" :bordered="false">
      <div class="search-area">
        <n-form class="search-form" :model="searchForm" label-placement="left" label-width="90">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="12" label="关键词">
              <n-input
                v-model:value="searchForm.keyword"
                placeholder="订单编号/客户名称"
                clearable
                @keyup.enter="handleSearch"
              />
            </n-form-item-gi>
            <n-form-item-gi :span="6" label="订单状态">
              <n-select v-model:value="searchForm.status" :options="statusOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="6">
              <n-space justify="end" style="width: 100%">
                <n-button type="primary" @click="handleSearch">搜索</n-button>
                <n-button @click="handleReset">重置</n-button>
              </n-space>
            </n-form-item-gi>
          </n-grid>
        </n-form>
      </div>

      <div class="action-area">
        <n-button type="primary" @click="goCreate">新建订单</n-button>
      </div>

      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="tableLoading"
        :row-key="(row: OrderListItem) => row.id"
        remote
      />

      <div class="pagination-area">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          @update:page="fetchList"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 订单管理列表页：提供订单查询、状态流转、详情、编辑与删除能力。
import { h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NTag,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import { orderDeleteApi, orderListApi, orderStatusUpdateApi, type OrderListItem } from '@/api/order'
import { ORDER_STATUS_OPTIONS, getOrderStatusLabel, getOrderStatusTagType } from '@/constants/enums'

type TransitionAction = {
  label: string
  target: 'confirmed' | 'completed' | 'cancelled'
  type: 'info' | 'success' | 'warning'
}

const message = useMessage()
const router = useRouter()

// 列表加载状态与状态流转中的订单编号
const tableLoading = ref(false)
const statusUpdatingId = ref<number | null>(null)

// 搜索状态
const searchForm = reactive({
  keyword: '',
  status: null as string | null
})

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 列表数据
const tableData = ref<OrderListItem[]>([])
const statusOptions = ORDER_STATUS_OPTIONS

// 获取状态流转按钮配置：包含“标记完成”和“取消订单”。
const getTransitionActions = (status: string): TransitionAction[] => {
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
}

// 状态流转确认文案。
const getTransitionConfirmText = (target: TransitionAction['target']): string => {
  if (target === 'confirmed') return '确认将该订单状态更新为“已确认”吗？'
  if (target === 'completed') return '确认将该订单状态更新为“已完成”吗？'
  return '确认将该订单状态更新为“已取消”吗？'
}

// 执行状态流转。
const handleStatusTransition = async (row: OrderListItem, target: TransitionAction['target']) => {
  statusUpdatingId.value = row.id
  try {
    const res = await orderStatusUpdateApi({ id: row.id, status: target })
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单状态流转失败')
      return
    }
    message.success('订单状态已更新')
    await fetchList()
  } catch (_error) {
    message.error('订单状态流转请求失败')
  } finally {
    statusUpdatingId.value = null
  }
}

const columns: DataTableColumns<OrderListItem> = [
  { title: '订单编号', key: 'order_no', minWidth: 180 },
  { title: '客户名称', key: 'customer_name', minWidth: 140 },
  {
    title: '订单状态',
    key: 'status',
    width: 110,
    render: (row) =>
      h(
        NTag,
        { type: getOrderStatusTagType(row.status), size: 'small' },
        { default: () => getOrderStatusLabel(row.status) }
      )
  },
  { title: '明细数量', key: 'item_count', width: 100 },
  {
    title: '订单总金额',
    key: 'total_amount',
    width: 130,
    render: (row) => `¥${Number(row.total_amount || 0).toFixed(2)}`
  },
  { title: '创建时间', key: 'created_at', minWidth: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 380,
    fixed: 'right',
    render: (row) =>
      h(NSpace, { wrap: false }, {
        default: () => {
          const transitionButtons = getTransitionActions(row.status).map((action) =>
            h(
              NPopconfirm,
              { onPositiveClick: () => handleStatusTransition(row, action.target) },
              {
                trigger: () =>
                  h(
                    NButton,
                    {
                      size: 'small',
                      tertiary: true,
                      type: action.type,
                      loading: statusUpdatingId.value === row.id
                    },
                    { default: () => action.label }
                  ),
                default: () => getTransitionConfirmText(action.target)
              }
            )
          )

          return [
            h(
              NButton,
              { size: 'small', tertiary: true, onClick: () => goDetail(row.id) },
              { default: () => '详情' }
            ),
            h(
              NButton,
              { size: 'small', tertiary: true, type: 'primary', onClick: () => goEdit(row.id) },
              { default: () => '编辑' }
            ),
            ...transitionButtons,
            h(
              NPopconfirm,
              { onPositiveClick: () => handleDelete(row.id) },
              {
                trigger: () =>
                  h(
                    NButton,
                    { size: 'small', tertiary: true, type: 'error' },
                    { default: () => '删除' }
                  ),
                default: () => '确认删除该订单吗？'
              }
            )
          ]
        }
      })
  }
]

// 获取订单列表。
const fetchList = async () => {
  tableLoading.value = true
  try {
    const res = await orderListApi({
      keyword: searchForm.keyword.trim(),
      status: searchForm.status || '',
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单列表加载失败')
      return
    }
    tableData.value = res.data?.data?.list || []
    pagination.total = res.data?.data?.total || 0
  } catch (_error) {
    message.error('订单列表请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 搜索
const handleSearch = async () => {
  pagination.page = 1
  await fetchList()
}

// 重置
const handleReset = async () => {
  searchForm.keyword = ''
  searchForm.status = null
  pagination.page = 1
  await fetchList()
}

// 分页大小变更
const handlePageSizeChange = async (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  await fetchList()
}

const goCreate = () => router.push('/order/create')
const goDetail = (id: number) => router.push(`/order/detail/${id}`)
const goEdit = (id: number) => router.push(`/order/edit/${id}`)

// 删除订单
const handleDelete = async (id: number) => {
  try {
    const res = await orderDeleteApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || '删除订单失败')
      return
    }
    message.success('删除订单成功')
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    await fetchList()
  } catch (_error) {
    message.error('删除订单请求失败')
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.order-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-area {
  margin-bottom: 12px;
}

.search-form :deep(.n-form-item-label__text) {
  white-space: nowrap;
}

.search-form :deep(.n-input .n-input-wrapper) {
  align-items: center;
}

.search-form :deep(.n-input .n-input__input-el) {
  height: 34px;
  line-height: 34px;
  padding-top: 0;
  padding-bottom: 0;
}

.search-form :deep(.n-input .n-input__placeholder) {
  line-height: 34px;
}

.search-form :deep(.n-base-selection .n-base-selection-label),
.search-form :deep(.n-base-selection .n-base-selection-placeholder) {
  line-height: 34px;
}

.action-area {
  margin-bottom: 12px;
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>

