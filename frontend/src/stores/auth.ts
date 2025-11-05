import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/axios'
import { jwtDecode } from 'jwt-decode'

interface UserInfo {
  username: string
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<boolean>(localStorage.getItem('isAdmin') === 'true')
  const isAuthenticated = computed(() => !!accessToken.value)

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

  function clearAuthInfo() {
    accessToken.value = null
    username.value = null
    isAdmin.value = false

    localStorage.removeItem('accessToken')
    localStorage.removeItem('username')
    localStorage.removeItem('isAdmin')

    delete axios.defaults.headers.common['Authorization']
  }

  async function login(user: string, pass:string): Promise<string> {
    try{
      const response = await axios.post<{access: string; redirect_url: string}>('/auth/login/', {
        username: user,
        password: pass,
      })
      
      const {access, redirect_url} = response.data
      setAuthInfo(access)
      return redirect_url
    }
    catch (error) {
      clearAuthInfo()
      throw error
    }
  }
  async function register(user: string, pass:string): Promise<void> {
    await axios.post('/auth/register/', {
      username: user,
      password: pass,
    })
  }

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