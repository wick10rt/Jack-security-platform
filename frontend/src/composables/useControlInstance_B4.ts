// src/composables/useControllInstance_B4.ts
import { ref } from 'vue'
import axios from '@/axios'
import type { Ref } from 'vue'
import daxios from 'axios'


interface ErrorResponseData {
  error?: string;
  detail?: string;
}


export function useControllInstance(labId: Ref<string>) {

  const instanceUrl = ref<string | null>(null)
  const isLaunching = ref(false)
  const launchError = ref<string | null>(null)
  const isTerminating = ref(false)


  const launchInstance = async () => {
    isLaunching.value = true
    launchError.value = null
    try {
      const response = await axios.post(`/labs/${labId.value}/launch/`)

      instanceUrl.value = response.data.proxy_url 
    } catch (err: unknown) {

      if (
        typeof err === 'object' &&
        err !== null &&
        'response' in err &&
        (err as any).response &&
        typeof (err as any).response.data === 'object'
      ) {
        const response = (err as any).response;
        const data: ErrorResponseData = response.data;
        launchError.value = data.error || data.detail || `請求失敗，狀態碼：${response.status}`;
      } else {
        launchError.value = '發生未知錯誤或網路異常，請重試。'
        console.error("An unexpected error occurred during launch:", err);
      }
    } finally {
      isLaunching.value = false
    }
  }

   const accessInstance = async () => {
  if (!instanceUrl.value) return;
  try {

    const response = await axios.get(instanceUrl.value);
    

    const realUrl = response.data.target_url;
    

    if (realUrl) {
      window.open(realUrl, '_blank');
    }
  } catch (error) {

    alert("无法访问靶机，授权失败或发生错误。");
    console.error("Access instance error:", error);
  }
}

  const terminateInstance = async () => {
    if (!confirm('確定要關閉當前靶機嗎？所有未保存的進度將會遺失。')) {
      return;
    }
    isTerminating.value = true
    try {
      await axios.post('/instances/terminate/')
      instanceUrl.value = null 
      alert('靶機已成功關閉。')
    } catch (err) {

      alert('關閉靶機失敗，請重試。')
      console.error("An unexpected error occurred during termination:", err);
    } finally {
      isTerminating.value = false
    }
  }


  return {
    instanceUrl,
    isLaunching,
    launchError,
    isTerminating,
    launchInstance,
    terminateInstance,
    accessInstance,
  }
}