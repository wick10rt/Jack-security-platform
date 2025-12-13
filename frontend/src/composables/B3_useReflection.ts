import { ref, reactive, watch } from 'vue'
import myaxios from '@/axios'
import type { Ref } from 'vue'
import axios from 'axios'

interface ReflectionResponse {
  id: string
  user: string
  lab: string
  payload: string
  reflection: string
}

export function useReflection(labId: Ref<string>, submissionStatus: Ref<string>) {
  const reflectionForm = reactive({
    reflection: '',
    payload: '',
  })
  
  const isSubmitting = ref(false)
  const submissionError = ref<string | null>(null)
  const submissionSuccess = ref(false)
  const isLoading = ref(false)

  // 獲取已存在的防禦表單內容
  const fetchReflection = async () => {
    isLoading.value = true
    try {
      const response = await myaxios.get<ReflectionResponse>(`/labs/${labId.value}/reflection/`)
      
      // 如果有已存在的內容，填入表單
      if (response.data) {
        reflectionForm.payload = response.data.payload
        reflectionForm.reflection = response.data.reflection
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status !== 404) {
        console.error('獲取防禦表單失敗:', err)
      }
    } finally {
      isLoading.value = false
    }
  }

  watch(
    () => submissionStatus.value,
    (status) => {
      if (status === 'pending_reflection' || status === 'already_completed') {
        fetchReflection()
      }
    },
    { immediate: true }
  )

  // EE-7 使用者提交表單
  const submitReflection = async () => {
    isSubmitting.value = true
    submissionError.value = null
    submissionSuccess.value = false

    // IE-7 B3 處理防禦表單
    try {
      await myaxios.post<ReflectionResponse>(`/labs/${labId.value}/reflection/`, {
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
    fetchReflection,
  }
}