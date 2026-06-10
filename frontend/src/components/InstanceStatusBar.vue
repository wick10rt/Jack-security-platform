<template>
  <div v-if="instance" class="instance-bar" :class="barClass">
    <div class="bar-inner">
      <span class="bar-status">
        <template v-if="instance.status === 'creating'">
          <span class="dot creating"></span> 靶機建立中…
        </template>
        <template v-else-if="isExpired">
          <span class="dot expired"></span> 靶機已到期
        </template>
        <template v-else>
          <span class="dot running"></span> 靶機運行中
        </template>
      </span>

      <RouterLink v-if="instance.labId" :to="`/labs/${instance.labId}`" class="bar-lab">
        前往實驗
      </RouterLink>

      <span
        v-if="instance.status === 'running' && !isExpired"
        class="bar-timer"
        :class="{ urgent: isUrgent }"
      >
        ⏱ 剩 {{ remainingLabel }}
      </span>

      <span class="bar-actions">
        <button
          v-if="instance.status === 'running' && !isExpired"
          class="bar-btn"
          @click="enter"
        >
          進入
        </button>
        <button
          v-if="instance.status === 'running' && !isExpired"
          class="bar-btn"
          :disabled="extensionsUsed >= maxExtensions"
          @click="extend"
        >
          {{ extensionsUsed >= maxExtensions ? '已達延長上限' : `延長 (${extensionsUsed}/${maxExtensions})` }}
        </button>
        <button class="bar-btn danger" :disabled="instanceStore.isLoading" @click="terminate">
          關閉
        </button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { storeToRefs } from 'pinia'
import Swal from 'sweetalert2'
import { useInstanceStore } from '@/stores/instance'

const instanceStore = useInstanceStore()
const { activeInstance: instance } = storeToRefs(instanceStore)

const maxExtensions = computed(() => instance.value?.maxExtensions ?? 2)

const now = ref(Date.now())
let timer: number | undefined

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

const extensionsUsed = computed(() => instance.value?.extensionsUsed ?? 0)

const remainingMs = computed(() => {
  if (!instance.value?.expiresAt) return 0
  return new Date(instance.value.expiresAt).getTime() - now.value
})

const isExpired = computed(
  () => instance.value?.status === 'running' && remainingMs.value <= 0,
)

const isUrgent = computed(
  () => remainingMs.value > 0 && remainingMs.value <= 5 * 60 * 1000,
)

const remainingLabel = computed(() => {
  const totalSec = Math.floor(Math.max(0, remainingMs.value) / 1000)
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const barClass = computed(() => ({
  'is-creating': instance.value?.status === 'creating',
  'is-expired': isExpired.value,
}))

// 倒數歸零時清掉靶機（server 端隨後也會被 beat 清除）
watch(isExpired, (expired) => {
  if (expired) instanceStore.handleExpired()
})

const enter = () => instanceStore.accessInstance()
const extend = () => instanceStore.extendInstance()

const terminate = async () => {
  const result = await Swal.fire({
    title: '確定要關閉靶機嗎？',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: '確定',
    cancelButtonText: '取消',
    confirmButtonColor: '#7e370eff',
  })
  if (result.isConfirmed) {
    await instanceStore.terminateInstance()
  }
}
</script>

<style scoped>
.instance-bar {
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(139, 115, 85, 0.1);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(10px);
}

.instance-bar.is-expired {
  background: rgba(199, 107, 107, 0.12);
}

.bar-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0.5rem 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: var(--text-sm);
}

.bar-status {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: var(--accent);
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
}

.dot.running {
  background: #6b9e6b;
  box-shadow: 0 0 0 3px rgba(107, 158, 107, 0.2);
}

.dot.creating {
  background: #d4a773;
  animation: pulse 1.2s ease-in-out infinite;
}

.dot.expired {
  background: #c76b6b;
}

.bar-lab {
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}

.bar-lab:hover {
  border-bottom-color: var(--accent);
}

.bar-timer {
  font-variant-numeric: tabular-nums;
  color: var(--text);
  opacity: 0.85;
}

.bar-timer.urgent {
  color: #c76b6b;
  font-weight: 600;
  opacity: 1;
}

.bar-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.bar-btn {
  padding: 0.35rem 0.9rem;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: inherit;
  cursor: pointer;
  transition: var(--transition);
}

.bar-btn:hover:not(:disabled) {
  background: var(--accent);
  color: var(--white);
}

.bar-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.bar-btn.danger {
  border-color: #c76b6b;
  color: #c76b6b;
}

.bar-btn.danger:hover {
  background: #c76b6b;
  color: var(--white);
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

@media (max-width: 480px) {
  .bar-inner {
    padding: 0.5rem 1rem;
    gap: 0.6rem;
  }

  .bar-actions {
    width: 100%;
    margin-left: 0;
    justify-content: flex-end;
  }
}
</style>
