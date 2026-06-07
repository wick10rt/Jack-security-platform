import { ref, computed, onMounted } from 'vue'
import axios from '@/axios'

interface LabSummary {
  id: string
  title: string
  category: string
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const PAGE_SIZE = 10

export function getLabList() {
  const labs = ref<LabSummary[]>([])
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  const currentPage = ref(1)
  const totalCount = ref(0)
  const hasNext = ref(false)
  const hasPrev = ref(false)
  const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))

  const fetchLabs = async (page = 1) => {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.get<Paginated<LabSummary>>('/labs/', {
        params: { page },
      })
      labs.value = response.data.results
      totalCount.value = response.data.count
      hasNext.value = !!response.data.next
      hasPrev.value = !!response.data.previous
      currentPage.value = page
    } catch (err) {
      console.error(err)
      error.value = '無法獲取實驗列表,請重試'
    } finally {
      isLoading.value = false
    }
  }

  const nextPage = () => {
    if (hasNext.value) fetchLabs(currentPage.value + 1)
  }
  const prevPage = () => {
    if (hasPrev.value) fetchLabs(currentPage.value - 1)
  }

  onMounted(() => fetchLabs(1))

  return {
    labs,
    isLoading,
    error,
    fetchLabs,
    currentPage,
    totalPages,
    hasNext,
    hasPrev,
    nextPage,
    prevPage,
  }
}
