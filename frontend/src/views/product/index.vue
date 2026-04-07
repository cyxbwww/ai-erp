<template>
  <div class="product-page">
    <n-card title="商品管理" :bordered="false">
      <div class="search-area">
        <n-form class="search-form" :model="searchForm" label-placement="left" label-width="90">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="10" label="关键词">
              <n-input
                v-model:value="searchForm.keyword"
                placeholder="商品名称/商品编码"
                clearable
                @keyup.enter="handleSearch"
              />
            </n-form-item-gi>
            <n-form-item-gi :span="5" label="商品分类">
              <n-select v-model:value="searchForm.category" :options="categoryOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="5" label="商品状态">
              <n-select v-model:value="searchForm.status" :options="statusOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4">
              <n-space justify="end" style="width: 100%">
                <n-button type="primary" @click="handleSearch">搜索</n-button>
                <n-button @click="handleReset">重置</n-button>
              </n-space>
            </n-form-item-gi>
          </n-grid>
        </n-form>
      </div>

      <div class="action-area">
        <n-button type="primary" @click="openCreate">新增商品</n-button>
      </div>

      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="tableLoading"
        :row-key="(row: ProductItem) => row.id"
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

    <n-modal v-model:show="modalVisible" preset="card" :title="modalTitle" style="width: 760px">
      <n-form ref="formRef" :model="formModel" :rules="rules" label-placement="left" label-width="100">
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
          <n-form-item-gi label="销售单价" path="sale_price">
            <n-input-number v-model:value="formModel.sale_price" :min="0" :precision="2" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="单位" path="unit">
            <n-select v-model:value="formModel.unit" :options="unitOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="库存数量" path="stock_qty">
            <n-input-number v-model:value="formModel.stock_qty" :min="0" :precision="0" style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi label="状态" path="status">
            <n-select v-model:value="formModel.status" :options="statusOptions" />
          </n-form-item-gi>
          <n-form-item-gi :span="2" label="备注" path="remark">
            <n-input v-model:value="formModel.remark" type="textarea" :rows="3" placeholder="请输入备注" />
          </n-form-item-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="modalVisible = false">取消</n-button>
          <n-button type="primary" :loading="submitLoading" @click="handleSubmit">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="detailVisible" preset="card" title="商品详情" style="width: 680px">
      <n-spin :show="detailLoading">
        <n-descriptions v-if="detailData" label-placement="left" bordered :column="2">
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
        <n-empty v-else description="暂无商品详情" />
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
// 商品管理页面：提供商品列表搜索、分页、详情、新增、编辑、删除全流程功能。
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NButton,
  NCard,
  NDataTable,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
  type DataTableColumns,
  type FormInst,
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

// 搜索表单状态
const searchForm = reactive({
  keyword: '',
  category: null as string | null,
  status: null as string | null
})

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 表格数据
const tableData = ref<ProductItem[]>([])

const categoryOptions = PRODUCT_CATEGORY_OPTIONS
const statusOptions = PRODUCT_STATUS_OPTIONS
const unitOptions = PRODUCT_UNIT_OPTIONS

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

// 商品表单校验规则
const rules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入商品编码', trigger: 'blur' }],
  category: [{ required: true, message: '请选择商品分类', trigger: 'change' }],
  sale_price: [{ required: true, type: 'number', message: '请输入销售单价', trigger: ['blur', 'change'] }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }],
  stock_qty: [{ required: true, type: 'number', message: '请输入库存数量', trigger: ['blur', 'change'] }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const modalTitle = computed(() => (editingId.value ? '编辑商品' : '新增商品'))

const columns: DataTableColumns<ProductItem> = [
  { title: '商品编号', key: 'id', width: 90 },
  { title: '商品名称', key: 'name', minWidth: 140 },
  { title: '商品编码', key: 'code', minWidth: 140 },
  {
    title: '商品分类',
    key: 'category',
    width: 120,
    render: (row) =>
      h(
        NTag,
        { type: getProductCategoryTagType(row.category), size: 'small' },
        { default: () => getProductCategoryLabel(row.category) }
      )
  },
  { title: '规格型号', key: 'spec_model', minWidth: 130 },
  {
    title: '销售单价',
    key: 'sale_price',
    width: 120,
    render: (row) => `¥${formatPrice(row.sale_price)}`
  },
  { title: '单位', key: 'unit', width: 90, render: (row) => getProductUnitLabel(row.unit) },
  { title: '库存数量', key: 'stock_qty', width: 100 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) =>
      h(
        NTag,
        { type: getProductStatusTagType(row.status), size: 'small' },
        { default: () => getProductStatusLabel(row.status) }
      )
  },
  { title: '创建时间', key: 'created_at', minWidth: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    fixed: 'right',
    render: (row) =>
      h(NSpace, {}, {
        default: () => [
          h(
            NButton,
            { size: 'small', tertiary: true, onClick: () => openDetail(row.id) },
            { default: () => '详情' }
          ),
          h(
            NButton,
            { size: 'small', tertiary: true, type: 'primary', onClick: () => openEdit(row) },
            { default: () => '编辑' }
          ),
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
              default: () => '确认删除该商品吗？'
            }
          )
        ]
      })
  }
]

// 格式化金额显示，统一保留两位小数。
const formatPrice = (price: number | null | undefined) => Number(price || 0).toFixed(2)

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

// 获取商品列表数据（含分页与筛选参数）。
const fetchList = async () => {
  tableLoading.value = true
  try {
    const res = await productListApi({
      keyword: searchForm.keyword.trim(),
      category: searchForm.category || '',
      status: searchForm.status || '',
      page: pagination.page,
      page_size: pagination.pageSize
    })

    if (res.data.code !== 0) {
      message.error(res.data.message || '商品列表加载失败')
      return
    }

    tableData.value = res.data?.data?.list || []
    pagination.total = res.data?.data?.total || 0
  } catch (_error) {
    message.error('商品列表请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 执行搜索并重置到第一页。
const handleSearch = async () => {
  pagination.page = 1
  await fetchList()
}

// 重置搜索条件并刷新列表。
const handleReset = async () => {
  searchForm.keyword = ''
  searchForm.category = null
  searchForm.status = null
  pagination.page = 1
  await fetchList()
}

// 切换分页大小后重新加载数据。
const handlePageSizeChange = async (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  await fetchList()
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

// 提交新增/编辑请求。
const handleSubmit = async () => {
  await formRef.value?.validate()
  submitLoading.value = true

  try {
    const payload: ProductFormPayload = {
      name: formModel.name,
      code: formModel.code,
      category: formModel.category,
      spec_model: formModel.spec_model,
      sale_price: Number(formModel.sale_price || 0),
      unit: formModel.unit,
      stock_qty: Number(formModel.stock_qty || 0),
      status: formModel.status,
      remark: formModel.remark
    }

    const res = editingId.value
      ? await productUpdateApi({ ...payload, id: editingId.value })
      : await productCreateApi(payload)

    if (res.data.code !== 0) {
      message.error(res.data.message || '保存失败')
      return
    }

    message.success(editingId.value ? '更新成功' : '创建成功')
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
</style>

