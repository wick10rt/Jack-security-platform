import { ref, onMounted, toRefs } from 'vue'
import myaxios from '@/axios'
import axios from 'axios'
import type { Ref } from 'vue'

interface LabDetail {
  id: string
  title: string
  description: string
  category: string
}

// IE-4 獲取實驗詳情
export function LabDetail(labId: Ref<string>) {
  const lab = ref<LabDetail | null>(null)
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  const fetchLabDetail = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await myaxios.get<LabDetail>(`/labs/${labId.value}/`)
      lab.value = response.data
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        error.value = '實驗不存在'
      } else {
        error.value = '無法取得資料,請重試'
      }
    } finally {
      isLoading.value = false
    }
  }

  onMounted(fetchLabDetail)

  return {
    lab,
    isLoading,
    error,
  }
}
