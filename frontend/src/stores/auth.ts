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

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')
  const tokenExp = ref<number>(Number(localStorage.getItem('tokenExp')) || 0)
  const isLoggingIn = ref(false)
  const loginError = ref<string | null>(null)

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
      return new Promise((resolve) => {
        refreshSubscribers.push((token: string) => {
          resolve(token)
        })
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

      refreshSubscribers.forEach((callback) => callback(access))
      refreshSubscribers = []

      return access
    } catch {
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
