import { ref, onUnmounted } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'
import { isAxiosError } from 'axios'

interface ErrorResponseData {
  error?: string
  detail?: string
}

interface LaunchResponse {
  id: string
  instance_url: string
}

interface StatusResponse {
  instance_url: string
  container_id: string
}

export function useControllInstance(labId: Ref<string>) {
  const instanceUrl = ref<string | null>(null)
  const isLaunching = ref(false)
  const launchError = ref<string | null>(null)
  const isTerminating = ref(false)
  const isPolling = ref(false)
  const pollingInterval = ref<number | undefined>(undefined)

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = undefined
      isPolling.value = false
    }
  }
  onUnmounted(stopPolling)

  const pollInstanceStatus = (instanceId: string) => {
    isPolling.value = true
    pollingInterval.value = window.setInterval(async () => {
      try {
        const response = await axios.get<StatusResponse>(`/instances/${instanceId}/status/`)
        const data = response.data

        if (data.instance_url && data.instance_url !== 'creating...') {
          stopPolling() // 停止轮询
          instanceUrl.value = `/instances/${instanceId}/access/`
          isLaunching.value = false
        }
      } catch (error) {
        stopPolling()
        launchError.value = '靶機創建失敗，請重試。'
        isLaunching.value = false
      }
    }, 3000)
  }

  const launchInstance = async () => {
    isLaunching.value = true
    launchError.value = null
    try {
      const response = await axios.post(`/labs/${labId.value}/launch/`)

      if (response.status === 202) {
        const instanceId = response.data.id
        pollInstanceStatus(instanceId)
      } else {
        launchError.value = '靶機創建失敗，請重試。'
        isLaunching.value = false
      }
    } catch (err) {
      if (isAxiosError<ErrorResponseData>(err) && err.response) {
        launchError.value =
          err.response.data.error || err.response.data.detail || `出現錯誤：${err.response.status}`
      } else {
        launchError.value = '出現未知錯誤，請重試。'
        console.error('An unexpected error occurred during launch dispatch:', err)
      }
      isLaunching.value = false
    }
  }

  const accessInstance = async () => {
    if (!instanceUrl.value) return
    try {
      const response = await axios.get(instanceUrl.value)

      const realUrl = response.data.target_url

      if (realUrl) {
        window.open(realUrl, '_blank')
      }
    } catch (error) {
      alert('無法訪問靶機，請稍後再試。')
      console.error('Access instance error:', error)
    }
  }

  const terminateInstance = async () => {
    if (!confirm('確定要關閉當前靶機嗎？')) {
      return
    }
    isTerminating.value = true
    try {
      await axios.post('/instances/terminate/')
      instanceUrl.value = null
      alert('靶機已成功關閉。')
    } catch (err) {
      alert('關閉靶機失敗，請重試。')
      console.error('An unexpected error occurred during termination:', err)
    } finally {
      isTerminating.value = false
    }
  }

  return {
    instanceUrl,
    isLaunching,
    launchError,
    isTerminating,
    isPolling,
    launchInstance,
    terminateInstance,
    accessInstance,
  }
}
