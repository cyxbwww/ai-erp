<template>
  <div class="product-page">
    <n-card title="商品管理" :bordered="false">
      <div class="search-area">
        <n-form class="search-form" :model="searchForm" label-placement="left" label-width="92">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="8" label="关键词">
              <n-input
                v-model:value="searchForm.keyword"
                placeholder="商品名称/商品编码"
                clearable
                @keyup.enter="handleSearch"
              />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="商品分类">
              <n-select v-model:value="searchForm.category" :options="categoryOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="商品状态">
              <n-select v-model:value="searchForm.status" :options="statusOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="库存状态">
              <n-select v-model:value="searchForm.inventory_status" :options="inventoryStatusOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4">
              <n-space justify="end" style="width: 100%">
                <n-button type="primary" @click="handleSearch">搜索</n-button>
                <n-button @click="handleReset">重置</n-button>
              </n-space>
            </n-form-item-gi>

            <n-form-item-gi :span="8" label="创建时间">
              <n-date-picker v-model:value="searchForm.created_range" type="daterange" clearable style="width: 100%" />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="最低价格">
              <n-input-number v-model:value="searchForm.price_min" :min="0" :precision="2" style="width: 100%" />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="最高价格">
              <n-input-number v-model:value="searchForm.price_max" :min="0" :precision="2" style="width: 100%" />
            </n-form-item-gi>
            <n-form-item-gi :span="8">
              <n-space justify="end" style="width: 100%">
                <n-button @click="handleRefresh">刷新</n-button>
              </n-space>
            </n-form-item-gi>
          </n-grid>
        </n-form>
      </div>

      <div class="action-area">
        <n-space>
          <n-button type="primary" @click="openCreate">新增商品</n-button>
          <n-button :disabled="!checkedRowKeys.length" @click="handleBatchStatus('enabled')">批量上架</n-button>
          <n-button :disabled="!checkedRowKeys.length" @click="handleBatchStatus('disabled')">批量下架</n-button>
          <n-popconfirm @positive-click="handleBatchDelete">
            <template #trigger>
              <n-button :disabled="!checkedRowKeys.length" type="error" secondary>批量删除</n-button>
            </template>
            确认删除选中的 {{ checkedRowKeys.length }} 个商品吗？
          </n-popconfirm>
        </n-space>
      </div>

      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="tableLoading"
        :row-key="(row: ProductItem) => row.id"
        :checked-row-keys="checkedRowKeys"
        @update:checked-row-keys="handleCheckedRowKeys"
        :locale="{ emptyText: '暂无商品数据，请调整筛选条件后重试' }"
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

    <n-modal v-model:show="modalVisible" preset="card" :title="modalTitle" style="width: 800px">
      <n-form ref="formRef" :model="formModel" :rules="rules" label-placement="left" label-width="100">
        <n-divider title-placement="left">基础信息</n-divider>
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="商品名称" path="name">
            <n-input v-model:value="formModel.name" placeholder="请输入商品名称" />
          </n-form-item-gi>
          <n-form-item-gi label="商品编码" path="code">
            <n-input v-model:value="formModel.code" placeholder="请输入商品编码" />
          </n-form-item-gi>
          <n-form-item-gi label="商品分类" path="category">
            <n-select v-model:value="formModel.category" :options="categoryOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="规格型号" path="spec_model">
            <n-input v-model:value="formModel.spec_model" placeholder="请输入规格型号" />
          </n-form-item-gi>
        </n-grid>

        <n-divider title-placement="left">销售与库存</n-divider>
        <n-grid :cols="2" :x-gap="12">
          <n-form-item-gi label="销售单价" path="sale_price">
            <n-input-number v-model:value="formModel.sale_price" :min="0" :precision="2" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="单位" path="unit">
            <n-select v-model:value="formModel.unit" :options="unitOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="库存数量" path="stock_qty">
            <n-input-number v-model:value="formModel.stock_qty" :min="0" :precision="0" style="width: 100%" />
            <div class="field-tip">当前版本允许直接维护库存数量，后续建议由库存模块统一管理。</div>
          </n-form-item-gi>
          <n-form-item-gi label="状态" path="status">
            <n-select v-model:value="formModel.status" :options="statusOptions" />
          </n-form-item-gi>
        </n-grid>

        <n-divider title-placement="left">其他信息</n-divider>
        <n-form-item label="备注" path="remark">
          <n-input v-model:value="formModel.remark" type="textarea" :rows="3" placeholder="请输入备注（最多 500 字）" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="modalVisible = false">取消</n-button>
          <n-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ editingId ? '保存修改' : '创建商品' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="detailVisible" preset="card" title="商品详情" style="width: 760px">
      <n-spin :show="detailLoading">
        <template v-if="detailData">
          <n-grid :cols="24" :x-gap="12" :y-gap="12" class="detail-summary-grid">
            <n-gi :span="6">
              <n-card size="small" title="商品状态">
                <n-tag :type="getProductStatusTagType(detailData.status)">{{ getProductStatusLabel(detailData.status) }}</n-tag>
              </n-card>
            </n-gi>
            <n-gi :span="6">
              <n-card size="small" title="库存状态">
                <n-tag :type="getInventoryStatusTagType(detailData.stock_qty)">{{ getInventoryStatusLabel(detailData.stock_qty) }}</n-tag>
              </n-card>
            </n-gi>
            <n-gi :span="6">
              <n-card size="small" title="销售单价">
                <div class="summary-text">¥{{ formatPrice(detailData.sale_price) }}</div>
              </n-card>
            </n-gi>
            <n-gi :span="6">
              <n-card size="small" title="商品分类">
                <n-tag :type="getProductCategoryTagType(detailData.category)">{{ getProductCategoryLabel(detailData.category) }}</n-tag>
              </n-card>
            </n-gi>
          </n-grid>

          <n-alert :type="getInventoryAlertType(detailData.stock_qty)" :title="getInventoryAlertTitle(detailData.stock_qty)" class="inventory-alert" />

          <n-grid :cols="24" :x-gap="12" :y-gap="12" class="business-grid">
            <n-gi :span="8">
              <n-statistic label="关联订单数" :value="detailBusinessInfo.relatedOrderCount" />
            </n-gi>
            <n-gi :span="8">
              <n-statistic label="累计销量" :value="detailBusinessInfo.totalSales" />
            </n-gi>
            <n-gi :span="8">
              <n-card size="small" title="最近下单时间">
                <div class="summary-text">{{ detailBusinessInfo.lastOrderedAt }}</div>
              </n-card>
            </n-gi>
          </n-grid>

          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="商品编号">{{ detailData.id }}</n-descriptions-item>
            <n-descriptions-item label="商品名称">{{ detailData.name }}</n-descriptions-item>
            <n-descriptions-item label="商品编码">{{ detailData.code }}</n-descriptions-item>
            <n-descriptions-item label="商品分类">{{ getProductCategoryLabel(detailData.category) }}</n-descriptions-item>
            <n-descriptions-item label="规格型号">{{ detailData.spec_model || '-' }}</n-descriptions-item>
            <n-descriptions-item label="销售单价">¥{{ formatPrice(detailData.sale_price) }}</n-descriptions-item>
            <n-descriptions-item label="单位">{{ getProductUnitLabel(detailData.unit) }}</n-descriptions-item>
            <n-descriptions-item label="库存数量">{{ detailData.stock_qty }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="getProductStatusTagType(detailData.status)" size="small">
                {{ getProductStatusLabel(detailData.status) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">{{ detailData.created_at }}</n-descriptions-item>
            <n-descriptions-item label="更新时间">{{ detailData.updated_at }}</n-descriptions-item>
            <n-descriptions-item label="备注" :span="2">{{ detailData.remark || '-' }}</n-descriptions-item>
          </n-descriptions>
        </template>

        <n-empty v-else description="暂无商品详情" />
      </n-spin>
      <template #footer>
        <n-space justify="end">
          <n-button @click="detailVisible = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="stockAdjustVisible" preset="card" title="调整库存" style="width: 460px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="商品名称">
          <n-input :value="stockAdjustTarget?.name || '-'" readonly />
        </n-form-item>
        <n-form-item label="当前库存">
          <n-input :value="String(stockAdjustTarget?.stock_qty ?? '-')" readonly />
        </n-form-item>
        <n-form-item label="调整数量">
          <n-input-number v-model:value="stockDelta" :precision="0" style="width: 100%" placeholder="正数加库存，负数减库存" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="stockAdjustVisible = false">取消</n-button>
          <n-button type="primary" @click="handleConfirmAdjustStock">确认调整</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
// 商品管理页面：增强筛选、库存状态、上下架与库存调整操作，保留现有弹窗交互模式。
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NEmpty,
  NForm,
  NFormItem,
  NFormItemGi,
  NGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NStatistic,
  NTag,
  NTooltip,
  useMessage,
  type DataTableColumns,
  type FormInst,
  type FormItemRule,
  type FormRules
} from 'naive-ui'
import {
  productCreateApi,
  productDeleteApi,
  productDetailApi,
  productListApi,
  productUpdateApi,
  type ProductFormPayload,
  type ProductItem
} from '@/api/product'
import {
  PRODUCT_CATEGORY_OPTIONS,
  PRODUCT_STATUS_OPTIONS,
  PRODUCT_UNIT_OPTIONS,
  getProductCategoryLabel,
  getProductCategoryTagType,
  getProductStatusLabel,
  getProductStatusTagType,
  getProductUnitLabel
} from '@/constants/enums'

type InventoryStatus = 'out_of_stock' | 'low_stock' | 'normal'

const message = useMessage()
const formRef = ref<FormInst | null>(null)

// 列表与弹窗提交加载状态
const tableLoading = ref(false)
const submitLoading = ref(false)
// 详情弹窗加载状态
const detailLoading = ref(false)

// 新增/编辑弹窗显示状态与编辑中的商品编号
const modalVisible = ref(false)
const editingId = ref<number | null>(null)
// 详情弹窗显示状态与详情数据
const detailVisible = ref(false)
const detailData = ref<ProductItem | null>(null)

// 库存调整弹窗状态
const stockAdjustVisible = ref(false)
const stockAdjustTarget = ref<ProductItem | null>(null)
const stockDelta = ref<number | null>(0)

// 库存阈值：用于低库存判断
const LOW_STOCK_THRESHOLD = 20

// 搜索表单状态
const searchForm = reactive({
  keyword: '',
  category: null as string | null,
  status: null as string | null,
  inventory_status: null as InventoryStatus | null,
  created_range: null as [number, number] | null,
  price_min: null as number | null,
  price_max: null as number | null
})

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const checkedRowKeys = ref<number[]>([])

// 全量数据与当前页数据
const filteredData = ref<ProductItem[]>([])
const tableData = ref<ProductItem[]>([])

const categoryOptions = PRODUCT_CATEGORY_OPTIONS
const statusOptions = PRODUCT_STATUS_OPTIONS
const unitOptions = PRODUCT_UNIT_OPTIONS
const inventoryStatusOptions = [
  { label: '缺货', value: 'out_of_stock' },
  { label: '低库存', value: 'low_stock' },
  { label: '库存正常', value: 'normal' }
]

// 商品新增/编辑表单状态
const formModel = reactive<ProductFormPayload>({
  name: '',
  code: '',
  category: 'software',
  spec_model: '',
  sale_price: 0,
  unit: 'set',
  stock_qty: 0,
  status: 'enabled',
  remark: ''
})

// 销售单价校验
const validateSalePrice = (_rule: FormItemRule, value: number): true | Error => {
  if (value === null || value === undefined) return new Error('请输入销售单价')
  if (Number(value) < 0) return new Error('销售单价必须大于等于 0')
  return true
}

// 库存数量校验
const validateStockQty = (_rule: FormItemRule, value: number): true | Error => {
  if (value === null || value === undefined) return new Error('请输入库存数量')
  if (!Number.isInteger(Number(value))) return new Error('库存数量必须为整数')
  if (Number(value) < 0) return new Error('库存数量必须为非负整数')
  return true
}

// 商品表单校验规则
const rules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: ['blur', 'input'] }],
  code: [{ required: true, message: '请输入商品编码', trigger: ['blur', 'input'] }],
  category: [{ required: true, message: '请选择商品分类', trigger: 'change' }],
  sale_price: [{ required: true, validator: validateSalePrice, trigger: ['blur', 'change'] }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
  stock_qty: [{ required: true, validator: validateStockQty, trigger: ['blur', 'change'] }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  remark: [{ max: 500, message: '备注最多 500 字', trigger: ['blur', 'input'] }]
}

const modalTitle = computed(() => (editingId.value ? '编辑商品' : '新增商品'))

const detailBusinessInfo = computed(() => {
  const p = detailData.value
  if (!p) {
    return { relatedOrderCount: 0, totalSales: 0, lastOrderedAt: '-' }
  }
  // 演示数据：后续可替换为真实统计接口
  const relatedOrderCount = (p.id % 6) + 1
  const totalSales = relatedOrderCount * ((p.id % 5) + 3)
  const lastOrderedAt = p.updated_at || p.created_at || '-'
  return { relatedOrderCount, totalSales, lastOrderedAt }
})

const checkedRows = computed(() => {
  const set = new Set(checkedRowKeys.value)
  return filteredData.value.filter((item) => set.has(item.id))
})

// 计算库存状态
const getInventoryStatus = (stockQty: number): InventoryStatus => {
  const qty = Number(stockQty || 0)
  if (qty <= 0) return 'out_of_stock'
  if (qty < LOW_STOCK_THRESHOLD) return 'low_stock'
  return 'normal'
}

const getInventoryStatusLabel = (stockQty: number): string => {
  const status = getInventoryStatus(stockQty)
  if (status === 'out_of_stock') return '缺货'
  if (status === 'low_stock') return '低库存'
  return '库存正常'
}

const getInventoryStatusTagType = (stockQty: number) => {
  const status = getInventoryStatus(stockQty)
  if (status === 'out_of_stock') return 'error'
  if (status === 'low_stock') return 'warning'
  return 'success'
}

const getInventoryAlertType = (stockQty: number): 'error' | 'warning' | 'success' => {
  const status = getInventoryStatus(stockQty)
  if (status === 'out_of_stock') return 'error'
  if (status === 'low_stock') return 'warning'
  return 'success'
}

const getInventoryAlertTitle = (stockQty: number): string => {
  const status = getInventoryStatus(stockQty)
  if (status === 'out_of_stock') return '库存风险提示：当前商品已缺货，请及时补货或调整上架状态。'
  if (status === 'low_stock') return `库存风险提示：当前库存低于阈值（${LOW_STOCK_THRESHOLD}），建议尽快补货。`
  return '库存状态正常：当前库存可满足近期业务需求。'
}

// 渲染商品名称列，附带规格型号提示
const renderNameCell = (row: ProductItem) => {
  const text = row.name || '-'
  const tooltip = row.spec_model ? `${text}（规格：${row.spec_model}）` : text
  return h(
    NTooltip,
    { trigger: 'hover' },
    {
      trigger: () => h('div', { class: 'text-ellipsis' }, text),
      default: () => tooltip
    }
  )
}

const columns: DataTableColumns<ProductItem> = [
  { type: 'selection', width: 48 },
  { title: '商品编号', key: 'id', width: 90 },
  { title: '商品名称', key: 'name', minWidth: 150, render: (row) => renderNameCell(row) },
  { title: '商品编码', key: 'code', minWidth: 140 },
  {
    title: '商品分类',
    key: 'category',
    width: 120,
    render: (row) =>
      h(NTag, { type: getProductCategoryTagType(row.category), size: 'small' }, { default: () => getProductCategoryLabel(row.category) })
  },
  { title: '规格型号', key: 'spec_model', minWidth: 130, render: (row) => row.spec_model || '-' },
  {
    title: '销售单价',
    key: 'sale_price',
    width: 120,
    render: (row) => `¥${formatPrice(row.sale_price)}`
  },
  { title: '单位', key: 'unit', width: 90, render: (row) => getProductUnitLabel(row.unit) },
  {
    title: '库存数量',
    key: 'stock_qty',
    width: 150,
    render: (row) =>
      h(NSpace, { align: 'center', size: 6 }, {
        default: () => [
          h('span', null, `${row.stock_qty}`),
          h(NTag, { size: 'small', type: getInventoryStatusTagType(row.stock_qty) }, { default: () => getInventoryStatusLabel(row.stock_qty) })
        ]
      })
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => h(NTag, { type: getProductStatusTagType(row.status), size: 'small' }, { default: () => getProductStatusLabel(row.status) })
  },
  { title: '创建时间', key: 'created_at', minWidth: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 360,
    fixed: 'right',
    render: (row) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'small', tertiary: true, onClick: () => openDetail(row.id) }, { default: () => '详情' }),
          h(NButton, { size: 'small', tertiary: true, type: 'primary', onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(
            NButton,
            { size: 'small', tertiary: true, type: row.status === 'enabled' ? 'warning' : 'success', onClick: () => handleToggleStatus(row) },
            { default: () => (row.status === 'enabled' ? '下架' : '上架') }
          ),
          h(NButton, { size: 'small', tertiary: true, type: 'info', onClick: () => openAdjustStock(row) }, { default: () => '调整库存' }),
          h(
            NPopconfirm,
            { onPositiveClick: () => handleDelete(row.id) },
            {
              trigger: () => h(NButton, { size: 'small', tertiary: true, type: 'error' }, { default: () => '删除' }),
              default: () => '确认删除该商品吗？'
            }
          )
        ]
      })
  }
]

// 格式化金额显示，统一保留两位小数
const formatPrice = (price: number | null | undefined) => Number(price || 0).toFixed(2)

// 解析日期时间字符串为时间戳
const parseDateTimeToTimestamp = (value?: string): number => {
  if (!value) return 0
  const normalized = value.replace(/-/g, '/').replace('T', ' ')
  const time = new Date(normalized).getTime()
  return Number.isNaN(time) ? 0 : time
}

// 重置新增/编辑表单，避免状态串扰。
const resetForm = () => {
  editingId.value = null
  formModel.name = ''
  formModel.code = ''
  formModel.category = 'software'
  formModel.spec_model = ''
  formModel.sale_price = 0
  formModel.unit = 'set'
  formModel.stock_qty = 0
  formModel.status = 'enabled'
  formModel.remark = ''
}

// 对后端列表结果执行前端扩展筛选（库存状态、创建时间、价格区间）。
const applyExtraFilters = (list: ProductItem[]) => {
  const createdRange = searchForm.created_range
  const priceMin = searchForm.price_min
  const priceMax = searchForm.price_max

  return list.filter((item) => {
    if (searchForm.inventory_status && getInventoryStatus(item.stock_qty) !== searchForm.inventory_status) {
      return false
    }

    const price = Number(item.sale_price || 0)
    if (priceMin !== null && price < priceMin) return false
    if (priceMax !== null && price > priceMax) return false

    if (createdRange && createdRange.length === 2) {
      const createdAt = parseDateTimeToTimestamp(item.created_at)
      if (!createdAt) return false
      if (createdAt < createdRange[0] || createdAt > createdRange[1]) return false
    }

    return true
  })
}

// 根据当前分页切片展示数据
const applyPagination = () => {
  pagination.total = filteredData.value.length
  const start = (pagination.page - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  tableData.value = filteredData.value.slice(start, end)

  const validIds = new Set(filteredData.value.map((item) => item.id))
  checkedRowKeys.value = checkedRowKeys.value.filter((id) => validIds.has(id))
}

// 获取商品列表数据（含分页与筛选参数）
const fetchList = async () => {
  tableLoading.value = true
  try {
    const allRows: ProductItem[] = []
    let page = 1
    const pageSize = 100
    let finished = false

    while (!finished) {
      const res = await productListApi({
        keyword: searchForm.keyword.trim(),
        category: searchForm.category || '',
        status: searchForm.status || '',
        page,
        page_size: pageSize
      })

      if (res.data.code !== 0) {
        message.error(res.data.message || '商品列表加载失败')
        return
      }

      const list = (res.data?.data?.list || []) as ProductItem[]
      allRows.push(...list)

      if (list.length < pageSize || page >= 30) {
        finished = true
      } else {
        page += 1
      }
    }

    filteredData.value = applyExtraFilters(allRows)
    applyPagination()
  } catch (_error) {
    message.error('商品列表请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 校验商品编码唯一性：当前为前端请求演示，后端仍会做最终校验。
const checkCodeUnique = async (code: string, currentId?: number) => {
  const res = await productListApi({ keyword: code.trim(), page: 1, page_size: 100 })
  if (res.data.code !== 0) return true
  const list = (res.data?.data?.list || []) as ProductItem[]
  return !list.some((item) => item.code === code.trim() && item.id !== (currentId || 0))
}

// 执行搜索并重置到第一页。
const handleSearch = async () => {
  if (searchForm.price_min !== null && searchForm.price_max !== null && searchForm.price_min > searchForm.price_max) {
    message.warning('最低价格不能大于最高价格')
    return
  }
  pagination.page = 1
  await fetchList()
}

// 重置搜索条件并刷新列表。
const handleReset = async () => {
  searchForm.keyword = ''
  searchForm.category = null
  searchForm.status = null
  searchForm.inventory_status = null
  searchForm.created_range = null
  searchForm.price_min = null
  searchForm.price_max = null
  pagination.page = 1
  await fetchList()
}

const handleRefresh = async () => {
  await fetchList()
  message.success('列表已刷新')
}

// 切换分页大小后重新加载数据。
const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  applyPagination()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  applyPagination()
}

const handleCheckedRowKeys = (keys: (string | number)[]) => {
  checkedRowKeys.value = keys.map((item) => Number(item)).filter((id) => Number.isFinite(id))
}

// 打开新增弹窗。
const openCreate = () => {
  resetForm()
  modalVisible.value = true
}

// 打开编辑弹窗并回填商品数据。
const openEdit = (row: ProductItem) => {
  editingId.value = row.id
  formModel.name = row.name
  formModel.code = row.code
  formModel.category = row.category
  formModel.spec_model = row.spec_model
  formModel.sale_price = Number(row.sale_price || 0)
  formModel.unit = row.unit
  formModel.stock_qty = Number(row.stock_qty || 0)
  formModel.status = row.status
  formModel.remark = row.remark
  modalVisible.value = true
}

// 打开详情弹窗并按需加载详情数据。
const openDetail = async (id: number) => {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await productDetailApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || '商品详情加载失败')
      return
    }
    detailData.value = res.data.data
  } catch (_error) {
    message.error('商品详情请求失败')
  } finally {
    detailLoading.value = false
  }
}

// 打开库存调整弹窗
const openAdjustStock = (row: ProductItem) => {
  stockAdjustTarget.value = row
  stockDelta.value = 0
  stockAdjustVisible.value = true
}

// 统一执行商品更新
const updateProduct = async (row: ProductItem, patch: Partial<ProductFormPayload>) => {
  const payload: ProductFormPayload = {
    id: row.id,
    name: row.name,
    code: row.code,
    category: row.category,
    spec_model: row.spec_model,
    sale_price: Number(row.sale_price || 0),
    unit: row.unit,
    stock_qty: Number(row.stock_qty || 0),
    status: row.status,
    remark: row.remark,
    ...patch
  }
  return productUpdateApi(payload)
}

// 上下架切换
const handleToggleStatus = async (row: ProductItem) => {
  const nextStatus = row.status === 'enabled' ? 'disabled' : 'enabled'
  try {
    const res = await updateProduct(row, { status: nextStatus })
    if (res.data.code !== 0) {
      message.error(res.data.message || '状态更新失败')
      return
    }
    message.success(nextStatus === 'enabled' ? '商品已上架' : '商品已下架')
    await fetchList()
  } catch (_error) {
    message.error('状态更新请求失败')
  }
}

// 确认库存调整
const handleConfirmAdjustStock = async () => {
  const target = stockAdjustTarget.value
  if (!target) return
  const delta = Number(stockDelta.value || 0)
  if (!Number.isInteger(delta)) {
    message.warning('调整数量必须为整数')
    return
  }

  const nextStock = Number(target.stock_qty || 0) + delta
  if (nextStock < 0) {
    message.warning('调整后库存不能小于 0')
    return
  }

  try {
    const res = await updateProduct(target, { stock_qty: nextStock })
    if (res.data.code !== 0) {
      message.error(res.data.message || '库存调整失败')
      return
    }
    message.success(`库存调整成功，当前库存 ${nextStock}`)
    stockAdjustVisible.value = false
    await fetchList()
  } catch (_error) {
    message.error('库存调整请求失败')
  }
}

// 批量上架/下架
const handleBatchStatus = async (status: 'enabled' | 'disabled') => {
  if (!checkedRows.value.length) return

  let successCount = 0
  for (const row of checkedRows.value) {
    if (row.status === status) continue
    try {
      const res = await updateProduct(row, { status })
      if (res.data.code === 0) {
        successCount += 1
      }
    } catch (_error) {
      // 单条失败继续处理其它条目
    }
  }

  message.success(`${status === 'enabled' ? '批量上架' : '批量下架'}完成，成功 ${successCount} 条`)
  await fetchList()
}

// 批量删除
const handleBatchDelete = async () => {
  if (!checkedRowKeys.value.length) return

  let successCount = 0
  for (const id of checkedRowKeys.value) {
    try {
      const res = await productDeleteApi(id)
      if (res.data.code === 0) {
        successCount += 1
      }
    } catch (_error) {
      // 单条失败继续处理其它条目
    }
  }

  checkedRowKeys.value = []
  message.success(`批量删除完成，成功 ${successCount} 条`)
  await fetchList()
}

// 提交新增/编辑请求。
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch (_error) {
    return
  }

  const codeUnique = await checkCodeUnique(formModel.code, editingId.value || undefined)
  if (!codeUnique) {
    message.warning('商品编码已存在，请更换后重试')
    return
  }

  submitLoading.value = true
  try {
    const payload: ProductFormPayload = {
      name: formModel.name,
      code: formModel.code,
      category: formModel.category,
      spec_model: formModel.spec_model,
      sale_price: Number(formModel.sale_price || 0),
      unit: formModel.unit,
      // 当前版本允许在商品表单维护库存字段，后续应迁移至库存模块。
      stock_qty: Number(formModel.stock_qty || 0),
      status: formModel.status,
      remark: formModel.remark
    }

    const res = editingId.value ? await productUpdateApi({ ...payload, id: editingId.value }) : await productCreateApi(payload)

    if (res.data.code !== 0) {
      message.error(res.data.message || '保存失败')
      return
    }

    message.success(editingId.value ? '商品更新成功' : '商品创建成功')
    modalVisible.value = false
    await fetchList()
  } catch (_error) {
    message.error('保存请求失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除商品。
const handleDelete = async (id: number) => {
  try {
    const res = await productDeleteApi(id)
    if (res.data.code !== 0) {
      message.error(res.data.message || '删除失败')
      return
    }
    message.success('删除成功')
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }
    await fetchList()
  } catch (_error) {
    message.error('删除请求失败')
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
/* 商品页面整体布局：与系统后台页面保持一致的上下分区。 */
.product-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 搜索区域样式。 */
.search-area {
  margin-bottom: 12px;
}

/* 统一搜索表单标签与输入视觉，避免错位。 */
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

/* 操作按钮区域。 */
.action-area {
  margin-bottom: 12px;
}

/* 分页区域右对齐。 */
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.field-tip {
  margin-top: 6px;
  color: #999;
  font-size: 12px;
  line-height: 1.4;
}

.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-summary-grid {
  margin-bottom: 12px;
}

.detail-summary-grid :deep(.n-card) {
  height: 100%;
}

.detail-summary-grid :deep(.n-card__content) {
  min-height: 56px;
  display: flex;
  align-items: center;
}

.inventory-alert {
  margin-bottom: 12px;
}

.summary-text {
  line-height: 24px;
}

.business-grid {
  margin-bottom: 12px;
}
</style>
