// 认证接口文件：提供登录相关 API 封装。
import http from './http'

// 登录请求参数
interface LoginPayload {
  username: string
  password: string
}

// 用户登录
export const loginApi = (payload: LoginPayload) => {
  return http.post('/api/auth/login', payload)
}
