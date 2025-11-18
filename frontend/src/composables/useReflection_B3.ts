import { ref, reactive } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'

interface ReflectionResponse {
  id: string
  user: string
  lab: string
  payload: string
  reflection: string
}

export function useReflection(labId: Ref<string>) {
  const reflectionForm = reactive({
    reflection: '',
    payload: '',
  })

  const isSubmitting = ref(false)
  const submissionError = ref<string | null>(null)
  const submissionSuccess = ref(false)
  const isLoading = ref(false)

  // EE-7 使用者提交表單
  const submitReflection = async () => {
    isSubmitting.value = true
    submissionError.value = null
    submissionSuccess.value = false

    // IE-7 B3 處理防禦表單
    try {
      await axios.post<ReflectionResponse>(`/labs/${labId.value}/reflection/`, {
        reflection: reflectionForm.reflection,
        payload: reflectionForm.payload,
      })
      submissionSuccess.value = true
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        submissionError.value =
          err.response.data.detail || err.response.data.error || '提交失敗, 請重試'
      } else {
        submissionError.value = '發生錯誤, 請重試'
      }
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    reflectionForm,
    isSubmitting,
    submissionError,
    submissionSuccess,
    isLoading,
    submitReflection,
  }
}
