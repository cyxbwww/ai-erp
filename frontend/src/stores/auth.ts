// 认证状态仓库：管理 access token、refresh token 与用户权限信息。
import { defineStore } from 'pinia'

// 认证状态结构
interface AuthState {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  username: string
  role: string
  permissions: string[]
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    // 保留 token 兼容读取，避免影响历史登录态数据。
    accessToken: localStorage.getItem('access_token') || localStorage.getItem('token') || '',
    refreshToken: localStorage.getItem('refresh_token') || '',
    tokenType: localStorage.getItem('token_type') || 'Bearer',
    expiresIn: Number(localStorage.getItem('expires_in') || '0'),
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || '',
    permissions: JSON.parse(localStorage.getItem('permissions') || '[]')
  }),
  getters: {
    // 是否已登录
    isLoggedIn: (state) => !!state.accessToken
  },
  actions: {
    // 写入 token 对并持久化。
    setTokenPair(accessToken: string, refreshToken: string, tokenType: string, expiresIn: number) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      this.tokenType = tokenType
      this.expiresIn = expiresIn

      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
      localStorage.setItem('token_type', tokenType)
      localStorage.setItem('expires_in', String(expiresIn))
      // 兼容历史代码读取 token 字段。
      localStorage.setItem('token', accessToken)
    },
    // 写入登录信息并持久化到本地存储。
    setAuth(
      accessToken: string,
      refreshToken: string,
      tokenType: string,
      expiresIn: number,
      username: string,
      role: string,
      permissions: string[]
    ) {
      this.setTokenPair(accessToken, refreshToken, tokenType, expiresIn)
      this.username = username
      this.role = role
      this.permissions = permissions

      localStorage.setItem('username', username)
      localStorage.setItem('role', role)
      localStorage.setItem('permissions', JSON.stringify(permissions))
    },
    // 清理登录信息。
    logout() {
      this.accessToken = ''
      this.refreshToken = ''
      this.tokenType = 'Bearer'
      this.expiresIn = 0
      this.username = ''
      this.role = ''
      this.permissions = []

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('token_type')
      localStorage.removeItem('expires_in')
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('permissions')
    },
    // 判断用户是否具备指定权限。
    hasPermission(permission: string): boolean {
      return this.role === 'admin' || this.permissions.includes(permission)
    }
  }
})
