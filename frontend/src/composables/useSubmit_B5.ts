import { ref } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'

interface SuccessResponse {
  status: 'pending_reflection' | 'already_completed'
  message?: string
}

interface ErrorResponse {
  error: string
}

export function useSubmit(labId: Ref<string>) {
  const answer = ref('')
  const isSubmitting = ref(false)
  const submissionError = ref<string | null>(null)
  const submissionStatus = ref<SuccessResponse['status'] | null>(null)

  // EE-6 使用者提交答案
  const submitAnswer = async () => {
    isSubmitting.value = true
    submissionError.value = null
    submissionStatus.value = null

    try {
      const response = await axios.post<SuccessResponse>(`/labs/${labId.value}/submit/`, {
        answer: answer.value,
      })
      submissionStatus.value = response.data.status
    } catch (err) {
      if (axios.isAxiosError<ErrorResponse>(err) && err.response) {
        if (err.response.status === 400) {
          submissionError.value = '答案錯誤'
        }
      } else {
        submissionError.value = '發生錯誤,請重試'
      }
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    answer,
    isSubmitting,
    submissionError,
    submissionStatus,
    submitAnswer,
  }
}
