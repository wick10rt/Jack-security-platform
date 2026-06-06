import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from '@/axios'
import { useToast } from 'vue-toastification'

interface ActiveInstance {
  id: string
  labId: string
  instanceUrl: string
  containerUrl: string
  expiresAt: string
}

export const useInstanceStore = defineStore('instance', () => {
  const toast = useToast()

  const loadFromLocalStorage = (): ActiveInstance | null => {
    try {
      const saved = localStorage.getItem('activeInstance')
      return saved ? JSON.parse(saved) : null
    } catch (error) {
      console.error('Failed to load instance from localStorage:', error)
      return null
    }
  }

  const activeInstance = ref<ActiveInstance | null>(loadFromLocalStorage())
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const pollingInterval = ref<number | undefined>(undefined)

  const saveToLocalStorage = () => {
    try {
      if (activeInstance.value) {
        localStorage.setItem('activeInstance', JSON.stringify(activeInstance.value))
      } else {
        localStorage.removeItem('activeInstance')
      }
    } catch (error) {
      console.error('Failed to save instance to localStorage:', error)
    }
  }

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = undefined
    }
  }

  const launchInstance = async (labId: string) => {
    isLoading.value = true
    error.value = null
    stopPolling()

    try {
      const response = await axios.post(`/labs/${labId}/launch/`)

      if (response.status === 202) {
        const data = response.data

        activeInstance.value = {
          id: data.id,
          labId: labId,
          instanceUrl: data.instance_url || 'creating...',
          containerUrl: data.container_id || 'creating...',
          expiresAt: data.expires_at,
        }
        saveToLocalStorage()

        pollInstanceStatus(data.id, labId)

        toast.info('靶機創建中，請稍候...')
      } else {
        throw new Error('伺服器錯誤')
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || '啟動失敗'
      error.value = errorMsg
      isLoading.value = false
      activeInstance.value = null
      saveToLocalStorage()
      toast.error(errorMsg)
      throw err
    }
  }

  const pollInstanceStatus = (instanceId: string, labId: string) => {
    pollingInterval.value = window.setInterval(async () => {
      try {
        const response = await axios.get(`/instances/${instanceId}/status/`)
        const data = response.data

        console.log('Polling status:', data)

        const isReady =
          data.instance_url &&
          data.instance_url !== 'creating...' &&
          data.instance_url !== 'waiting...' &&
          !data.instance_url.includes('creating')

        if (isReady) {
          stopPolling()

          activeInstance.value = {
            id: data.id,
            labId: labId,
            instanceUrl: data.instance_url,
            containerUrl: data.container_id,
            expiresAt: data.expires_at,
          }
          saveToLocalStorage()

          isLoading.value = false
          toast.success('靶機已成功啟動！')
        }
      } catch (err: any) {
        console.error('Polling error:', err)

        if (err.response?.status === 404 || err.response?.status === 403) {
          stopPolling()
          activeInstance.value = null
          saveToLocalStorage()
          isLoading.value = false
          toast.error('你無權訪問這個靶機')
        }
      }
    }, 3000)
  }

  const terminateInstance = async () => {
    if (!activeInstance.value) return

    isLoading.value = true

    try {
      const response = await axios.post('/instances/terminate/')

      if (response.status === 202) {
        stopPolling()
        activeInstance.value = null
        saveToLocalStorage()

        toast.success('關閉靶機成功')
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || '關閉靶機失敗'
      toast.error(errorMsg)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const initializeFromStorage = async () => {
    if (!activeInstance.value) return

    const { id, labId, instanceUrl } = activeInstance.value

    console.log('Initializing from storage:', activeInstance.value)

    const isReady =
      instanceUrl &&
      instanceUrl !== 'creating...' &&
      instanceUrl !== 'waiting...' &&
      !instanceUrl.includes('creating')

    if (isReady) {
      console.log('Instance already running, no need to poll')
      return
    }

    try {
      const response = await axios.get(`/instances/${id}/status/`)
      const data = response.data

      console.log('Initial status check:', data)

      const isNowReady =
        data.instance_url &&
        data.instance_url !== 'creating...' &&
        data.instance_url !== 'waiting...' &&
        !data.instance_url.includes('creating')

      if (isNowReady) {
        activeInstance.value = {
          id: data.id,
          labId: labId,
          instanceUrl: data.instance_url,
          containerUrl: data.container_id,
          expiresAt: data.expires_at,
        }
        saveToLocalStorage()
        toast.success('靶機已就緒！')
      } else {
        isLoading.value = true
        pollInstanceStatus(id, labId)
        toast.info('靶機正在創建中...')
      }
    } catch (error: any) {
      console.error('Failed to initialize from storage:', error)

      if (error.response?.status === 404 || error.response?.status === 403) {
        activeInstance.value = null
        saveToLocalStorage()
        toast.warning('之前的靶機已過期')
      }
    }
  }

  return {
    activeInstance,
    isLoading,
    error,
    launchInstance,
    terminateInstance,
    stopPolling,
    initializeFromStorage,
  }
})
