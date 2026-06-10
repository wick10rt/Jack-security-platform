import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { isAxiosError } from 'axios'
import { useToast } from 'vue-toastification'

// admin 與 API 同一個 Django：未指定 VITE_ADMIN_URL 時直接由 API base 推導，
// 部署時就不會忘了改而導去 127.0.0.1
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'
const ADMIN_URL =
  import.meta.env.VITE_ADMIN_URL ?? new URL('/admin/', new URL(API_BASE, window.location.origin)).href

export function useAuthForm() {
  const authStore = useAuthStore()
  const router = useRouter()
  const route = useRoute()
  const { isLoggingIn, loginError } = storeToRefs(authStore)
  const isRegisterMode = ref(false)
  const toast = useToast()

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
    registerForm.passwordConfirm = ''
  }

  const registerForm = reactive({
    username: '',
    password: '',
    passwordConfirm: '',
  })

  const registerErrors = reactive<{
    username?: string[]
    password?: string[]
    non_field_errors?: string[]
  }>({})

  const isRegistering = ref(false)

  const passwordMismatch = computed(() => {
    if (registerForm.password && registerForm.passwordConfirm) {
      return registerForm.password !== registerForm.passwordConfirm
    }
    return false
  })

  const checkPasswordMatch = () => {}

  const handleRegister = async () => {
    if (isRegistering.value) return

    if (passwordMismatch.value) {
      toast.error('兩次輸入的密碼不一樣')
      return
    }

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

  const loginForm = reactive({ username: '', password: '' })

  const handleLogin = async () => {
    if (isLoggingIn.value) return
    const redirectUrl = await authStore.login(loginForm.username, loginForm.password)

    if (redirectUrl) {
      if (redirectUrl === '/admin/') {
        window.location.href = ADMIN_URL
      } else if (redirectUrl.startsWith('http://') || redirectUrl.startsWith('https://')) {
        window.location.href = redirectUrl
      } else {
        // 被路由守衛擋下來的話，登入後跳回原本要去的頁面（僅接受站內路徑）
        const intended = typeof route.query.redirect === 'string' ? route.query.redirect : ''
        const safeTarget =
          intended.startsWith('/') && !intended.startsWith('//') ? intended : redirectUrl
        await router.push(safeTarget)
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
    passwordMismatch,
    checkPasswordMatch,
  }
}

