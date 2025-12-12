import { ref } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'

interface Solution {
  payload: string
  reflection: string
}

// EE-8 使用者查看其他人的解法
export function useSolutions(labId: Ref<string>) {
  const solutions = ref<Solution[]>([])
  const showSolutions = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // IE-8 向 B2 請求解法清單
  const fetchSolutions = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get<Solution[]>(`/labs/${labId.value}/solutions/`)
      solutions.value = response.data
    } catch (err) {
      error.value = '獲取資料失敗，請重試'
    } finally {
      isLoading.value = false
    }
  }

  const toggleSolutions = () => {
    showSolutions.value = !showSolutions.value
    if (showSolutions.value && solutions.value.length === 0) {
      fetchSolutions()
    }
  }

  return {
    solutions,
    showSolutions,
    isLoading,
    error,
    toggleSolutions,
  }
}
