// 前端入口文件：初始化 Vue 应用、Pinia 状态与路由。
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles.css'

const app = createApp(App)
const pinia = createPinia()

// 注册状态管理
app.use(pinia)
// 注册路由
app.use(router)
// 挂载根节点
app.mount('#app')
