import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/axios'
import { jwtDecode } from 'jwt-decode'

interface UserInfo {
  username: string
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  // 取出認證資訊
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')

  const isAuthenticated = computed(() => !!accessToken.value)

  // 解析token, 儲存使用者資訊
  function setAuthInfo(token: string) {
    accessToken.value = token

    const decodedToken = jwtDecode<UserInfo>(token)
    username.value = decodedToken.username
    isAdmin.value = decodedToken.is_admin

    localStorage.setItem('accessToken', token)
    localStorage.setItem('username', username.value)
    localStorage.setItem('isAdmin', String(isAdmin.value))

    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  // 清除使用者資訊
  function clearAuthInfo() {
    accessToken.value = null
    username.value = null
    isAdmin.value = false

    localStorage.removeItem('accessToken')
    localStorage.removeItem('username')
    localStorage.removeItem('isAdmin')

    delete axios.defaults.headers.common['Authorization']
  }

  // 處理 EE-1 使用者登入
  async function login(user: string, pass: string): Promise<string> {
    try {
      const response = await axios.post<{ access: string; redirect_url: string }>('/auth/login/', {
        username: user,
        password: pass,
      })

      const { access, redirect_url } = response.data
      setAuthInfo(access)
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
    login,
    register,
    logout,
  }
})
