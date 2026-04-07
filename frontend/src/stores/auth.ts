// 认证状态仓库：管理登录令牌、用户信息与权限集合。
import { defineStore } from 'pinia'

// 认证状态结构
interface AuthState {
  token: string
  username: string
  role: string
  permissions: string[]
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || '',
    permissions: JSON.parse(localStorage.getItem('permissions') || '[]')
  }),
  getters: {
    // 是否已登录
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    // 写入登录信息并持久化到本地存储
    setAuth(token: string, username: string, role: string, permissions: string[]) {
      this.token = token
      this.username = username
      this.role = role
      this.permissions = permissions

      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
      localStorage.setItem('role', role)
      localStorage.setItem('permissions', JSON.stringify(permissions))
    },
    // 清理登录信息
    logout() {
      this.token = ''
      this.username = ''
      this.role = ''
      this.permissions = []
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('permissions')
    },
    // 判断用户是否具备指定权限
    hasPermission(permission: string): boolean {
      return this.role === 'admin' || this.permissions.includes(permission)
    }
  }
})
