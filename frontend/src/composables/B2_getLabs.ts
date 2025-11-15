import { ref, onMounted } from 'vue'
import axios from '@/axios'

interface LabSummary {
  id: string
  title: string
  category: string
}

// IE-3 取得實驗列表
export function getLabList() {
  const labs = ref<LabSummary[]>([])
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  const fetchLabs = async () => {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get<LabSummary[]>('/labs/')
      labs.value = response.data
    } catch (err) {
      console.error(err)
      error.value = '無法獲取實驗列表,請重試'
    } finally {
      isLoading.value = false
    }
  }

  // 自動獲取數據
  onMounted(fetchLabs)

  return {
    labs,
    isLoading,
    error,
    fetchLabs,
  }
}
