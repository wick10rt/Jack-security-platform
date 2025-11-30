// src/axios.ts
import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 10000,
})

// ===== 請求攔截器 =====
axiosInstance.interceptors.request.use(
  (config) => {
    // 修正：從 localStorage 讀取，避免循環依賴
    const token = localStorage.getItem('accessToken')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// ===== 回應攔截器 =====
axiosInstance.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // 如果是 401 錯誤且還沒重試過
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 修正 1：排除登入和刷新 token 的請求
      if (
        originalRequest.url?.includes('/auth/login/') ||
        originalRequest.url?.includes('/auth/token/refresh/') ||
        originalRequest.url?.includes('/auth/register/')
      ) {
        console.log('Auth endpoint failed, not attempting refresh')
        return Promise.reject(error)
      }

      // 修正 2：檢查是否有 refresh token
      const refreshToken = localStorage.getItem('refreshToken')
      if (!refreshToken) {
        console.log('No refresh token available, cannot refresh')
        return Promise.reject(error)
      }

      originalRequest._retry = true

      try {
        console.log('Access token expired. Attempting to refresh...')

        // 修正 3：動態導入 store 避免循環依賴
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()

        // 嘗試刷新 token
        const newToken = await authStore.refreshTokenAction()

        console.log('Token refreshed successfully.')

        // 更新原始請求的 header
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }

        // 重新發送原始請求
        return axiosInstance(originalRequest)
      } catch (refreshError) {
        // 修正 4：不要調用 logout()，因為 refreshTokenAction 已經調用了 clearAuthInfo()
        console.error('Failed to refresh token. Redirecting to login.')

        // 只在需要時導向登入頁
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }

        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export default axiosInstance
