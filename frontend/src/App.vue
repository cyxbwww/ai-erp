<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <router-view />
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
// 应用根组件：统一注入 Naive UI 的中文语言、消息和通知能力。
import { NConfigProvider, NMessageProvider, NNotificationProvider, dateZhCN, zhCN } from 'naive-ui'
</script>
