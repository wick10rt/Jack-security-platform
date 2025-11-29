import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import myaxios from '@/axios'
import axios from 'axios'

const ADMIN_ACCESS_KEY = import.meta.env.VITE_ADMIN_ACCESS_KEY ?? ''

export function useAuthForm() {
  const authStore = useAuthStore()
  const router = useRouter()

  // 登入註冊切換
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

  // IE-0 處理註冊表單
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
      // --- 关键修改：现在 isAxiosError 可以被正确识别 ---
      if (axios.isAxiosError(error) && error.response) {
      // ------------------------------------------------
        const data = error.response.data;
        if (error.response.status === 400 && typeof data === 'object' && data !== null) {
          Object.assign(registerErrors, data as Record<string, string[]>);
        } else {
          const detail = (data as Record<string, unknown>)?.['detail']
          registerErrors.non_field_errors = [
            typeof detail === 'string' ? detail : '发生未知错误，请重试',
          ]
        }
      } else {
        registerErrors.non_field_errors = ['网路异常，请稍后重试']
      }
}
  }

  // IE-1 處理登入表單
  const loginForm = reactive({ username: '', password: '' })
  const loginError = ref<string | null>(null)

  const handleLogin = async () => {
    loginError.value = null
    try {
      const redirectUrl = await authStore.login(loginForm.username, loginForm.password)
      if (redirectUrl === '/admin/') {
        const adminUrl = new URL('http://127.0.0.1:8000/admin/')
        if (ADMIN_ACCESS_KEY) {
          adminUrl.searchParams.set('admin_key', ADMIN_ACCESS_KEY)
        }
        window.location.href = adminUrl.toString()
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
