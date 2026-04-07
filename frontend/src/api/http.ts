// 统一 HTTP 请求实例：负责注入 token 与基础配置。
import axios from 'axios'

const http = axios.create({
  // 优先走前端同源代理，避免本地开发跨域问题。
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000
})

// 请求拦截器：自动附加登录令牌。
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default http
