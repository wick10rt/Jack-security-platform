// src/composables/useProgress.ts
import { ref, onMounted } from 'vue'
import axios from '@/axios'
import { useAuthStore } from '@/stores/auth'

// 定义从后端 API 返回的单条进度记录的类型接口
interface LabCompletion {
  id: string
  status: 'pending_reflection' | 'completed'
  user: string // 我们之前设定 B3 返回的是 username
  lab: string // 我们之前设定 B3 返回的是 lab title
}

export function useProgress() {
  const authStore = useAuthStore()

  // --- 状态定义 ---
  // 用于储存从 API 获取到的进度列表
  const completions = ref<LabCompletion[]>([])
  // 用于表示数据是否正在加载中
  const isLoading = ref(true)
  // 用于储存可能发生的错误
  const error = ref<string | null>(null)

  // --- 核心逻辑：获取数据的函数 ---
  const fetchProgress = async () => {
    // 确保使用者已登入
    if (!authStore.isAuthenticated) {
      error.value = 'User is not authenticated.'
      isLoading.value = false
      return
    }

    isLoading.value = true
    error.value = null
    try {
      // 呼叫 B3 的 /progress/ API
      const response = await axios.get<LabCompletion[]>('/progress/')
      completions.value = response.data
    } catch (err) {
      error.value = 'Failed to fetch progress data.'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  // --- Vue 生命週期鉤子 ---
  // onMounted 会在元件挂载到 DOM 后自动执行
  onMounted(() => {
    fetchProgress()
  })

  // 从 Composable 中返回所有需要在元件中使用的数据和方法
  return {
    completions,
    isLoading,
    error,
    fetchProgress, // 也可暴露一个手动刷新的方法
  }
}
