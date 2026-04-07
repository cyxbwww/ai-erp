<template>
  <div class="customer-page">
    <n-card title="客户管理" :bordered="false">
      <div class="search-area">
        <n-form class="search-form" :model="searchForm" label-placement="left" label-width="110">
          <n-grid :cols="24" :x-gap="12" :y-gap="10">
            <n-form-item-gi :span="8" label="关键词">
              <n-input
                v-model:value="searchForm.keyword"
                placeholder="客户名称/联系人/手机号/邮箱/公司"
                clearable
                @keyup.enter="handleSearch"
              />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="客户等级">
              <n-select v-model:value="searchForm.level" :options="levelOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="跟进状态">
              <n-select v-model:value="searchForm.status" :options="statusOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="客户来源">
              <n-select v-model:value="searchForm.source" :options="sourceOptions" clearable />
            </n-form-item-gi>
            <n-form-item-gi :span="4" label="负责人">
              <n-input v-model:value="searchForm.owner_name" placeholder="请输入负责人" clearable @keyup.enter="handleSearch" />
            </n-form-item-gi>
            <n-form-item-gi :span="8" label="创建时间">
              <n-date-picker v-model:value="searchForm.createdRange" type="daterange" clearable style="width: 100%" />
            </n-form-item-gi>
            <n-form-item-gi :span="8" label="最近跟进时间">
              <n-date-picker v-model:value="searchForm.followRange" type="daterange" clearable style="width: 100%" />
            </n-form-item-gi>
            <n-form-item-gi :span="8">
              <n-space justify="end" style="width: 100%">
                <n-button type="primary" @click="handleSearch">搜索</n-button>
                <n-button @click="handleReset">重置</n-button>
              </n-space>
            </n-form-item-gi>
          </n-grid>
        </n-form>
      </div>

      <div class="action-area">
        <n-button type="primary" @click="openCreate">新增客户</n-button>
      </div>

      <n-data-table
        :columns="columns"
        :data="tableData"
        :loading="tableLoading"
        :row-key="(row: CustomerItem) => row.id"
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
          <n-form-item-gi label="客户名称" path="name">
            <n-input v-model:value="formModel.name" placeholder="请输入客户名称" />
          </n-form-item-gi>
          <n-form-item-gi label="联系人" path="contact_name">
            <n-input v-model:value="formModel.contact_name" placeholder="请输入联系人" />
          </n-form-item-gi>
          <n-form-item-gi label="手机号" path="phone">
            <n-input v-model:value="formModel.phone" placeholder="请输入手机号" />
          </n-form-item-gi>
          <n-form-item-gi label="邮箱" path="email">
            <n-input v-model:value="formModel.email" placeholder="请输入邮箱" />
          </n-form-item-gi>
          <n-form-item-gi label="公司" path="company">
            <n-input v-model:value="formModel.company" placeholder="请输入公司名" />
          </n-form-item-gi>
          <n-form-item-gi label="负责人" path="owner_name">
            <n-input v-model:value="formModel.owner_name" placeholder="请输入负责人" />
          </n-form-item-gi>
          <n-form-item-gi label="客户等级" path="level">
            <n-select v-model:value="formModel.level" :options="levelOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="跟进状态" path="status">
            <n-select v-model:value="formModel.status" :options="statusOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="客户来源" path="source">
            <n-select v-model:value="formModel.source" :options="sourceOptions" />
          </n-form-item-gi>
          <n-form-item-gi label="最近跟进时间" path="last_follow_at">
            <n-date-picker v-model:value="lastFollowAtValue" type="datetime" clearable style="width: 100%" />
          </n-form-item-gi>
          <n-form-item-gi span="2" label="备注" path="remark">
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
  </div>
</template>

<script setup lang="ts">
// 客户管理列表页：提供客户搜索、分页、新增、编辑、删除等功能。
import { computed, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NModal,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NTag,
  useMessage,
  type DataTableColumns,
  type FormInst,
  type FormRules
} from 'naive-ui'
import {
  customerCreateApi,
  customerDeleteApi,
  customerListApi,
  customerUpdateApi,
  type CustomerFormPayload,
  type CustomerItem
} from '@/api/customer'
import {
  CUSTOMER_LEVEL_OPTIONS,
  CUSTOMER_SOURCE_OPTIONS,
  CUSTOMER_STATUS_OPTIONS,
  getCustomerLevelLabel,
  getCustomerLevelTagType,
  getCustomerSourceLabel,
  getCustomerSourceTagType,
  getCustomerStatusLabel,
  getCustomerStatusTagType
} from '@/constants/enums'

const message = useMessage()
const router = useRouter()
const formRef = ref<FormInst | null>(null)

// 列表与提交的加载状态
const tableLoading = ref(false)
const submitLoading = ref(false)
// 弹窗显示状态与编辑中的客户编号
const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const lastFollowAtValue = ref<number | null>(null)

// 搜索表单状态
const searchForm = reactive({
  keyword: '',
  level: null as string | null,
  status: null as string | null,
  source: null as string | null,
  owner_name: '',
  createdRange: null as [number, number] | null,
  followRange: null as [number, number] | null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const tableData = ref<CustomerItem[]>([])

const levelOptions = CUSTOMER_LEVEL_OPTIONS
const statusOptions = CUSTOMER_STATUS_OPTIONS
const sourceOptions = CUSTOMER_SOURCE_OPTIONS

const formModel = reactive<CustomerFormPayload>({
  name: '',
  contact_name: '',
  phone: '',
  email: '',
  company: '',
  level: 'normal',
  status: 'active',
  source: 'manual',
  owner_name: '',
  last_follow_at: '',
  remark: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'input'] }]
}

const modalTitle = computed(() => (editingId.value ? '编辑客户' : '新增客户'))

const columns: DataTableColumns<CustomerItem> = [
  { title: '客户编号', key: 'id', width: 90 },
  { title: '客户名称', key: 'name', minWidth: 120 },
  { title: '联系人', key: 'contact_name', minWidth: 100 },
  { title: '手机号', key: 'phone', minWidth: 120 },
  { title: '邮箱', key: 'email', minWidth: 180 },
  { title: '公司', key: 'company', minWidth: 140 },
  { title: '负责人', key: 'owner_name', minWidth: 100 },
  {
    title: '等级',
    key: 'level',
    width: 110,
    render: (row) =>
      h(
        NTag,
        { type: getCustomerLevelTagType(row.level), size: 'small' },
        { default: () => getCustomerLevelLabel(row.level) }
      )
  },
  {
    title: '跟进状态',
    key: 'status',
    width: 110,
    render: (row) =>
      h(
        NTag,
        { type: getCustomerStatusTagType(row.status), size: 'small' },
        { default: () => getCustomerStatusLabel(row.status) }
      )
  },
  {
    title: '来源',
    key: 'source',
    width: 110,
    render: (row) =>
      h(
        NTag,
        { type: getCustomerSourceTagType(row.source), size: 'small' },
        { default: () => getCustomerSourceLabel(row.source) }
      )
  },
  { title: '最近跟进时间', key: 'last_follow_at', minWidth: 160 },
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
            { size: 'small', tertiary: true, onClick: () => goDetail(row.id) },
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
              default: () => '确认删除该客户吗？'
            }
          )
        ]
      })
  }
]

const formatDate = (timestamp: number | null | undefined): string => {
  if (!timestamp) return ''
  const d = new Date(timestamp)
  const y = d.getFullYear()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${day}`
}

const resetForm = () => {
  editingId.value = null
  formModel.name = ''
  formModel.contact_name = ''
  formModel.phone = ''
  formModel.email = ''
  formModel.company = ''
  formModel.level = 'normal'
  formModel.status = 'active'
  formModel.source = 'manual'
  formModel.owner_name = ''
  formModel.last_follow_at = ''
  lastFollowAtValue.value = null
  formModel.remark = ''
}

// 获取客户列表数据（含分页与筛选参数）
const fetchList = async () => {
  tableLoading.value = true
  try {
    const created_start = formatDate(searchForm.createdRange?.[0])
    const created_end = formatDate(searchForm.createdRange?.[1])
    const follow_start = formatDate(searchForm.followRange?.[0])
    const follow_end = formatDate(searchForm.followRange?.[1])

    const res = await customerListApi({
      keyword: searchForm.keyword.trim(),
      level: searchForm.level || '',
      status: searchForm.status || '',
      source: searchForm.source || '',
      owner_name: searchForm.owner_name.trim(),
      created_start,
      created_end,
      follow_start,
      follow_end,
      page: pagination.page,
      page_size: pagination.pageSize
    })

    if (res.data.code !== 0) {
      message.error(res.data.message || '客户列表加载失败')
      return
    }
    tableData.value = res.data.data.list || []
    pagination.total = res.data.data.total || 0
  } catch (_error) {
    message.error('客户列表请求失败')
  } finally {
    tableLoading.value = false
  }
}

// 执行搜索并重置到第一页
const handleSearch = async () => {
  pagination.page = 1
  await fetchList()
}

// 重置搜索条件并刷新列表
const handleReset = async () => {
  searchForm.keyword = ''
  searchForm.level = null
  searchForm.status = null
  searchForm.source = null
  searchForm.owner_name = ''
  searchForm.createdRange = null
  searchForm.followRange = null
  pagination.page = 1
  await fetchList()
}

// 切换分页大小后重新加载数据
const handlePageSizeChange = async (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  await fetchList()
}

// 打开新增弹窗
const openCreate = () => {
  resetForm()
  modalVisible.value = true
}

// 打开编辑弹窗并回填客户数据
const openEdit = (row: CustomerItem) => {
  editingId.value = row.id
  formModel.name = row.name
  formModel.contact_name = row.contact_name
  formModel.phone = row.phone
  formModel.email = row.email
  formModel.company = row.company
  formModel.level = row.level
  formModel.status = row.status
  formModel.source = row.source
  formModel.owner_name = row.owner_name
  formModel.last_follow_at = row.last_follow_at || ''
  lastFollowAtValue.value = parseDateTimeToTimestamp(row.last_follow_at)
  formModel.remark = row.remark
  modalVisible.value = true
}

// 提交新增/编辑请求
const handleSubmit = async () => {
  await formRef.value?.validate()
  submitLoading.value = true

  try {
    const payload: CustomerFormPayload = {
      name: formModel.name,
      contact_name: formModel.contact_name,
      phone: formModel.phone,
      email: formModel.email,
      company: formModel.company,
      level: formModel.level,
      status: formModel.status,
      source: formModel.source,
      owner_name: formModel.owner_name,
      last_follow_at: formatTimestampToDateTime(lastFollowAtValue.value) || '',
      remark: formModel.remark
    }

    const res = editingId.value
      ? await customerUpdateApi({ ...payload, id: editingId.value })
      : await customerCreateApi(payload)

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

// 删除客户
const handleDelete = async (id: number) => {
  try {
    const res = await customerDeleteApi(id)
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

const goDetail = (id: number) => {
  router.push(`/customer/detail/${id}`)
}

// 解析 yyyy-MM-dd HH:mm:ss 为时间戳，无法解析时返回 null，避免日期组件报错。
const parseDateTimeToTimestamp = (value?: string | null): number | null => {
  if (!value) return null
  const normalized = value.replace(' ', 'T')
  const timestamp = new Date(normalized).getTime()
  return Number.isNaN(timestamp) ? null : timestamp
}

// 将时间戳转换为 yyyy-MM-dd HH:mm:ss，供后端接口使用。
const formatTimestampToDateTime = (value: number | null): string | null => {
  if (!value) return null
  const d = new Date(value)
  const y = d.getFullYear()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  const hh = `${d.getHours()}`.padStart(2, '0')
  const mm = `${d.getMinutes()}`.padStart(2, '0')
  const ss = `${d.getSeconds()}`.padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}:${ss}`
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.customer-page {
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
