// 认证接口文件：提供登录与刷新令牌 API 封装。
import http from './http'

// 登录请求参数。
interface LoginPayload {
  username: string
  password: string
}

// 刷新令牌请求参数。
interface RefreshTokenPayload {
  refresh_token: string
}

// 用户登录。
export const loginApi = (payload: LoginPayload) => {
  return http.post('/api/auth/login', payload)
}

// 刷新 access token。
export const refreshTokenApi = (payload: RefreshTokenPayload) => {
  return http.post('/api/auth/refresh', payload)
}
