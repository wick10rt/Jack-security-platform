import { ref, onMounted } from 'vue'
import axios from '@/axios'
import { useAuthStore } from '@/stores/auth'

interface LabCompletion {
  id: string
  status: 'pending_reflection' | 'completed'
  user: string
  lab: string
}

export function useProgress() {
  const authStore = useAuthStore()
  const completions = ref<LabCompletion[]>([])
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  // 驗證是否登入
  const fetchProgress = async () => {
    if (!authStore.isAuthenticated) {
      error.value = '請先去登入'
      isLoading.value = false
      return
    }

    isLoading.value = true
    error.value = null

    // IE-2 獲取使用者資料
    try {
      const response = await axios.get<LabCompletion[]>('/progress/')
      completions.value = response.data
    } catch (err) {
      error.value = '獲取使用者資料失敗，請重試'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  // 自動獲取數據
  onMounted(() => {
    fetchProgress()
  })

  return {
    completions,
    isLoading,
    error,
    fetchProgress,
  }
}
