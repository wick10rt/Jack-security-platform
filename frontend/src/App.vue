<template>
  <div id="app-layout">
    <header v-if="authStore.isAuthenticated" class="main-header">
      <div class="logo">
        <RouterLink to="/dashboard">張胖胖資安攻防平台</RouterLink>
      </div>
      <nav class="main-nav">
        <RouterLink to="/labs">Lab 清單</RouterLink>
      </nav>
      <div class="user-actions">
        <span v-if="authStore.username" class="username">使用者: {{ authStore.username }}</span>
        <button @click="handleLogout" class="logout-btn">登出</button>
      </div>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onMounted, watch } from 'vue'
import { useInstanceStore } from '@/stores/instance'

const authStore = useAuthStore()
const router = useRouter()
const instanceStore = useInstanceStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    instanceStore.initializeFromStorage()
  }
})

watch(
  () => authStore.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      instanceStore.initializeFromStorage()
    } else {
      instanceStore.stopPolling()
      instanceStore.activeInstance = null
      localStorage.removeItem('activeInstance')
    }
  },
)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
