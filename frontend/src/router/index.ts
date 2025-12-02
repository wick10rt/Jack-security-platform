import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/F1_LoginView.vue'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      // F1 登入頁面
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      // F2 Dashboard
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/F2_DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      // F3 Lab 目錄
      path: '/labs',
      name: 'labs',
      component: () => import('../views/F3_LabsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      // F4 Lab 詳細頁面
      path: '/labs/:id',
      name: 'lab-detail',
      component: () => import('../views/F4_LabDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('../views/NotFoundView.vue'),
    },
  ],
})

// C-1 沒登入的用戶不能進入F2~F4頁面
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router
