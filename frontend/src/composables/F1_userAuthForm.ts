import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

export function useAuthForm() {
  const authStore = useAuthStore()
  const router = useRouter()

  const isRegisterMode = ref(false)
  const toggleMode = () => {
    isRegisterMode.value = !isRegisterMode.value
    loginError.value = null
    Object.keys(registerErrors).forEach(
      (key) => delete registerErrors[key as keyof typeof registerErrors],
    )
    loginForm.username = ''
    loginForm.password = ''
    registerForm.username = ''
    registerForm.password = ''
  }

  // 處理 EE-0 註冊表單
  const registerForm = reactive({ username: '', password: '' })
  const registerErrors = reactive<{
    username?: string[]
    password?: string[]
    non_field_errors?: string[]
  }>({})

  const handleRegister = async () => {
    Object.keys(registerErrors).forEach(
      (key) => delete registerErrors[key as keyof typeof registerErrors],
    )
    try {
      await authStore.register(registerForm.username, registerForm.password)
      alert('註冊成功')
      toggleMode()
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 400) {
        Object.assign(registerErrors, error.response.data)
      } else {
        registerErrors.non_field_errors = ['發生未知錯誤，請重試']
      }
    }
  }

  // 處理 EE-1 登入表單
  const loginForm = reactive({ username: '', password: '' })
  const loginError = ref<string | null>(null)

  const handleLogin = async () => {
    loginError.value = null
    try {
      const redirectUrl = await authStore.login(loginForm.username, loginForm.password)
      if (redirectUrl === '/admin/') {
        window.location.href = 'http://127.0.0.1:8000/admin/'
      } else {
        await router.push(redirectUrl)
      }
    } catch {
      loginError.value = '登入失敗，帳號或密碼錯誤'
    }
  }

  return {
    isRegisterMode,
    toggleMode,
    loginForm,
    loginError,
    handleLogin,
    registerForm,
    registerErrors,
    handleRegister,
  }
}
