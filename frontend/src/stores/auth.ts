import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/axios'
import { isAxiosError } from 'axios'
import { jwtDecode } from 'jwt-decode'

interface DecodedToken {
  username: string
  is_admin: boolean
  exp: number
}

function tokenExpiry(token: string | null): number {
  if (!token) return 0
  try {
    return jwtDecode<{ exp: number }>(token).exp
  } catch {
    return 0
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')
  const isLoggingIn = ref(false)
  const loginError = ref<string | null>(null)

  let isRefreshing = false
  let refreshSubscribers: Array<{
    resolve: (token: string) => void
    reject: (error: unknown) => void
  }> = []

  // 以 refresh token 的效期判斷登入態：access 過期會由 axios 自動續期，
  // 不該因為 access 到期（30 分鐘）就把人踢回登入頁
  const isAuthenticated = computed(() => tokenExpiry(refreshToken.value) * 1000 > Date.now())

  function setAuthInfo(access: string, refresh?: string, updateUserInfo = true) {
    accessToken.value = access
    localStorage.setItem('accessToken', access)

    if (updateUserInfo) {
      const decodedToken = jwtDecode<DecodedToken>(access)
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

    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('username')
    localStorage.removeItem('isAdmin')
    localStorage.removeItem('tokenExp')

    delete axios.defaults.headers.common['Authorization']

    refreshSubscribers = []
    isRefreshing = false
  }

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
    } catch (error) {
      if (isAxiosError(error) && error.response) {
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
      } else if (isAxiosError(error) && error.request) {
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
      throw new Error('沒有可用的 refresh token')
    }

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        refreshSubscribers.push({ resolve, reject })
      })
    }

    isRefreshing = true

    try {
      delete axios.defaults.headers.common['Authorization']

      const response = await axios.post<{ access: string }>('/auth/token/refresh/', {
        refresh: refreshToken.value,
      })

      const { access } = response.data

      setAuthInfo(access, undefined, false)

      refreshSubscribers.forEach((sub) => sub.resolve(access))
      refreshSubscribers = []

      return access
    } catch (err) {
      // 失敗時逐一 reject 排隊中的並發請求，否則它們會 hang 到 timeout（B7）
      const subscribers = refreshSubscribers
      refreshSubscribers = []
      subscribers.forEach((sub) => sub.reject(err))
      clearAuthInfo()
      throw new Error('刷新 token 失敗')
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

  async function logout() {
    try {
      if (refreshToken.value) {
        await axios.post('/auth/logout/', { refresh: refreshToken.value })
      }
    } catch (error) {
      console.error('登出撤銷 token 失敗（已忽略）:', error)
    }
    clearAuthInfo()
    loginError.value = null
    isLoggingIn.value = false
  }

  return {
    accessToken,
    refreshToken,
    username,
    isAdmin,
    isAuthenticated,
    isLoggingIn,
    loginError,
    login,
    register,
    logout,
    refreshTokenAction,
    clearLoginError,
  }
})
