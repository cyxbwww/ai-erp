<template>
  <div class="sidebar">
    <div class="logo">
      <div class="logo-mark" aria-hidden="true">ERP</div>
      <div class="logo-text">系统菜单</div>
    </div>
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
  { label: '订单管理', key: '/order' },
  { label: '知识库助手', key: '/knowledge-base' }
]

// 根据当前路由计算菜单激活项。
const activeKey = computed(() => {
  if (route.path.startsWith('/customer')) return '/customer'
  if (route.path.startsWith('/product')) return '/product'
  if (route.path.startsWith('/knowledge-base')) return '/knowledge-base'
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

/* 菜单标题区域：展示 Logo 与标题。 */
.logo {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-bottom: 12px;
}

/* 侧边栏 Logo 图形：用于强化系统品牌识别。 */
.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: linear-gradient(135deg, #18a058, #36ad6a);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 28px;
  text-align: center;
  letter-spacing: 0.5px;
}

/* 菜单标题文字。 */
.logo-text {
  font-weight: 600;
  color: #1f2329;
}
</style>
