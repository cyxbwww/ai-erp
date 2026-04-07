// 枚举常量文件：统一维护“存英文，显中文”的展示映射。
import type { SelectOption } from 'naive-ui'

// 通用枚举选项结构
export interface EnumOption extends SelectOption {
  label: string
  value: string
  tagType?: 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error'
}

// 将枚举数组转为 value => option 的快速映射
const toMap = (options: EnumOption[]) =>
  options.reduce<Record<string, EnumOption>>((acc, item) => {
    acc[item.value] = item
    return acc
  }, {})

// 客户等级枚举
export const CUSTOMER_LEVEL_OPTIONS: EnumOption[] = [
  { label: '普通客户', value: 'normal', tagType: 'default' },
  { label: '重点客户', value: 'vip', tagType: 'warning' },
  { label: '战略客户', value: 'strategic', tagType: 'error' }
]

// 客户状态枚举
export const CUSTOMER_STATUS_OPTIONS: EnumOption[] = [
  { label: '跟进中', value: 'active', tagType: 'info' },
  { label: '已成交', value: 'closed', tagType: 'success' },
  { label: '已流失', value: 'lost', tagType: 'default' }
]

// 客户来源枚举
export const CUSTOMER_SOURCE_OPTIONS: EnumOption[] = [
  { label: '手工录入', value: 'manual', tagType: 'default' },
  { label: '销售录入', value: 'sales', tagType: 'primary' },
  { label: '活动线索', value: 'campaign', tagType: 'warning' },
  { label: '外部导入', value: 'import', tagType: 'info' }
]

// 跟进类型枚举
export const FOLLOW_TYPE_OPTIONS: EnumOption[] = [
  { label: '电话', value: 'call', tagType: 'info' },
  { label: '微信', value: 'wechat', tagType: 'success' },
  { label: '拜访', value: 'visit', tagType: 'warning' },
  { label: '邮件', value: 'email', tagType: 'primary' },
  { label: '演示', value: 'demo', tagType: 'error' },
  { label: '其他', value: 'other', tagType: 'default' }
]

const CUSTOMER_LEVEL_MAP = toMap(CUSTOMER_LEVEL_OPTIONS)
const CUSTOMER_STATUS_MAP = toMap(CUSTOMER_STATUS_OPTIONS)
const CUSTOMER_SOURCE_MAP = toMap(CUSTOMER_SOURCE_OPTIONS)
const FOLLOW_TYPE_MAP = toMap(FOLLOW_TYPE_OPTIONS)

// 商品分类枚举
export const PRODUCT_CATEGORY_OPTIONS: EnumOption[] = [
  { label: '软件产品', value: 'software', tagType: 'primary' },
  { label: '服务产品', value: 'service', tagType: 'warning' },
  { label: '硬件产品', value: 'hardware', tagType: 'info' },
  { label: '其他', value: 'other', tagType: 'default' }
]

// 商品状态枚举
export const PRODUCT_STATUS_OPTIONS: EnumOption[] = [
  { label: '上架', value: 'enabled', tagType: 'success' },
  { label: '下架', value: 'disabled', tagType: 'default' }
]

// 商品单位枚举
export const PRODUCT_UNIT_OPTIONS: EnumOption[] = [
  { label: '套', value: 'set', tagType: 'default' },
  { label: '个', value: 'item', tagType: 'default' },
  { label: '年', value: 'year', tagType: 'default' },
  { label: '月', value: 'month', tagType: 'default' },
  { label: '许可', value: 'license', tagType: 'default' }
]

const PRODUCT_CATEGORY_MAP = toMap(PRODUCT_CATEGORY_OPTIONS)
const PRODUCT_STATUS_MAP = toMap(PRODUCT_STATUS_OPTIONS)
const PRODUCT_UNIT_MAP = toMap(PRODUCT_UNIT_OPTIONS)

// 订单状态枚举
export const ORDER_STATUS_OPTIONS: EnumOption[] = [
  { label: '草稿', value: 'draft', tagType: 'default' },
  { label: '已确认', value: 'confirmed', tagType: 'info' },
  { label: '已完成', value: 'completed', tagType: 'success' },
  { label: '已取消', value: 'cancelled', tagType: 'warning' }
]

const ORDER_STATUS_MAP = toMap(ORDER_STATUS_OPTIONS)

// 客户等级中文名称
export const getCustomerLevelLabel = (value: string) => CUSTOMER_LEVEL_MAP[value]?.label || value || '-'
// 客户状态中文名称
export const getCustomerStatusLabel = (value: string) => CUSTOMER_STATUS_MAP[value]?.label || value || '-'
// 客户来源中文名称
export const getCustomerSourceLabel = (value: string) => CUSTOMER_SOURCE_MAP[value]?.label || value || '-'

// 客户等级标签类型
export const getCustomerLevelTagType = (value: string) => CUSTOMER_LEVEL_MAP[value]?.tagType || 'default'
// 客户状态标签类型
export const getCustomerStatusTagType = (value: string) => CUSTOMER_STATUS_MAP[value]?.tagType || 'default'
// 客户来源标签类型
export const getCustomerSourceTagType = (value: string) => CUSTOMER_SOURCE_MAP[value]?.tagType || 'default'

// 跟进类型中文名称
export const getFollowTypeLabel = (value: string) => FOLLOW_TYPE_MAP[value]?.label || value || '-'
// 跟进类型标签类型
export const getFollowTypeTagType = (value: string) => FOLLOW_TYPE_MAP[value]?.tagType || 'default'

// 商品分类中文名称
export const getProductCategoryLabel = (value: string) => PRODUCT_CATEGORY_MAP[value]?.label || value || '-'
// 商品状态中文名称
export const getProductStatusLabel = (value: string) => PRODUCT_STATUS_MAP[value]?.label || value || '-'
// 商品单位中文名称
export const getProductUnitLabel = (value: string) => PRODUCT_UNIT_MAP[value]?.label || value || '-'

// 商品分类标签类型
export const getProductCategoryTagType = (value: string) => PRODUCT_CATEGORY_MAP[value]?.tagType || 'default'
// 商品状态标签类型
export const getProductStatusTagType = (value: string) => PRODUCT_STATUS_MAP[value]?.tagType || 'default'

// 订单状态中文名称
export const getOrderStatusLabel = (value: string) => ORDER_STATUS_MAP[value]?.label || value || '-'
// 订单状态标签类型
export const getOrderStatusTagType = (value: string) => ORDER_STATUS_MAP[value]?.tagType || 'default'
