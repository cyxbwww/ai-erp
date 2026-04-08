// 统一 HTTP 请求实例：负责注入 token、自动续期和失败重试。
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { createDiscreteApi } from 'naive-ui'
import router from '@/router'

// 扩展请求配置：用于标记请求是否已经重试，避免死循环。
interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

const http = axios.create({
  // 优先走前端同源代理，避免本地开发跨域问题。
  baseURL,
  timeout: 10000
})

// 刷新令牌请求使用独立实例，避免被当前拦截器再次拦截导致循环。
const refreshClient = axios.create({
  baseURL,
  timeout: 10000
})

const { message } = createDiscreteApi(['message'])

let refreshPromise: Promise<string> | null = null
let hasShownExpiredMessage = false

// 判断当前错误是否属于 access token 过期场景。
const isAccessTokenExpiredError = (error: AxiosError<{ code?: number; message?: string }>) => {
  const status = error.response?.status
  const code = error.response?.data?.code
  const messageText = error.response?.data?.message || ''
  return (status === 401 || code === 401) && messageText.includes('token 无效或已过期')
}

// 判断当前请求是否为认证相关接口，认证接口失败时不应继续触发刷新。
const isAuthEndpoint = (url?: string) => {
  if (!url) {
    return false
  }
  return url.includes('/api/auth/login') || url.includes('/api/auth/refresh')
}

// 清空本地登录态并强制跳转登录页。
const clearAuthAndRedirectToLogin = async () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('token_type')
  localStorage.removeItem('expires_in')
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  localStorage.removeItem('permissions')

  // 避免并发失败时重复提示。
  if (!hasShownExpiredMessage) {
    hasShownExpiredMessage = true
    message.error('登录已过期，请重新登录')
    window.setTimeout(() => {
      hasShownExpiredMessage = false
    }, 500)
  }

  if (router.currentRoute.value.path !== '/login') {
    await router.push('/login')
  }
}

// 通过 refresh token 换取新的 access token，并写回本地。
const refreshAccessToken = async (): Promise<string> => {
  const refreshToken = localStorage.getItem('refresh_token') || ''
  if (!refreshToken) {
    throw new Error('refresh token 缺失')
  }

  const response = await refreshClient.post('/api/auth/refresh', {
    refresh_token: refreshToken
  })

  if (response.data?.code !== 0) {
    throw new Error(response.data?.message || '刷新 access token 失败')
  }

  const data = response.data.data || {}
  const newAccessToken = data.access_token || ''
  const newRefreshToken = data.refresh_token || ''
  const tokenType = data.token_type || 'Bearer'
  const expiresIn = Number(data.expires_in || 0)

  if (!newAccessToken || !newRefreshToken) {
    throw new Error('刷新接口返回 token 不完整')
  }

  localStorage.setItem('access_token', newAccessToken)
  localStorage.setItem('refresh_token', newRefreshToken)
  localStorage.setItem('token_type', tokenType)
  localStorage.setItem('expires_in', String(expiresIn))
  // 保留历史 token 字段，兼容现有路由守卫与旧代码。
  localStorage.setItem('token', newAccessToken)

  return newAccessToken
}

// 请求拦截器：自动附加 access token。
http.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token') || localStorage.getItem('token')
  const tokenType = localStorage.getItem('token_type') || 'Bearer'
  if (accessToken) {
    config.headers.Authorization = `${tokenType} ${accessToken}`
  }
  return config
})

// 响应拦截器：处理 token 过期、自动刷新与原请求重试。
http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ code?: number; message?: string }>) => {
    const originalRequest = error.config as CustomAxiosRequestConfig | undefined
    if (!originalRequest) {
      return Promise.reject(error)
    }

    // 登录或刷新接口失败时直接透传，避免出现递归刷新。
    if (isAuthEndpoint(originalRequest.url)) {
      return Promise.reject(error)
    }

    // 非 token 过期错误，保持原有错误处理链路。
    if (!isAccessTokenExpiredError(error)) {
      return Promise.reject(error)
    }

    // 已重试过仍失败，认为 refresh 不可用，直接清理登录态。
    if (originalRequest._retry) {
      await clearAuthAndRedirectToLogin()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      // 并发控制：多个请求同时过期时，仅发起一次刷新。
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }

      const newAccessToken = await refreshPromise
      originalRequest.headers.Authorization = `${localStorage.getItem('token_type') || 'Bearer'} ${newAccessToken}`
      return http(originalRequest)
    } catch (refreshError) {
      // 刷新失败时，统一清理登录态并跳转登录页。
      await clearAuthAndRedirectToLogin()
      return Promise.reject(refreshError)
    }
  }
)

export default http
