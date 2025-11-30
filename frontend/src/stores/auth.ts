// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/axios'
import { jwtDecode } from 'jwt-decode'

interface DecodedToken {
  username: string
  is_admin: boolean
  exp: number
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')
  const tokenExp = ref<number>(Number(localStorage.getItem('tokenExp')) || 0)
  const isLoggingIn = ref(false)
  const loginError = ref<string | null>(null)

  // 防止重複刷新的標記
  let isRefreshing = false
  let refreshSubscribers: Array<(token: string) => void> = []

  const isAuthenticated = computed(() => {
    if (!accessToken.value || !tokenExp.value) return false
    return tokenExp.value * 1000 > Date.now()
  })

  function setAuthInfo(access: string, refresh?: string, updateUserInfo = true) {
    accessToken.value = access
    localStorage.setItem('accessToken', access)

    const decodedToken = jwtDecode<DecodedToken>(access)
    tokenExp.value = decodedToken.exp
    localStorage.setItem('tokenExp', String(tokenExp.value))

    if (updateUserInfo) {
      username.value = decodedToken.username
      isAdmin.value = decodedToken.is_admin
      localStorage.setItem('username', username.value)
      localStorage.setItem('isAdmin', String(isAdmin.value))
    }

    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem('refreshToken', refresh)
    }

    axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
  }

  function clearAuthInfo() {
    accessToken.value = null
    refreshToken.value = null
    username.value = null
    isAdmin.value = false
    tokenExp.value = 0
    // 修正：不清除 loginError 和 isLoggingIn

    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('username')
    localStorage.removeItem('isAdmin')
    localStorage.removeItem('tokenExp')

    delete axios.defaults.headers.common['Authorization']

    refreshSubscribers = []
    isRefreshing = false
  }

  // 新增: 清除登入錯誤
  function clearLoginError() {
    loginError.value = null
  }

  async function login(user: string, pass: string): Promise<string | null> {
    isLoggingIn.value = true
    loginError.value = null

    try {
      const response = await axios.post<{
        access: string
        refresh: string
        redirect_url: string
      }>('/auth/login/', {
        username: user,
        password: pass,
      })

      const { access, refresh, redirect_url } = response.data
      setAuthInfo(access, refresh, true)
      return redirect_url
    } catch (error: any) {
      if (error.response) {
        switch (error.response.status) {
          case 401:
            loginError.value = '帳號或密碼錯誤'
            break
          case 400:
            loginError.value = '請求格式錯誤'
            break
          default:
            loginError.value = '登入失敗，請稍後再試'
        }
      } else if (error.request) {
        loginError.value = '無法連接到伺服器'
      } else {
        loginError.value = '發生未知錯誤'
      }
      return null
    } finally {
      isLoggingIn.value = false
    }
  }

  async function refreshTokenAction(): Promise<string> {
    if (!refreshToken.value) {
      clearAuthInfo()
      throw new Error('No refresh token available')
    }

    if (isRefreshing) {
      return new Promise((resolve) => {
        refreshSubscribers.push((token: string) => {
          resolve(token)
        })
      })
    }

    isRefreshing = true

    try {
      // 修正: 刷新時暫時移除 Authorization header
      const tempAuth = axios.defaults.headers.common['Authorization']
      delete axios.defaults.headers.common['Authorization']

      const response = await axios.post<{ access: string }>('/auth/token/refresh/', {
        refresh: refreshToken.value,
      })

      const { access } = response.data

      // setAuthInfo 會設置新的 Authorization header，所以不需要手動恢復
      setAuthInfo(access, undefined, false)

      // 通知所有等待的請求
      refreshSubscribers.forEach((callback) => callback(access))
      refreshSubscribers = []

      return access
    } catch (error: any) {
      // Refresh token 失敗，清除所有資訊
      clearAuthInfo()
      throw new Error('Token refresh failed')
    } finally {
      isRefreshing = false
    }
  }

  async function register(user: string, pass: string): Promise<void> {
    const publicAxios = axios.create({
      baseURL: axios.defaults.baseURL,
    })

    await publicAxios.post('/auth/register/', {
      username: user,
      password: pass,
    })
  }

  function logout() {
    clearAuthInfo()
    loginError.value = null // ✅ 只有登出時才清除
    isLoggingIn.value = false
  }

  return {
    // 狀態
    accessToken,
    refreshToken,
    username,
    isAdmin,
    isAuthenticated,
    isLoggingIn,
    loginError,

    // 方法
    login,
    register,
    logout,
    refreshTokenAction,
    clearLoginError, // 新增: 暴露清除錯誤的方法
  }
})
