<template>
  <div id="app-layout">
    <header v-if="authStore.isAuthenticated" class="main-header">
      <div class="header-container">
        <div class="logo">
          <span class="logo-text">張胖胖資安攻防平台</span>
        </div>

        <nav class="logo">
          <RouterLink to="/dashboard" class="nav-link"> Dashboard </RouterLink>
        </nav>

        <nav class="main-nav">
          <RouterLink to="/labs" class="nav-link"> Lab 清單 </RouterLink>
        </nav>

        <div class="user-actions">
          <span v-if="authStore.username" class="username">
            <span class="username-label">使用者:</span>
            <span class="username-value">{{ authStore.username }}</span>
          </span>
          <button @click="handleLogout" class="logout-btn">
            <span class="logout-icon">→</span>
            登出
          </button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <RouterView />
    </main>

    <footer v-if="authStore.isAuthenticated" class="main-footer">
      <p>Jack Security Platform - 張胖胖資安攻防平台</p>
    </footer>
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

<style scoped>
#app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, var(--bg) 0%, var(--secondary) 100%);
}

.main-header {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-md);
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid var(--border);
  animation: fadeInDown 0.6s ease;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0.5rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.logo {
  flex-shrink: 0;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--accent);
  font-size: var(--text-lg);
  font-weight: 400;
  letter-spacing: 1px;
  transition: var(--transition);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
}

.logo-link:hover {
  background: rgba(139, 115, 85, 0.05);
  transform: translateY(-2px);
}

.logo-icon {
  font-size: 1.5rem;
  animation: swing 3s ease-in-out infinite;
  transform-origin: top center;
}

.logo-text {
  font-weight: 300;
}

.main-nav {
  flex: 1;
  display: flex;
  gap: 1rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  color: var(--text);
  text-decoration: none;
  font-size: var(--text-base);
  letter-spacing: 0.5px;
  border-radius: var(--radius-sm);
  transition: var(--transition);
  position: relative;
}

.nav-link::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--accent);
  transform: translateX(-50%);
  transition: width 0.3s ease;
}

.nav-link:hover {
  background: rgba(139, 115, 85, 0.08);
  color: var(--accent);
}

.nav-link:hover::before {
  width: 80%;
}

.nav-link.router-link-active {
  background: rgba(139, 115, 85, 0.12);
  color: var(--accent);
  font-weight: 500;
}

.nav-link.router-link-active::before {
  width: 80%;
}

.nav-icon {
  font-size: 1.1rem;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-shrink: 0;
}

.username {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.85rem;
  background: rgba(139, 115, 85, 0.08);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--text);
  border: 1px solid var(--border);
}

.username-label {
  opacity: 0.7;
}

.username-value {
  font-weight: 500;
  color: var(--accent);
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  background: transparent;
  color: var(--accent);
  border: 2px solid var(--accent);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: inherit;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.logout-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: var(--accent);
  transform: translate(-50%, -50%);
  transition:
    width 0.4s ease,
    height 0.4s ease;
  z-index: 0;
}

.logout-btn:hover::before {
  width: 200px;
  height: 200px;
}

.logout-btn:hover {
  color: var(--white);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.logout-btn:active {
  transform: translateY(0);
}

.logout-btn span {
  position: relative;
  z-index: 1;
}

.logout-icon {
  font-size: 1.1rem;
  transition: var(--transition);
}

.logout-btn:hover .logout-icon {
  transform: translateX(3px);
}

.main-content {
  flex: 1;
  animation: fadeIn 0.6s ease;
}

.main-footer {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 2rem;
  text-align: center;
  border-top: 1px solid var(--border);
  margin-top: 4rem;
}

.main-footer p {
  color: var(--text);
  opacity: 0.7;
  font-size: var(--text-sm);
  letter-spacing: 0.5px;
  margin: 0;
}

@media (max-width: 1024px) {
  .header-container {
    padding: 0.5rem 1.5rem;
  }

  .logo-text {
    font-size: var(--text-base);
  }
}

@media (max-width: 768px) {
  .header-container {
    flex-wrap: wrap;
    gap: 1rem;
  }

  .logo {
    order: 1;
  }

  .user-actions {
    order: 2;
    margin-left: auto;
  }

  .main-nav {
    order: 3;
    width: 100%;
    justify-content: flex-start;
    padding-top: 0.5rem;
    border-top: 1px solid var(--border);
  }

  .username {
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.5rem 0.75rem;
  }

  .username-label {
    font-size: var(--text-xs);
  }

  .username-value {
    font-size: var(--text-sm);
  }

  .logout-btn {
    padding: 0.6rem 1.25rem;
    font-size: var(--text-xs);
  }
}

@media (max-width: 480px) {
  .header-container {
    padding: 0.5rem 1rem;
  }

  .logo-link {
    font-size: var(--text-base);
    gap: 0.5rem;
  }

  .logo-icon {
    font-size: 1.5rem;
  }

  .logo-text {
    display: none;
  }

  .username {
    display: none;
  }

  .nav-link {
    padding: 0.6rem 1rem;
    font-size: var(--text-sm);
  }

  .logout-btn {
    padding: 0.5rem 1rem;
  }

  .logout-icon {
    font-size: 1rem;
  }

  .main-footer {
    padding: 1.5rem 1rem;
    margin-top: 2rem;
  }

  .main-footer p {
    font-size: var(--text-xs);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes swing {
  0%,
  100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(5deg);
  }
  75% {
    transform: rotate(-5deg);
  }
}
</style>

