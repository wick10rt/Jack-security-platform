<template>
  <div class="lab-list-page">
    <div class="page-header fade-in-down">
      <h1 class="page-title">實驗列表</h1>
      <p class="page-subtitle">來跟張胖胖一起學習</p>
    </div>

    <!-- 載入狀態 -->
    <div v-if="isLoading" class="loading-container fade-in">
      <div class="spinner"></div>
      <p class="loading-text">正在載入實驗列表...</p>
    </div>

    <!-- 錯誤狀態 -->
    <div v-if="error" class="error-container fade-in">
      <div class="error-icon">⚠️</div>
      <p class="error-text">{{ error }}</p>
    </div>

    <!-- EE-3 使用者查看實驗清單 -->
    <div v-if="!isLoading && !error" class="lab-content">
      <div v-if="labs.length > 0" class="lab-grid">
        <div
          v-for="(lab, index) in labs"
          :key="lab.id"
          class="lab-card fade-in-up hover-lift"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="lab-card-header">
            <span class="lab-category">{{ lab.category }}</span>
          </div>

          <div class="lab-card-body">
            <h3 class="lab-title">{{ lab.title }}</h3>
          </div>

          <div class="lab-card-footer">
            <RouterLink :to="{ name: 'lab-detail', params: { id: lab.id } }" class="lab-link">
              <button class="btn btn-primary lab-btn">
                <span>進入實驗</span>
                <span class="lab-btn-icon">→</span>
              </button>
            </RouterLink>
          </div>

          <div class="lab-card-shine"></div>
        </div>
      </div>

      <!-- 沒有資料狀態 -->
      <div v-else class="empty-state fade-in-up">
        <p class="empty-text">目前沒有可用的實驗</p>
        <p class="empty-hint">敬請期待張胖胖增加更多精彩內容</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { getLabList } from '@/composables/B2_useGetLabs'

const { labs, isLoading, error } = getLabList()
</script>

<style scoped>
.lab-list-page {
  min-height: 100vh;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}

.page-title {
  font-size: var(--text-4xl);
  font-weight: 300;
  color: var(--accent);
  margin-bottom: 0.5rem;
  letter-spacing: 2px;
}

.page-subtitle {
  font-size: var(--text-base);
  color: var(--text);
  opacity: 0.7;
  letter-spacing: 1px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  min-height: 400px;
}

.loading-text {
  margin-top: 1.5rem;
  color: var(--text);
  opacity: 0.7;
  font-size: var(--text-lg);
  letter-spacing: 1px;
}

.error-container {
  background: rgba(199, 107, 107, 0.1);
  border: 1px solid rgba(199, 107, 107, 0.3);
  border-left: 4px solid #c76b6b;
  border-radius: var(--radius-sm);
  padding: 2rem;
  text-align: center;
  max-width: 600px;
  margin: 2rem auto;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-text {
  color: #c76b6b;
  font-size: var(--text-lg);
  margin: 0;
}

.lab-content {
  animation: fadeIn 0.6s ease;
}

.lab-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
}

.lab-card {
  background: var(--white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: var(--transition);
  border-top: 4px solid var(--primary);
  position: relative;
  display: flex;
  flex-direction: column;
}

.lab-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 181, 160, 0.15), transparent);
  transition: left 0.6s ease;
  pointer-events: none;
}

.lab-card:hover::before {
  left: 100%;
}

.lab-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg);
  border-top-color: var(--accent);
}

.lab-card-header {
  padding: 1.5rem 1.5rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(212, 181, 160, 0.2);
}

.lab-icon {
  font-size: 2.5rem;
  animation: float 3s ease-in-out infinite;
}

.lab-category {
  padding: 0.4rem 1rem;
  background: rgba(139, 115, 85, 0.1);
  color: var(--accent);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  letter-spacing: 1px;
  text-transform: uppercase;
  font-weight: 500;
  border: 1px solid var(--border);
}

.lab-card-body {
  padding: 1.5rem;
  flex: 1;
}

.lab-title {
  font-size: var(--text-xl);
  font-weight: 400;
  color: var(--text);
  letter-spacing: 0.5px;
  line-height: 1.5;
  margin: 0;
  transition: var(--transition);
}

.lab-card:hover .lab-title {
  color: var(--accent);
}

.lab-card-footer {
  padding: 1.5rem;
  background: rgba(250, 248, 245, 0.5);
  border-top: 1px solid rgba(212, 181, 160, 0.2);
}

.lab-link {
  text-decoration: none;
}

.lab-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  font-size: var(--text-base);
}

.lab-btn-icon {
  font-size: 1.5rem;
  transition: var(--transition);
}

.lab-btn:hover .lab-btn-icon {
  transform: translateX(5px);
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  max-width: 600px;
  margin: 2rem auto;
}

.empty-icon {
  font-size: 5rem;
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
}

.empty-text {
  font-size: var(--text-2xl);
  color: var(--accent);
  margin-bottom: 0.5rem;
  letter-spacing: 1px;
}

.empty-hint {
  font-size: var(--text-base);
  color: var(--text);
  opacity: 0.6;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
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

@media (max-width: 1024px) {
  .lab-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .lab-list-page {
    padding: 1.5rem;
  }

  .page-title {
    font-size: var(--text-3xl);
  }

  .lab-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .lab-card-header {
    padding: 1.25rem 1.25rem 0.75rem;
  }

  .lab-icon {
    font-size: 2rem;
  }

  .lab-card-body {
    padding: 1.25rem;
  }

  .lab-title {
    font-size: var(--text-lg);
  }
}

@media (max-width: 480px) {
  .lab-list-page {
    padding: 1rem;
  }

  .page-title {
    font-size: var(--text-2xl);
  }

  .page-subtitle {
    font-size: var(--text-sm);
  }

  .lab-card-header {
    padding: 1rem 1rem 0.5rem;
  }

  .lab-icon {
    font-size: 1.75rem;
  }

  .lab-category {
    font-size: 0.65rem;
    padding: 0.3rem 0.75rem;
  }

  .lab-card-body {
    padding: 1rem;
  }

  .lab-card-footer {
    padding: 1rem;
  }

  .lab-btn {
    padding: 0.75rem 1.25rem;
    font-size: var(--text-sm);
  }

  .empty-icon {
    font-size: 4rem;
  }

  .empty-text {
    font-size: var(--text-xl);
  }
}

@media (hover: hover) {
  .lab-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(
      circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
      rgba(139, 115, 85, 0.05) 0%,
      transparent 50%
    );
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }

  .lab-card:hover::after {
    opacity: 1;
  }
}
</style>
