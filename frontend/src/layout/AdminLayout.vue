<template>
  <n-layout has-sider class="erp-layout">
    <n-layout-sider bordered :width="220" collapse-mode="width">
      <AppSidebar />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered class="header">
        <div>AI 智能销售后台管理系统</div>
        <n-button text @click="handleLogout">退出登录</n-button>
      </n-layout-header>
      <n-layout-content content-style="padding: 16px;">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
// 后台布局组件：负责整体框架布局与退出登录。
import { useRouter } from 'vue-router'
import { NButton, NLayout, NLayoutContent, NLayoutHeader, NLayoutSider } from 'naive-ui'
import AppSidebar from '@/components/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 退出登录：清理本地登录态并跳转到登录页。
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* 后台整体布局占满可视区域 */
.erp-layout {
  width: 100%;
  height: 100%;
}

/* 顶部栏样式：左右布局标题与操作按钮 */
.header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}
</style>
