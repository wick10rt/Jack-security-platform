import { ref, onMounted } from 'vue'
import axios from '@/axios'
import { isAxiosError } from 'axios'
import type { Ref } from 'vue'

interface LabProgress {
  id: string
  status: 'pending_reflection' | 'completed'
  user: string
  lab: string
  lab_id?: string
  lab_title?: string
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function useSubmit(labId: Ref<string>) {
  const answer = ref('')
  const isSubmitting = ref(false)
  const submissionError = ref<string | null>(null)
  const submissionStatus = ref<'not_started' | 'pending_reflection' | 'already_completed'>(
    'not_started',
  )
  const isLoadingStatus = ref(true)

  const fetchSubmissionStatus = async () => {
    isLoadingStatus.value = true
    try {
      const response = await axios.get<Paginated<LabProgress>>('/progress/', {
        params: { lab: labId.value },
      })
      const current = response.data.results[0]
      if (current?.status === 'completed') {
        submissionStatus.value = 'already_completed'
      } else if (current?.status === 'pending_reflection') {
        submissionStatus.value = 'pending_reflection'
      } else {
        submissionStatus.value = 'not_started'
      }
    } catch (err) {
      console.error('獲取狀態失敗:', err)
      submissionStatus.value = 'not_started'
    } finally {
      isLoadingStatus.value = false
    }
  }

  const submitAnswer = async () => {
    if (isSubmitting.value) return

    isSubmitting.value = true
    submissionError.value = null

    try {
      await axios.post(`/labs/${labId.value}/submit/`, {
        answer: answer.value,
      })

      submissionStatus.value = 'pending_reflection'
      answer.value = ''
    } catch (err) {
      if (isAxiosError(err) && err.response) {
        submissionError.value =
          err.response.data.detail || err.response.data.error || '提交失敗，請重試'
      } else {
        submissionError.value = '發生錯誤，請重試'
      }
    } finally {
      isSubmitting.value = false
    }
  }

  onMounted(() => {
    fetchSubmissionStatus()
  })

  return {
    answer,
    isSubmitting,
    submissionError,
    submissionStatus,
    isLoadingStatus,
    submitAnswer,
    fetchSubmissionStatus,
  }
}
