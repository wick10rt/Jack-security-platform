import { ref, computed, onMounted } from 'vue'
import axios from '@/axios'
import { useAuthStore } from '@/stores/auth'

interface LabCompletion {
  id: string
  status: 'pending_reflection' | 'completed'
  user: string
  lab: string
  lab_id: string
  lab_title: string
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

interface ProgressStats {
  total: number
  completed: number
  pending: number
}

export function useProgress() {
  const authStore = useAuthStore()
  const completions = ref<LabCompletion[]>([])
  const stats = ref<ProgressStats>({ total: 0, completed: 0, pending: 0 })
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  const currentPage = ref(1)
  const totalCount = ref(0)
  const hasNext = ref(false)
  const hasPrev = ref(false)
  // 每頁筆數由 API 回應推導（後端 PAGE_SIZE 可調），不寫死
  const pageSize = ref(10)
  const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

  const fetchStats = async () => {
    try {
      const response = await axios.get<ProgressStats>('/progress/stats/')
      stats.value = response.data
    } catch (err) {
      console.error(err)
    }
  }

  const fetchProgress = async (page = 1) => {
    if (!authStore.isAuthenticated) {
      error.value = '請先登入'
      isLoading.value = false
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await axios.get<Paginated<LabCompletion>>('/progress/', {
        params: { page },
      })
      completions.value = response.data.results
      if (response.data.results.length > pageSize.value) {
        pageSize.value = response.data.results.length
      }
      totalCount.value = response.data.count
      hasNext.value = !!response.data.next
      hasPrev.value = !!response.data.previous
      currentPage.value = page
    } catch (err) {
      error.value = '獲取使用者資料失敗，請重試'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  const nextPage = () => {
    if (hasNext.value) fetchProgress(currentPage.value + 1)
  }
  const prevPage = () => {
    if (hasPrev.value) fetchProgress(currentPage.value - 1)
  }

  onMounted(() => {
    fetchStats()
    fetchProgress(1)
  })

  return {
    completions,
    stats,
    isLoading,
    error,
    fetchProgress,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    nextPage,
    prevPage,
  }
}
