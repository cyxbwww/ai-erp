// 商品接口文件：封装商品管理模块的列表、详情、新增、编辑、删除请求。
import http from './http'

// 商品列表项类型
export interface ProductItem {
  id: number
  name: string
  code: string
  category: string
  spec_model: string
  sale_price: number
  unit: string
  stock_qty: number
  status: string
  remark: string
  created_at: string
  updated_at: string
}

// 商品列表查询参数
export interface ProductListParams {
  keyword?: string
  category?: string
  status?: string
  page?: number
  page_size?: number
}

// 商品新增/编辑表单参数
export interface ProductFormPayload {
  id?: number
  name: string
  code: string
  category: string
  spec_model: string
  sale_price: number
  unit: string
  stock_qty: number
  status: string
  remark: string
}

// 获取商品列表（搜索 + 分页）
export const productListApi = (params: ProductListParams) => {
  return http.get('/api/product/list', { params })
}

// 获取商品详情
export const productDetailApi = (id: number) => {
  return http.get(`/api/product/detail/${id}`)
}

// 新增商品
export const productCreateApi = (payload: ProductFormPayload) => {
  return http.post('/api/product/create', payload)
}

// 编辑商品
export const productUpdateApi = (payload: ProductFormPayload) => {
  return http.put('/api/product/update', payload)
}

// 删除商品
export const productDeleteApi = (id: number) => {
  return http.delete(`/api/product/delete/${id}`)
}

