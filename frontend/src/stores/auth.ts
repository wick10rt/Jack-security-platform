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
  // 取出認證資訊
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')
  const tokenExp = ref<number>(Number(localStorage.getItem('tokenexp')) || 0)

  const isAuthenticated = computed(() => {
    if(!accessToken.value || !tokenExp.value) return false
    return tokenExp.value * 1000 > Date.now()
  })

  // 解析token, 儲存使用者資訊
  function setAuthInfo(access: string, refresh?: string) {
    accessToken.value = access

    if(refresh){
      refreshToken.value = refresh
      localStorage.setItem('refreshToken', refresh)
    }

    const decodedToken = jwtDecode<DecodedToken>(access)
    username.value = decodedToken.username
    isAdmin.value = decodedToken.is_admin
    tokenExp.value = decodedToken.exp

    localStorage.setItem('accessToken', access)
    localStorage.setItem('username', username.value)
    localStorage.setItem('isAdmin', String(isAdmin.value))
    localStorage.setItem('tokenexp', String(tokenExp.value))

    axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
  }

  // 清除使用者資訊
  function clearAuthInfo() {
    accessToken.value = null
    refreshToken.value = null
    tokenExp.value = 0
    username.value = null
    isAdmin.value = false

    localStorage.removeItem('refreshToken')
    localStorage.removeItem('accessToken')
    localStorage.removeItem('username')
    localStorage.removeItem('isAdmin')
    localStorage.removeItem('tokenexp')

    delete axios.defaults.headers.common['Authorization']
  }

  async function refreshTokenAction(): Promise<void> {
    if (!refreshToken.value) {
      clearAuthInfo()
      throw new Error('No refresh token available')
    }
    try{
      const response = await axios.post<{ access: string }>('/auth/refresh/', {
        refresh: refreshToken.value,
      })
      const { access } = response.data
      setAuthInfo(access)
    } catch (error) {
      clearAuthInfo()
      throw error
    }
  }
  
  // 處理 EE-1 使用者登入
  async function login(user: string, pass: string): Promise<string> {
    try {
      const response = await axios.post<{ access: string; refresh: string; redirect_url: string }>('/auth/login/', {
        username: user,
        password: pass,
      })

      const { access, refresh, redirect_url } = response.data
      setAuthInfo(access, refresh)
      return redirect_url
    } catch (error) {
      clearAuthInfo()
      throw error
    }
  }

  // 處理 EE-0 使用者註冊
  async function register(user: string, pass: string): Promise<void> {
    const originalAuthHeader = axios.defaults.headers.common['Authorization']
    delete axios.defaults.headers.common['Authorization']

    try {
      await axios.post('/auth/register/', {
        username: user,
        password: pass,
      })
    } finally {
      if (originalAuthHeader) {
        axios.defaults.headers.common['Authorization'] = originalAuthHeader
      }
    }
  }

  // 處理使用者登出
  function logout() {
    clearAuthInfo()
  }

  return {
    accessToken,
    username,
    isAdmin,
    isAuthenticated,
    refreshToken,
    login,
    register,
    logout,
    refreshTokenAction,
  }
})
