import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from '@/axios'
import { isAxiosError } from 'axios'
import { useToast } from 'vue-toastification'

function errMsg(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    return err.response?.data?.error || err.response?.data?.message || fallback
  }
  return fallback
}

function statusCode(err: unknown): number | undefined {
  return isAxiosError(err) ? err.response?.status : undefined
}

interface ActiveInstance {
  id: string
  labId: string
  status: string
  instanceUrl: string
  expiresAt: string
  extensionsUsed: number
  maxExtensions: number
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
          status: data.status || 'creating',
          instanceUrl: data.instance_url || '',
          expiresAt: data.expires_at,
          extensionsUsed: data.extensions_used || 0,
          maxExtensions: data.max_extensions ?? 2,
        }
        saveToLocalStorage()

        pollInstanceStatus(data.id, labId)

        toast.info('靶機創建中，請稍候...')
      } else {
        throw new Error('伺服器錯誤')
      }
    } catch (err) {
      const errorMsg = errMsg(err, '啟動失敗')
      isLoading.value = false
      if (statusCode(err) === 409) {
        // 伺服器上其實已有靶機（另一分頁/裝置）：同步回來，不顯示錯誤（B6）
        error.value = null
        await hydrateFromServer()
        toast.info('你已有一個運行中的靶機，已為你載入。')
      } else {
        error.value = errorMsg
        activeInstance.value = null
        saveToLocalStorage()
        toast.error(errorMsg)
      }
      throw err
    }
  }

  const pollInstanceStatus = (instanceId: string, labId: string) => {
    stopPolling() // 先清掉既有輪詢，避免重複 setInterval 洩漏（B4）
    pollingInterval.value = window.setInterval(async () => {
      try {
        const response = await axios.get(`/instances/${instanceId}/status/`)
        const data = response.data

        if (data.status === 'error') {
          stopPolling()
          activeInstance.value = null
          saveToLocalStorage()
          isLoading.value = false
          error.value = '靶機啟動失敗，請重試'
          toast.error('靶機啟動失敗，請重試')
          return
        }

        if (data.status === 'running') {
          stopPolling()

          activeInstance.value = {
            id: data.id,
            labId: labId,
            status: data.status,
            instanceUrl: data.instance_url,
            expiresAt: data.expires_at,
            extensionsUsed: data.extensions_used || 0,
            maxExtensions: data.max_extensions ?? 2,
          }
          saveToLocalStorage()

          isLoading.value = false
          toast.success('靶機已成功啟動！')
        }
      } catch (err) {
        console.error('Polling error:', err)

        const code = statusCode(err)
        if (code === 404 || code === 403) {
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
    } catch (err) {
      const errorMsg = errMsg(err, '關閉靶機失敗')
      toast.error(errorMsg)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 以 server 為唯一真實來源：進站/登入後用此 hydrate，localStorage 只是樂觀快取
  const hydrateFromServer = async () => {
    try {
      const response = await axios.get('/instances/current/')

      if (response.status === 204 || !response.data || !response.data.id) {
        stopPolling()
        activeInstance.value = null
        saveToLocalStorage()
        return
      }

      const data = response.data
      activeInstance.value = {
        id: data.id,
        labId: data.lab_id,
        status: data.status,
        instanceUrl: data.instance_url,
        expiresAt: data.expires_at,
        extensionsUsed: data.extensions_used ?? 0,
        maxExtensions: data.max_extensions ?? 2,
      }
      saveToLocalStorage()

      if (data.status === 'creating') {
        isLoading.value = true
        pollInstanceStatus(data.id, data.lab_id)
      }
    } catch (error) {
      // 網路錯誤時保留 localStorage 的樂觀值，不做破壞性清除
      console.error('hydrateFromServer 失敗:', error)
    }
  }

  const handleExpired = () => {
    if (!activeInstance.value) return
    stopPolling()
    activeInstance.value = null
    saveToLocalStorage()
    isLoading.value = false
    toast.info('靶機已到期並自動關閉')
  }

  const accessInstance = async () => {
    if (!activeInstance.value) {
      toast.warning('靶機尚未就緒，請稍候。')
      return
    }
    try {
      const response = await axios.get(`/instances/${activeInstance.value.id}/access/`)
      const targetUrl = response.data.target_url
      if (targetUrl) {
        window.open(targetUrl, '_blank')
      } else {
        toast.error('無法獲取靶機 URL')
      }
    } catch {
      toast.error('進入靶機時出現錯誤，請重試')
    }
  }

  const extendInstance = async () => {
    if (!activeInstance.value) return

    try {
      const response = await axios.post('/instances/extend/')
      const data = response.data
      if (activeInstance.value) {
        activeInstance.value.expiresAt = data.expires_at
        activeInstance.value.extensionsUsed = data.extensions_used
        saveToLocalStorage()
      }
      toast.success('已延長靶機時間')
    } catch (err) {
      const errorMsg = errMsg(err, '延長失敗')
      toast.error(errorMsg)
      throw err
    }
  }

  return {
    activeInstance,
    isLoading,
    error,
    launchInstance,
    terminateInstance,
    extendInstance,
    stopPolling,
    hydrateFromServer,
    handleExpired,
    accessInstance,
  }
})
