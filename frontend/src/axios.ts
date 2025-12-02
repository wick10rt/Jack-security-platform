import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 10000,
})

// 自動加上 Token 到每個請求的標頭
axiosInstance.interceptors.request.use(
  (config) => {
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

// 自動刷新 Token
axiosInstance.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (
        originalRequest.url?.includes('/auth/login/') ||
        originalRequest.url?.includes('/auth/token/refresh/') ||
        originalRequest.url?.includes('/auth/register/')
      ) {
        console.log('跳過 token 刷新')
        return Promise.reject(error)
      }

      const refreshToken = localStorage.getItem('refreshToken')
      if (!refreshToken) {
        console.log('沒有可用的 refresh token，無法刷新')
        return Promise.reject(error)
      }

      originalRequest._retry = true

      try {
        console.log('刷新 token 中')

        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()

        const newToken = await authStore.refreshTokenAction()

        console.log('成功刷新 token')

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }

        return axiosInstance(originalRequest)
      } catch (refreshError) {
        console.error('刷新失敗')

        // 刷新失敗 導向 F1 登入頁面
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
