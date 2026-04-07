<template>
  <div class="sidebar">
    <div class="logo">系统菜单</div>
    <n-menu :value="activeKey" :options="menuOptions" @update:value="handleSelect" />
  </div>
</template>

<script setup lang="ts">
// 侧边栏组件：负责菜单展示、激活态计算与页面跳转。
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NMenu, type MenuOption } from 'naive-ui'

const router = useRouter()
const route = useRoute()

// 菜单项配置
const menuOptions: MenuOption[] = [
  { label: '销售看板', key: '/dashboard' },
  { label: '客户管理', key: '/customer' },
  { label: '商品管理', key: '/product' },
  { label: '订单管理', key: '/order' }
]

// 根据当前路由计算菜单激活项。
const activeKey = computed(() => {
  if (route.path.startsWith('/customer')) return '/customer'
  if (route.path.startsWith('/product')) return '/product'
  if (route.path.startsWith('/order')) return '/order'
  if (route.path.startsWith('/dashboard')) return '/dashboard'
  return route.path
})

// 菜单选择后执行路由跳转。
const handleSelect = (key: string) => {
  router.push(key)
}
</script>

<style scoped>
/* 侧边栏容器 */
.sidebar {
  height: 100%;
  padding: 12px;
}

/* 菜单标题 */
.logo {
  height: 36px;
  line-height: 36px;
  text-align: center;
  font-weight: 600;
  margin-bottom: 12px;
}
</style>
