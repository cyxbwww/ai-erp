<template>
  <div class="order-form-page">
    <n-card :title="pageTitle" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button @click="goList">{{ backButtonText }}</n-button>
        </n-space>
      </template>

      <n-spin :show="pageLoading">
        <n-form ref="formRef" :model="formModel" :rules="rules" label-placement="left" label-width="100">
          <n-grid :cols="2" :x-gap="12">
            <n-form-item-gi label="客户" path="customer_id">
              <n-select
                v-model:value="formModel.customer_id"
                :options="customerOptions"
                placeholder="请选择客户"
                filterable
              />
            </n-form-item-gi>
            <n-form-item-gi label="订单状态" path="status">
              <n-select v-model:value="formModel.status" :options="statusOptions" placeholder="请选择订单状态" />
            </n-form-item-gi>
            <n-form-item-gi :span="2" label="备注" path="remark">
              <n-input v-model:value="formModel.remark" type="textarea" :rows="3" placeholder="请输入备注" />
            </n-form-item-gi>
          </n-grid>
        </n-form>

        <div class="items-head">
          <div class="items-title">订单明细</div>
          <n-button type="primary" tertiary @click="addItem">新增商品</n-button>
        </div>

        <n-empty v-if="!formModel.items.length" description="暂无商品明细，请先新增商品" />
        <n-table v-else bordered single-line :scroll-x="1080">
          <thead>
            <tr>
              <th style="width: 320px">商品</th>
              <th style="width: 100px">库存</th>
              <th style="width: 120px">单价</th>
              <th style="width: 140px">数量</th>
              <th style="width: 160px">小计</th>
              <th style="width: 120px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in formModel.items" :key="index">
              <td>
                <n-select
                  v-model:value="item.product_id"
                  :options="productOptions"
                  placeholder="请选择商品"
                  filterable
                  @update:value="(_v) => handleProductChange(index)"
                />
              </td>
              <td>
                <span>{{ getRowStock(item.product_id) }}</span>
              </td>
              <td>
                <n-input-number
                  v-model:value="item.unit_price"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  @update:value="(_v) => handleItemChange(index)"
                />
              </td>
              <td>
                <div class="qty-cell">
                  <n-input-number
                    v-model:value="item.quantity"
                    :min="1"
                    :precision="0"
                    style="width: 100%"
                    @update:value="(_v) => handleItemChange(index)"
                  />
                  <div v-if="isStockInsufficient(item)" class="stock-warning">库存不足，最多可下单 {{ getRowStock(item.product_id) }}</div>
                </div>
              </td>
              <td>¥{{ Number(item.subtotal || 0).toFixed(2) }}</td>
              <td>
                <n-button type="error" tertiary @click="removeItem(index)">删除</n-button>
              </td>
            </tr>
          </tbody>
        </n-table>

        <div class="total-area">
          <span class="total-label">订单总金额：</span>
          <span class="total-value">¥{{ totalAmount.toFixed(2) }}</span>
        </div>

        <div class="footer-actions">
          <n-space justify="end">
            <n-button @click="goList">取消</n-button>
            <n-button type="primary" :loading="submitLoading" @click="handleSubmit">保存订单</n-button>
          </n-space>
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 订单新建/编辑页：支持客户选择、商品选择、库存校验与金额自动计算。
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NEmpty,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NSelect,
  NSpace,
  NSpin,
  NTable,
  useMessage,
  type FormInst,
  type FormRules
} from 'naive-ui'
import { customerListApi } from '@/api/customer'
import { orderCreateApi, orderDetailApi, orderUpdateApi, type OrderFormPayload } from '@/api/order'
import { productListApi, type ProductItem } from '@/api/product'
import { ORDER_STATUS_OPTIONS } from '@/constants/enums'

type CustomerOption = {
  label: string
  value: number
}

type ProductOption = {
  label: string
  value: number
  price: number
  unit: string
  stock_qty: number
}

type OrderFormItem = {
  product_id: number | null
  unit_price: number
  quantity: number
  subtotal: number
}

const route = useRoute()
const router = useRouter()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
// 页面与提交加载状态
const pageLoading = ref(false)
const submitLoading = ref(false)

const customerOptions = ref<CustomerOption[]>([])
const productOptions = ref<ProductOption[]>([])

const statusOptions = ORDER_STATUS_OPTIONS
const editingOrderId = computed(() => Number(route.params.id) || 0)
const isEditMode = computed(() => editingOrderId.value > 0)
const pageTitle = computed(() => (isEditMode.value ? '编辑订单' : '新建订单'))
// 判断是否从详情页进入编辑页，用于返回路径控制。
const fromDetail = computed(() => String(route.query.from || '') === 'detail')
const backButtonText = computed(() => (isEditMode.value && fromDetail.value ? '返回详情' : '返回列表'))

// 订单表单主状态
const formModel = reactive({
  customer_id: null as number | null,
  status: 'draft',
  remark: '',
  items: [] as OrderFormItem[]
})

const rules: FormRules = {
  customer_id: [{ required: true, type: 'number', message: '请选择客户', trigger: 'change' }],
  status: [{ required: true, message: '请选择订单状态', trigger: 'change' }]
}

// 计算订单总金额。
const totalAmount = computed(() => formModel.items.reduce((sum, item) => sum + Number(item.subtotal || 0), 0))

// 返回列表或详情页。
const goList = () => {
  if (isEditMode.value && fromDetail.value) {
    router.push(`/order/detail/${editingOrderId.value}`)
    return
  }
  router.push('/order')
}

// 新增一行空明细。
const addItem = () => {
  formModel.items.push({
    product_id: null,
    unit_price: 0,
    quantity: 1,
    subtotal: 0
  })
}

// 删除一行明细。
const removeItem = (index: number) => {
  formModel.items.splice(index, 1)
}

// 读取当前行商品库存。
const getRowStock = (productId: number | null): number => {
  const product = productOptions.value.find((item) => item.value === productId)
  return Number(product?.stock_qty || 0)
}

// 判断当前行是否库存不足。
const isStockInsufficient = (item: OrderFormItem): boolean => {
  if (!item.product_id) return false
  return Number(item.quantity || 0) > getRowStock(item.product_id)
}

// 商品切换后自动带出单价，并重算小计。
const handleProductChange = (index: number) => {
  const item = formModel.items[index]
  const selected = productOptions.value.find((option) => option.value === item.product_id)
  if (selected) {
    item.unit_price = Number(selected.price || 0)
  }
  handleItemChange(index)
}

// 单价或数量变更后重算当前行小计。
const handleItemChange = (index: number) => {
  const item = formModel.items[index]
  item.unit_price = Number(item.unit_price || 0)
  item.quantity = Math.max(1, Number(item.quantity || 1))
  item.subtotal = Number((item.unit_price * item.quantity).toFixed(2))
}

// 拉取全部客户选项。
const fetchAllCustomers = async (): Promise<Array<{ id: number; name: string }>> => {
  const merged: Array<{ id: number; name: string }> = []
  let page = 1
  const pageSize = 100

  while (true) {
    const res = await customerListApi({ page, page_size: pageSize })
    if (res.data.code !== 0) {
      throw new Error(res.data.message || '客户选项加载失败')
    }
    const list = (res.data?.data?.list || []) as Array<{ id: number; name: string }>
    merged.push(...list)
    if (list.length < pageSize) break
    page += 1
  }
  return merged
}

// 拉取全部上架商品选项，并保留库存信息用于下单校验。
const fetchAllEnabledProducts = async (): Promise<ProductItem[]> => {
  const merged: ProductItem[] = []
  let page = 1
  const pageSize = 100

  while (true) {
    const res = await productListApi({ page, page_size: pageSize, status: 'enabled' })
    if (res.data.code !== 0) {
      throw new Error(res.data.message || '商品选项加载失败')
    }
    const list = (res.data?.data?.list || []) as ProductItem[]
    merged.push(...list)
    if (list.length < pageSize) break
    page += 1
  }
  return merged
}

// 编辑模式下回填订单数据。
const fetchOrderDetail = async () => {
  if (!isEditMode.value) return
  const res = await orderDetailApi(editingOrderId.value)
  if (res.data.code !== 0) {
    throw new Error(res.data.message || '订单详情加载失败')
  }
  const detail = res.data.data
  formModel.customer_id = detail.customer_id
  formModel.status = detail.status
  formModel.remark = detail.remark || ''
  formModel.items = (detail.items || []).map(
    (item: { product_id: number; unit_price: number; quantity: number; subtotal: number }) => ({
      product_id: item.product_id,
      unit_price: Number(item.unit_price || 0),
      quantity: Number(item.quantity || 1),
      subtotal: Number(item.subtotal || 0)
    })
  )
}

// 校验明细数据，确保商品、数量与库存均合法。
const validateItems = (): boolean => {
  if (!formModel.items.length) {
    message.error('请至少添加一条商品明细')
    return false
  }
  for (const item of formModel.items) {
    if (!item.product_id) {
      message.error('请选择商品明细中的商品')
      return false
    }
    if (!item.quantity || item.quantity <= 0) {
      message.error('商品数量必须大于 0')
      return false
    }
    if (item.unit_price < 0) {
      message.error('商品单价不能小于 0')
      return false
    }
    const stockQty = getRowStock(item.product_id)
    if (item.quantity > stockQty) {
      message.error(`商品库存不足：最多可下单 ${stockQty}`)
      return false
    }
  }
  return true
}

// 提交订单（新增/编辑）。
const handleSubmit = async () => {
  await formRef.value?.validate()
  if (!validateItems()) return

  submitLoading.value = true
  try {
    const payload: OrderFormPayload = {
      customer_id: Number(formModel.customer_id),
      status: formModel.status,
      remark: formModel.remark,
      items: formModel.items.map((item) => ({
        product_id: Number(item.product_id),
        unit_price: Number(item.unit_price || 0),
        quantity: Number(item.quantity || 1)
      }))
    }

    const res = isEditMode.value
      ? await orderUpdateApi({ ...payload, id: editingOrderId.value })
      : await orderCreateApi(payload)

    if (res.data.code !== 0) {
      message.error(res.data.message || '订单保存失败')
      return
    }
    message.success(isEditMode.value ? '订单更新成功' : '订单创建成功')
    if (isEditMode.value && fromDetail.value) {
      router.push(`/order/detail/${editingOrderId.value}`)
      return
    }
    router.push('/order')
  } catch (_error) {
    message.error('订单保存请求失败')
  } finally {
    submitLoading.value = false
  }
}

onMounted(async () => {
  pageLoading.value = true
  try {
    const [customerList, productList] = await Promise.all([fetchAllCustomers(), fetchAllEnabledProducts()])
    customerOptions.value = customerList.map((item) => ({
      label: item.name,
      value: item.id
    }))
    productOptions.value = productList.map((item) => ({
      label: `${item.name}（${item.code}）`,
      value: item.id,
      price: Number(item.sale_price || 0),
      unit: item.unit,
      stock_qty: Number(item.stock_qty || 0)
    }))

    await fetchOrderDetail()
    if (!isEditMode.value && !formModel.items.length) {
      addItem()
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : '页面初始化失败')
  } finally {
    pageLoading.value = false
  }
})
</script>

<style scoped>
.order-form-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.items-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  margin-bottom: 10px;
}

.items-title {
  font-weight: 600;
  color: #333;
}

.qty-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-warning {
  color: #d03050;
  font-size: 12px;
  line-height: 1.3;
}

.total-area {
  margin-top: 14px;
  text-align: right;
}

.total-label {
  color: #666;
  margin-right: 8px;
}

.total-value {
  color: #d03050;
  font-weight: 600;
  font-size: 18px;
}

.footer-actions {
  margin-top: 16px;
}
</style>

