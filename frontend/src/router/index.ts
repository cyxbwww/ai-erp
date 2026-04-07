// 路由配置文件：定义系统页面路由与登录权限守卫。
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AdminLayout from '@/layout/AdminLayout.vue'

// 路由表：统一维护页面路径与权限点。
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue')
  },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '销售看板', menuKey: 'dashboard', permission: 'dashboard:view' }
      },
      {
        path: 'customer',
        name: 'Customer',
        component: () => import('@/views/customer/index.vue'),
        meta: { title: '客户管理', menuKey: 'customer', permission: 'customer:view' }
      },
      {
        path: 'customer/detail/:id',
        name: 'CustomerDetail',
        component: () => import('@/views/customer/detail.vue'),
        meta: { title: '客户详情', menuKey: 'customer', permission: 'customer:view' }
      },
      {
        path: 'product',
        name: 'Product',
        component: () => import('@/views/product/index.vue'),
        meta: { title: '商品管理', menuKey: 'product', permission: 'product:view' }
      },
      {
        path: 'order',
        name: 'Order',
        component: () => import('@/views/order/index.vue'),
        meta: { title: '订单管理', menuKey: 'order', permission: 'order:view' }
      },
      {
        path: 'order/create',
        name: 'OrderCreate',
        component: () => import('@/views/order/form.vue'),
        meta: { title: '新建订单', menuKey: 'order', permission: 'order:view' }
      },
      {
        path: 'order/edit/:id',
        name: 'OrderEdit',
        component: () => import('@/views/order/form.vue'),
        meta: { title: '编辑订单', menuKey: 'order', permission: 'order:view' }
      },
      {
        path: 'order/detail/:id',
        name: 'OrderDetail',
        component: () => import('@/views/order/detail.vue'),
        meta: { title: '订单详情', menuKey: 'order', permission: 'order:view' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫：处理登录态校验与权限拦截。
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role') || ''
  const permissions: string[] = JSON.parse(localStorage.getItem('permissions') || '[]')

  // 未登录用户访问受保护页面时跳转登录页。
  if (to.path !== '/login' && !token) {
    next('/login')
    return
  }

  // 已登录用户访问登录页时回到首页。
  if (to.path === '/login' && token) {
    next('/dashboard')
    return
  }

  // 非管理员根据权限点进行页面级访问控制。
  const requiredPermission = to.meta?.permission as string | undefined
  if (requiredPermission && role !== 'admin' && !permissions.includes(requiredPermission)) {
    next('/dashboard')
    return
  }

  next()
})

export default router
