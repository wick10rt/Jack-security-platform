import { computed } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'
import { useToast } from 'vue-toastification'
import Swal from 'sweetalert2'
import { useInstanceStore } from '@/stores/instance'

export function useControllInstance(labId: Ref<string>) {
  const instanceStore = useInstanceStore()
  const toast = useToast()

  const hasAnyInstance = computed(() => !!instanceStore.activeInstance)
  const isCurrentLabActive = computed(() => instanceStore.activeInstance?.labId === labId.value)
  const instanceStatus = computed(() => {
    if (!hasAnyInstance.value) {
      return 'no-instance'
    }
    if (isCurrentLabActive.value) {
      return 'current-lab'
    }
    return 'other-lab'
  })

  const instanceUrl = computed(() => {
    if (isCurrentLabActive.value) {
      return instanceStore.activeInstance?.instanceUrl || null
    }
    return null
  })

  const isLaunching = computed(() => isCurrentLabActive.value && instanceStore.isLoading)

  // EE-5 啟動靶機
  const launchInstance = async () => {
    if (hasAnyInstance.value && !isCurrentLabActive.value) {
      toast.warning('你已經有一個靶機在運行了，請先關閉它。')
      return
    }

    try {
      await instanceStore.launchInstance(labId.value)
    } catch (err: any) {
      console.error('Launch instance error:', err)
    }
  }

  // EE-11 手動關閉靶機
  const terminateInstance = async () => {
    const result = await Swal.fire({
      title: '確定要關閉靶機嗎？',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: '確定',
      cancelButtonText: '取消',
      confirmButtonColor: '#7e370eff',
    })

    if (result.isConfirmed) {
      try {
        await instanceStore.terminateInstance()
      } catch (err: any) {
        console.error('Terminate instance error:', err)
      }
    }
  }

  // 進入靶機
  const accessInstance = async () => {
    if (!instanceStore.activeInstance) {
      toast.warning('靶機尚未就緒，請稍候。')
      return
    }

    const instanceId = instanceStore.activeInstance.id

    try {
      const response = await axios.get(`/instances/${instanceId}/access/`)
      const targetUrl = response.data.target_url

      if (targetUrl) {
        window.open(targetUrl, '_blank')
      } else {
        toast.error('無法獲取靶機 URL')
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('無權訪問此靶機')
      } else if (error.response?.status === 404) {
        toast.error('靶機不存在')
      } else {
        toast.error('進入靶機時出現錯誤，請重試')
      }
      console.error('無法進入靶機:', error)
    }
  }

  return {
    instanceUrl,
    instanceStatus,
    hasAnyInstance,
    isCurrentLabActive,
    isLaunching,
    isTerminating: computed(() => instanceStore.isLoading),
    launchError: computed(() => instanceStore.error),
    launchInstance,
    terminateInstance,
    accessInstance,
  }
}
