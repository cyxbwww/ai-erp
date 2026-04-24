<template>
  <div class="order-page">
    <n-card title="订单管理" :bordered="false">
      <div class="search-area">
        <n-form class="search-form" :model="searchForm" label-placement="left" label-width="88">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="6" label="订单编号">
              <n-input v-model:value="searchForm.orderNo" placeholder="请输入订单编号" clearable @keyup.enter="handleSearch" />
            </n-form-item-gi>

            <n-form-item-gi :span="6" label="客户名称">
              <n-input v-model:value="searchForm.customerName" placeholder="请输入客户名称" clearable @keyup.enter="handleSearch" />
            </n-form-item-gi>

            <n-form-item-gi :span="6" label="订单状态">
              <n-select v-model:value="searchForm.status" :options="statusOptions" clearable placeholder="请选择订单状态" />
            </n-form-item-gi>

            <n-form-item-gi :span="6" label="下单时间">
              <n-date-picker
                v-model:value="searchForm.orderTimeRange"
                type="daterange"
                clearable
                style="width: 100%"
                :is-date-disabled="() => false"
              />
            </n-form-item-gi>

            <n-form-item-gi :span="6" label="金额区间">
              <n-input-number v-model:value="searchForm.amountMin" :min="0" :precision="2" style="width: 100%" placeholder="最低金额" />
            </n-form-item-gi>

            <n-form-item-gi :span="6" label="至">
              <n-input-number v-model:value="searchForm.amountMax" :min="0" :precision="2" style="width: 100%" placeholder="最高金额" />
            </n-form-item-gi>

            <n-form-item-gi :span="12">
              <n-space justify="end" style="width: 100%">
                <n-button type="primary" @click="handleSearch">搜索</n-button>
                <n-button @click="handleReset">重置</n-button>
                <n-button @click="handleRefresh">刷新</n-button>
              </n-space>
            </n-form-item-gi>
          </n-grid>
        </n-form>
      </div>

      <div class="action-area">
        <n-space>
          <n-button type="primary" @click="goCreate">新建订单</n-button>
          <n-popconfirm @positive-click="handleBatchDelete" :show-icon="true">
            <template #trigger>
              <n-button :disabled="!checkedRowKeys.length" type="error" secondary :loading="batchDeleting">批量删除</n-button>
            </template>
            确认删除选中的 {{ checkedRowKeys.length }} 条订单吗？
          </n-popconfirm>
          <n-button :disabled="!checkedRowKeys.length" @click="handleBatchExport">批量导出</n-button>
        </n-space>
      </div>

      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="tableLoading"
        :row-key="(row: OrderListItem) => row.id"
        :locale="{ emptyText: '暂无订单数据，请调整筛选条件后重试' }"
        :checked-row-keys="checkedRowKeys"
        @update:checked-row-keys="handleCheckedRowKeysUpdate"
      />

      <div class="pagination-area">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 订单管理列表页：增强筛选、状态操作、批量能力，并与详情页共享订单运行态。
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NDropdown,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NTag,
  useMessage,
  type DataTableColumns,
  type DropdownOption
} from 'naive-ui'
import { orderDeleteApi, orderListApi, orderStatusUpdateApi, type OrderListItem } from '@/api/order'
import { ORDER_STATUS_OPTIONS, getOrderStatusLabel, getOrderStatusTagType } from '@/constants/enums'
import {
  ensureOrderRuntimeStates,
  getOrderRuntimeState,
  getOrderRuntimeStateMap,
  patchOrderRuntimeState,
  setOrderRuntimeStateMap,
  type OrderRuntimeState,
  type OrderPaymentStatus,
  type OrderShippingStatus
} from '@/utils/order-runtime-state'

type MoreActionKey = 'confirm_paid' | 'confirm_shipped' | 'complete_order' | 'cancel_order'

const message = useMessage()
const router = useRouter()

// 列表与批量操作加载状态
const tableLoading = ref(false)
const batchDeleting = ref(false)
const statusUpdatingId = ref<number | null>(null)

// 筛选表单：支持状态、时间、金额等组合筛选
const searchForm = reactive({
  orderNo: '',
  customerName: '',
  status: null as string | null,
  orderTimeRange: null as [number, number] | null,
  amountMin: null as number | null,
  amountMax: null as number | null
})

// 分页状态：本页使用前端分页，便于承接扩展筛选
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 原始列表数据与展示数据
const allOrders = ref<OrderListItem[]>([])
const tableData = ref<OrderListItem[]>([])
const checkedRowKeys = ref<number[]>([])
// 订单运行态响应式缓存：避免仅写 localStorage 导致视图不刷新
const runtimeStateMap = ref<Record<number, OrderRuntimeState>>({})

const statusOptions = ORDER_STATUS_OPTIONS

// 已勾选的完整行数据
const checkedRows = computed(() => {
  const keySet = new Set(checkedRowKeys.value)
  return allOrders.value.filter((item) => keySet.has(item.id))
})

// 时间字符串转时间戳：用于时间范围筛选
const parseDateTime = (value: string): number => {
  if (!value) return 0
  const normalized = value.replace(/-/g, '/')
  const time = new Date(normalized).getTime()
  return Number.isNaN(time) ? 0 : time
}

// 读取订单支付状态中文名称
const getPaymentStatusLabel = (status: OrderPaymentStatus): string => {
  if (status === 'paid') return '已付款'
  if (status === 'closed') return '交易关闭'
  return '未付款'
}

// 读取支付状态标签颜色
const getPaymentStatusTagType = (status: OrderPaymentStatus) => {
  if (status === 'paid') return 'success'
  if (status === 'closed') return 'default'
  return 'warning'
}

// 读取发货状态中文名称
const getShippingStatusLabel = (status: OrderShippingStatus): string => (status === 'shipped' ? '已发货' : '未发货')

// 读取发货状态标签颜色
const getShippingStatusTagType = (status: OrderShippingStatus) => (status === 'shipped' ? 'success' : 'warning')

// 获取行级运行态（列表和详情共用）
const syncRuntimeStateMap = () => {
  runtimeStateMap.value = getOrderRuntimeStateMap()
}

const getRuntime = (row: OrderListItem) => runtimeStateMap.value[row.id] || getOrderRuntimeState(row.id)

// 计算商品总件数：后端暂未返回时先用行数近似演示
const getTotalQuantity = (row: OrderListItem): number => Number(row.item_count || 0)

// 根据状态生成“更多操作”下拉项
const getMoreOptions = (row: OrderListItem): DropdownOption[] => {
  const runtime = getRuntime(row)
  const paymentStatus = runtime?.payment_status || 'unpaid'
  const shippingStatus = runtime?.shipping_status || 'unshipped'

  const canConfirmPaid = row.status !== 'cancelled' && row.status !== 'completed' && paymentStatus !== 'paid'
  const canConfirmShipped = row.status === 'confirmed' && paymentStatus === 'paid' && shippingStatus !== 'shipped'
  const canComplete = row.status === 'confirmed'
  const canCancel = row.status === 'draft' || row.status === 'confirmed'

  return [
    { label: '确认付款', key: 'confirm_paid', disabled: !canConfirmPaid },
    { label: '确认发货', key: 'confirm_shipped', disabled: !canConfirmShipped },
    { label: '完成订单', key: 'complete_order', disabled: !canComplete },
    { label: '取消订单', key: 'cancel_order', disabled: !canCancel }
  ]
}

// 获取当前筛选后的列表，并更新分页展示
const refreshTableByFilter = () => {
  const orderNo = searchForm.orderNo.trim().toLowerCase()
  const customerName = searchForm.customerName.trim().toLowerCase()
  const minAmount = searchForm.amountMin
  const maxAmount = searchForm.amountMax
  const timeRange = searchForm.orderTimeRange

  let filtered = allOrders.value.filter((row) => {
    if (orderNo && !String(row.order_no || '').toLowerCase().includes(orderNo)) return false
    if (customerName && !String(row.customer_name || '').toLowerCase().includes(customerName)) return false

    const totalAmount = Number(row.total_amount || 0)
    if (minAmount !== null && totalAmount < minAmount) return false
    if (maxAmount !== null && totalAmount > maxAmount) return false

    if (timeRange?.length === 2) {
      const createdAt = parseDateTime(row.created_at || '')
      const [start, end] = timeRange
      if (!createdAt) return false
      if (createdAt < start || createdAt > end) return false
    }

    return true
  })

  pagination.total = filtered.length
  const startIndex = (pagination.page - 1) * pagination.pageSize
  const endIndex = startIndex + pagination.pageSize
  tableData.value = filtered.slice(startIndex, endIndex)

  // 过滤后清理无效选中项
  const idSet = new Set(allOrders.value.map((item) => item.id))
  checkedRowKeys.value = checkedRowKeys.value.filter((id) => idSet.has(id))
}

// 拉取全部订单（按状态过滤）并在前端执行扩展筛选
const fetchList = async () => {
  tableLoading.value = true
  try {
    const pageSize = 100
    let page = 1
    let loop = true
    const list: OrderListItem[] = []

    while (loop) {
      const res = await orderListApi({
        keyword: '',
        status: searchForm.status || '',
        page,
        page_size: pageSize
      })
      if (res.data.code !== 0) {
        message.error(res.data.message || '订单列表加载失败')
        return
      }

      const currentList = (res.data?.data?.list || []) as OrderListItem[]
      list.push(...currentList)

      if (currentList.length < pageSize) {
        loop = false
      } else {
        page += 1
      }

      // 安全上限：防止异常分页死循环
      if (page > 30) {
        loop = false
      }
    }

    ensureOrderRuntimeStates(list.map((item) => ({ id: item.id, status: item.status })))
    syncRuntimeStateMap()
    allOrders.value = list
    refreshTableByFilter()
  } catch (_error) {
    message.error('订单列表请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 执行状态流转并刷新列表
const handleStatusTransition = async (row: OrderListItem, target: 'confirmed' | 'completed' | 'cancelled') => {
  statusUpdatingId.value = row.id
  try {
    const res = await orderStatusUpdateApi({ id: row.id, status: target })
    if (res.data.code !== 0) {
      message.error(res.data.message || '订单状态流转失败')
      return
    }

    // 同步运行态：状态变更后修正支付/发货展示，避免列表与详情不一致
    if (target === 'cancelled') {
      patchOrderRuntimeState(row.id, { payment_status: 'closed', shipping_status: 'unshipped' })
    }
    if (target === 'completed') {
      patchOrderRuntimeState(row.id, { payment_status: 'paid', shipping_status: 'shipped' })
    }
    syncRuntimeStateMap()

    message.success('订单状态已更新')
    await fetchList()
  } catch (_error) {
    message.error('订单状态流转请求失败')
  } finally {
    statusUpdatingId.value = null
  }
}

// 行级更多操作分发
const handleMoreAction = (action: string | number, row: OrderListItem) => {
  const key = String(action) as MoreActionKey
  const runtime = getRuntime(row)

  if (key === 'confirm_paid') {
    patchOrderRuntimeState(row.id, {
      payment_status: 'paid',
      payment_time: new Date().toLocaleString('zh-CN')
    })
    syncRuntimeStateMap()
    message.success(`订单 ${row.order_no} 已确认付款`)
    refreshTableByFilter()
    return
  }

  if (key === 'confirm_shipped') {
    patchOrderRuntimeState(row.id, {
      shipping_status: 'shipped',
      shipping_time: new Date().toLocaleString('zh-CN')
    })
    syncRuntimeStateMap()
    message.success(`订单 ${row.order_no} 已确认发货`)
    refreshTableByFilter()
    return
  }

  if (key === 'complete_order') {
    handleStatusTransition(row, 'completed')
    return
  }

  if (key === 'cancel_order') {
    const ok = window.confirm(`确认取消订单 ${row.order_no} 吗？`)
    if (ok) {
      handleStatusTransition(row, 'cancelled')
    }
    return
  }

  // 防御分支
  if (runtime) {
    message.warning('当前操作暂不可用')
  }
}

// 删除订单
const handleDelete = async (id: number) => {
  try {
    const res = await orderDeleteApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || '删除订单失败')
      return
    }

    // 清理运行态中已删除订单
    const runtimeMap = getOrderRuntimeStateMap()
    delete runtimeMap[id]
    setOrderRuntimeStateMap(runtimeMap)
    syncRuntimeStateMap()

    message.success('删除订单成功')
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    await fetchList()
  } catch (_error) {
    message.error('删除订单请求失败')
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!checkedRowKeys.value.length) return

  batchDeleting.value = true
  try {
    const tasks = checkedRowKeys.value.map((id) => orderDeleteApi(id))
    const results = await Promise.allSettled(tasks)

    let successCount = 0
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.data.code === 0) {
        successCount += 1
      } else {
        const id = checkedRowKeys.value[index]
        message.error(`订单 ID ${id} 删除失败`)
      }
    })

    const runtimeMap = getOrderRuntimeStateMap()
    checkedRowKeys.value.forEach((id) => {
      delete runtimeMap[id]
    })
    setOrderRuntimeStateMap(runtimeMap)
    syncRuntimeStateMap()

    checkedRowKeys.value = []
    message.success(`批量删除完成，成功 ${successCount} 条`)
    await fetchList()
  } finally {
    batchDeleting.value = false
  }
}

// 批量导出：前端导出 CSV，后续可替换后端文件导出接口
const handleBatchExport = () => {
  if (!checkedRows.value.length) return

  const header = ['订单编号', '客户名称', '订单状态', '支付状态', '发货状态', '订单总金额', '创建时间', '更新时间']
  const rows = checkedRows.value.map((row) => {
    const runtime = getRuntime(row)
    return [
      row.order_no,
      row.customer_name,
      getOrderStatusLabel(row.status),
      getPaymentStatusLabel(runtime?.payment_status || 'unpaid'),
      getShippingStatusLabel(runtime?.shipping_status || 'unshipped'),
      Number(row.total_amount || 0).toFixed(2),
      row.created_at,
      row.updated_at
    ]
  })

  const csv = [header, ...rows]
    .map((line) => line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n')

  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `订单导出_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)

  message.success(`已导出 ${checkedRows.value.length} 条订单`) 
}

// 搜索
const handleSearch = async () => {
  if (searchForm.amountMin !== null && searchForm.amountMax !== null && searchForm.amountMin > searchForm.amountMax) {
    message.warning('最低金额不能大于最高金额')
    return
  }
  pagination.page = 1
  await fetchList()
}

// 重置
const handleReset = async () => {
  searchForm.orderNo = ''
  searchForm.customerName = ''
  searchForm.status = null
  searchForm.orderTimeRange = null
  searchForm.amountMin = null
  searchForm.amountMax = null
  pagination.page = 1
  await fetchList()
}

// 刷新
const handleRefresh = async () => {
  await fetchList()
  message.success('列表已刷新')
}

// 页码变更
const handlePageChange = (page: number) => {
  pagination.page = page
  refreshTableByFilter()
}

// 分页大小变更
const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  refreshTableByFilter()
}

// 更新勾选项
const handleCheckedRowKeysUpdate = (keys: (string | number)[]) => {
  checkedRowKeys.value = keys.map((key) => Number(key)).filter((id) => Number.isFinite(id))
}

const goCreate = () => router.push('/order/create')
const goDetail = (id: number) => router.push(`/order/detail/${id}`)
const goEdit = (id: number) => router.push(`/order/edit/${id}`)

const columns: DataTableColumns<OrderListItem> = [
  { type: 'selection', width: 48 },
  { title: '订单编号', key: 'order_no', minWidth: 180 },
  { title: '客户名称', key: 'customer_name', minWidth: 140 },
  {
    title: '订单状态',
    key: 'status',
    width: 108,
    render: (row) => h(NTag, { type: getOrderStatusTagType(row.status), size: 'small' }, { default: () => getOrderStatusLabel(row.status) })
  },
  {
    title: '支付状态',
    key: 'payment_status',
    width: 100,
    render: (row) => {
      const paymentStatus = getRuntime(row)?.payment_status || 'unpaid'
      return h(NTag, { size: 'small', type: getPaymentStatusTagType(paymentStatus) }, { default: () => getPaymentStatusLabel(paymentStatus) })
    }
  },
  {
    title: '发货状态',
    key: 'shipping_status',
    width: 100,
    render: (row) => {
      const shippingStatus = getRuntime(row)?.shipping_status || 'unshipped'
      return h(NTag, { size: 'small', type: getShippingStatusTagType(shippingStatus) }, { default: () => getShippingStatusLabel(shippingStatus) })
    }
  },
  { title: '商品总件数', key: 'item_count', width: 100, render: (row) => `${getTotalQuantity(row)}` },
  {
    title: '订单总金额',
    key: 'total_amount',
    width: 130,
    render: (row) => `¥${Number(row.total_amount || 0).toFixed(2)}`
  },
  { title: '更新时间', key: 'updated_at', minWidth: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 320,
    fixed: 'right',
    render: (row) =>
      h(NSpace, { wrap: false, size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', tertiary: true, onClick: () => goDetail(row.id) }, { default: () => '详情' }),
          h(NButton, { size: 'small', tertiary: true, type: 'primary', onClick: () => goEdit(row.id) }, { default: () => '编辑' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row.id) },
            {
              trigger: () => h(NButton, { size: 'small', tertiary: true, type: 'error' }, { default: () => '删除' }),
              default: () => '确认删除该订单吗？'
            }
          ),
          h(
            NDropdown,
            {
              options: getMoreOptions(row),
              trigger: 'click',
              onSelect: (key: string | number) => handleMoreAction(key, row)
            },
            {
              default: () => h(NButton, { size: 'small', tertiary: true, loading: statusUpdatingId.value === row.id }, { default: () => '更多' })
            }
          )
        ]
      })
  }
]

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

.search-form :deep(.n-input .n-input-wrapper),
.search-form :deep(.n-base-selection),
.search-form :deep(.n-input-number) {
  align-items: center;
}

.search-form :deep(.n-input .n-input__input-el),
.search-form :deep(.n-base-selection .n-base-selection-label),
.search-form :deep(.n-base-selection .n-base-selection-placeholder) {
  height: 34px;
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
