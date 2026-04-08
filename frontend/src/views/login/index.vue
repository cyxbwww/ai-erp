<template>
  <div class="login-page">
    <n-card title="AI 智能销售系统登录" :bordered="false" style="width: 380px">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="form.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="请输入密码" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleLogin">登录</n-button>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
// 登录页面：用于用户身份校验并写入 access/refresh 双令牌登录态。
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NForm, NFormItem, NInput, type FormInst, type FormRules, useMessage } from 'naive-ui'
import { loginApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: '123456'
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  await formRef.value?.validate()
  loading.value = true
  try {
    const res = await loginApi({ username: form.username, password: form.password })
    if (res.data.code === 0) {
      const {
        access_token,
        refresh_token,
        token_type,
        expires_in,
        username,
        role,
        permissions
      } = res.data.data
      authStore.setAuth(
        access_token,
        refresh_token,
        token_type || 'Bearer',
        expires_in || 0,
        username,
        role,
        permissions || []
      )
      message.success('登录成功')
      router.push('/dashboard')
    } else {
      message.error(res.data.message || '登录失败')
    }
  } catch (_error) {
    message.error('登录请求失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 登录页背景样式：用于提升面试演示观感。 */
.login-page {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f4f8ff, #eef3ff);
}
</style>
