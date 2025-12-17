import { ref, onMounted } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'

interface LabProgress {
  id: string
  status: 'pending_reflection' | 'completed'
  user: string
  lab: string
  lab_id?: string
  lab_title?: string
}

export function useSubmit(labId: Ref<string>) {
  const answer = ref('')
  const isSubmitting = ref(false)
  const submissionError = ref<string | null>(null)
  const submissionStatus = ref<'not_started' | 'pending_reflection' | 'already_completed'>(
    'not_started',
  )
  const isLoadingStatus = ref(true)

  const extractLabId = (progress: LabProgress): string => {
    if (progress.lab) {
      return String(progress.lab)
    }
    if (progress.lab_id) {
      return String(progress.lab_id)
    }
    return ''
  }

  // 取的進行實驗的狀態
  const fetchSubmissionStatus = async () => {
    isLoadingStatus.value = true
    try {
      const response = await axios.get<LabProgress[]>('/progress/')

      console.log('Progress API Response:', response.data)
      console.log('Current Lab ID:', labId.value)

      const currentLabProgress = response.data.find((progress) => {
        const progressLabId = extractLabId(progress)
        const currentLabId = String(labId.value)

        console.log(`Comparing: "${progressLabId}" === "${currentLabId}"`)

        return progressLabId === currentLabId
      })

      console.log('Found Progress:', currentLabProgress)

      if (currentLabProgress) {
        if (currentLabProgress.status === 'completed') {
          submissionStatus.value = 'already_completed'
          console.log('Status set to: already_completed')
        } else if (currentLabProgress.status === 'pending_reflection') {
          submissionStatus.value = 'pending_reflection'
          console.log('Status set to: pending_reflection')
        }
      } else {
        submissionStatus.value = 'not_started'
        console.log('Status set to: not_started (no matching lab found)')
      }
    } catch (err) {
      console.error('獲取狀態失敗:', err)
      submissionStatus.value = 'not_started'
    } finally {
      isLoadingStatus.value = false
      console.log('Loading complete. Final status:', submissionStatus.value)
    }
  }

  // EE-6 提交答案
  const submitAnswer = async () => {
    if (isSubmitting.value) return

    isSubmitting.value = true
    submissionError.value = null

    try {
      await axios.post(`/labs/${labId.value}/submit/`, {
        answer: answer.value,
      })

      // 提交成功後更新狀態
      submissionStatus.value = 'pending_reflection'
      answer.value = ''
    } catch (err: any) {
      if (err.response) {
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
    console.log('useSubmit mounted, fetching status...')
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

