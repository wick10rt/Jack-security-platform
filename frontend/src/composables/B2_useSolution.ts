import { ref, computed, watch } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'

interface Solution {
  payload: string
  reflection: string
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function useSolutions(labId: Ref<string>, submissionStatus: Ref<string>) {
  const solutions = ref<Solution[]>([])
  const showSolutions = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const currentPage = ref(1)
  const totalCount = ref(0)
  const hasNext = ref(false)
  const hasPrev = ref(false)
  // 每頁筆數由 API 回應推導（後端 PAGE_SIZE 可調），不寫死
  const pageSize = ref(10)
  const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

  const fetchSolutions = async (page = 1) => {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get<Paginated<Solution>>(
        `/labs/${labId.value}/solutions/`,
        { params: { page } },
      )
      solutions.value = response.data.results
      if (response.data.results.length > pageSize.value) {
        pageSize.value = response.data.results.length
      }
      totalCount.value = response.data.count
      hasNext.value = !!response.data.next
      hasPrev.value = !!response.data.previous
      currentPage.value = page
    } catch {
      error.value = '獲取資料失敗，請重試'
    } finally {
      isLoading.value = false
    }
  }

  const nextPage = () => {
    if (hasNext.value) fetchSolutions(currentPage.value + 1)
  }
  const prevPage = () => {
    if (hasPrev.value) fetchSolutions(currentPage.value - 1)
  }

  const toggleSolutions = () => {
    showSolutions.value = !showSolutions.value
    if (showSolutions.value && solutions.value.length === 0) {
      fetchSolutions()
    }
  }

  watch(
    () => submissionStatus.value,
    (status) => {
      if (status === 'already_completed') {
        showSolutions.value = false
        if (solutions.value.length === 0) {
          fetchSolutions()
        }
      }
    },
    { immediate: true },
  )

  return {
    solutions,
    showSolutions,
    isLoading,
    error,
    toggleSolutions,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    nextPage,
    prevPage,
  }
}
