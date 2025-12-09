import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { isAxiosError } from 'axios'
import { useToast } from 'vue-toastification'

const ADMIN_ACCESS_KEY = import.meta.env.VITE_ADMIN_ACCESS_KEY ?? ''
const ADMIN_URL = import.meta.env.VITE_ADMIN_URL ?? 'http://127.0.0.1:8000/admin/'

export function useAuthForm() {
  const authStore = useAuthStore()
  const router = useRouter()
  const { isLoggingIn, loginError } = storeToRefs(authStore)
  const isRegisterMode = ref(false)
  const toast = useToast()

  // 登入/註冊切換
  const toggleMode = () => {
    isRegisterMode.value = !isRegisterMode.value

    authStore.clearLoginError()

    Object.keys(registerErrors).forEach(
      (key) => delete registerErrors[key as keyof typeof registerErrors],
    )

    loginForm.username = ''
    loginForm.password = ''
    registerForm.username = ''
    registerForm.password = ''
  }

  // EE-0 使用者註冊
  const registerForm = reactive({ username: '', password: '' })
  const registerErrors = reactive<{
    username?: string[]
    password?: string[]
    non_field_errors?: string[]
  }>({})
  const isRegistering = ref(false)

  const handleRegister = async () => {
    if (isRegistering.value) return

    isRegistering.value = true

    Object.keys(registerErrors).forEach(
      (key) => delete registerErrors[key as keyof typeof registerErrors],
    )

    try {
      await authStore.register(registerForm.username, registerForm.password)
      toast.success('註冊成功')
      toggleMode()
    } catch (error) {
      if (isAxiosError(error) && error.response) {
        const data = error.response.data

        if (error.response.status === 400 && typeof data === 'object' && data !== null) {
          Object.assign(registerErrors, data as Record<string, string[]>)
        } else {
          const detail = (data as Record<string, unknown>)?.detail
          registerErrors.non_field_errors = [
            typeof detail === 'string' ? detail : '發生未知錯誤，請重試',
          ]
        }
      } else if (isAxiosError(error) && error.request) {
        registerErrors.non_field_errors = ['無法連接到伺服器']
      } else {
        registerErrors.non_field_errors = ['發生未知錯誤，請重試']
      }
    } finally {
      isRegistering.value = false
    }
  }

  // EE-1 使用者登入
  const loginForm = reactive({ username: '', password: '' })

  const handleLogin = async () => {
    if (isLoggingIn.value) return

    const redirectUrl = await authStore.login(loginForm.username, loginForm.password)

    // 根據後端回傳的 redirect_url 進行導向
    if (redirectUrl) {
      if (redirectUrl === '/admin/') {
        const adminUrl = new URL(ADMIN_URL)
        if (ADMIN_ACCESS_KEY) {
          adminUrl.searchParams.set('admin_key', ADMIN_ACCESS_KEY)
        }
        window.location.href = adminUrl.toString()
      } else if (redirectUrl.startsWith('http://') || redirectUrl.startsWith('https://')) {
        window.location.href = redirectUrl
      } else {
        await router.push(redirectUrl)
      }
    }
  }

  return {
    isRegisterMode,
    toggleMode,
    loginForm,
    loginError,
    isLoggingIn,
    handleLogin,
    registerForm,
    registerErrors,
    isRegistering,
    handleRegister,
  }
}
