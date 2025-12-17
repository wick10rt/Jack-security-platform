<template>
  <div class="dashboard">
    <div class="dashboard-header fade-in-down">
      <h1 class="dashboard-title">你的學習進度</h1>
      <p class="dashboard-subtitle">記錄你在張胖胖平台的每一步</p>
    </div>

    <!-- EE-2 使用者查看學習進度 -->
    <div class="dashboard-content">
      <!-- 載入狀態 -->
      <div v-if="isLoading" class="loading-state fade-in">
        <div class="spinner"></div>
        <p class="loading-text">正在獲取數據...</p>
      </div>

      <!-- 錯誤狀態 -->
      <div v-else-if="error" class="error-state fade-in">
        <div class="error-icon">⚠️</div>
        <p class="error-text">{{ error }}</p>
      </div>

      <!-- 有數據狀態 -->
      <div v-else-if="completions.length > 0" class="completions-container">
        <div class="stats-summary fade-in-up">
          <div class="stat-card">
            <div class="stat-number">{{ completions.length }}</div>
            <div class="stat-label">學習紀錄</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">
              {{ completions.filter((c) => c.status === 'completed').length }}
            </div>
            <div class="stat-label">已完成</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">
              {{ completions.filter((c) => c.status !== 'completed').length }}
            </div>
            <div class="stat-label">進行中</div>
          </div>
        </div>

        <ul class="completion-list">
          <li
            v-for="(completion, index) in completions"
            :key="completion.id"
            class="completion-item fade-in-up"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="completion-icon">
              <span v-if="completion.status === 'completed'">✓</span>
              <span v-else>◷</span>
            </div>
            <div class="completion-info">
              <strong class="completion-title">{{ completion.lab_title }}</strong>
              <span class="completion-status" :class="completion.status">
                {{ completion.status === 'completed' ? '已完成' : '待完成省思' }}
              </span>
            </div>
          </li>
        </ul>
      </div>

      <!-- 沒有數據狀態 -->
      <div v-else class="empty-state fade-in-up">
        <p class="empty-text">這裡空空如也!!!</p>
        <p class="empty-hint">開始你跟張胖胖的學習之旅吧</p>
      </div>
    </div>

    <!-- 底部按鈕 -->
    <div class="dashboard-footer fade-in-up delay-2">
      <RouterLink to="/labs" class="nav-link">
        <button class="btn btn-primary">
          <span class="btn-icon">→</span>
          選擇你想進入的 Lab
        </button>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useProgress } from '@/composables/B3_useGetProgress'

const { completions, isLoading, error } = useProgress()
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}

.dashboard-title {
  font-size: var(--text-4xl);
  font-weight: 300;
  color: var(--accent);
  margin-bottom: 0.5rem;
  letter-spacing: 2px;
}

.dashboard-subtitle {
  font-size: var(--text-base);
  color: var(--text);
  opacity: 0.7;
  letter-spacing: 1px;
}

.dashboard-content {
  margin-bottom: 3rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
}

.loading-text {
  margin-top: 1.5rem;
  color: var(--text);
  opacity: 0.7;
  font-size: var(--text-lg);
  letter-spacing: 1px;
}

.error-state {
  background: rgba(199, 107, 107, 0.1);
  border: 1px solid rgba(199, 107, 107, 0.3);
  border-left: 4px solid #c76b6b;
  border-radius: var(--radius-sm);
  padding: 2rem;
  text-align: center;
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

.stats-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--white);
  padding: 2rem;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  text-align: center;
  transition: var(--transition);
  border-top: 3px solid var(--primary);
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
}

.stat-number {
  font-size: var(--text-4xl);
  font-weight: 300;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text);
  opacity: 0.7;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.completion-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.completion-item {
  background: var(--white);
  padding: 1.5rem;
  margin-bottom: 1rem;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: var(--transition);
  border-left: 4px solid transparent;
}

.completion-item:hover {
  transform: translateX(8px);
  box-shadow: var(--shadow-md);
  border-left-color: var(--primary);
}

.completion-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
  transition: var(--transition);
}

.completion-item:hover .completion-icon {
  transform: scale(1.1);
}

.completion-icon span {
  display: block;
}

.completion-item .completion-icon {
  background: var(--secondary);
  color: var(--accent);
}

.completion-item:has(.completed) .completion-icon {
  background: rgba(139, 115, 85, 0.2);
}

.completion-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.completion-title {
  font-size: var(--text-lg);
  color: var(--text);
  font-weight: 400;
  letter-spacing: 0.5px;
}

.completion-status {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.completion-status.completed {
  background: rgba(139, 115, 85, 0.15);
  color: var(--accent);
  border: 1px solid var(--primary);
}

.completion-status:not(.completed) {
  background: rgba(212, 181, 160, 0.15);
  color: #8b7355;
  border: 1px solid var(--border);
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
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

.dashboard-footer {
  text-align: center;
}

.nav-link {
  text-decoration: none;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2.5rem;
  font-size: var(--text-lg);
}

.btn-icon {
  font-size: 1.5rem;
  transition: var(--transition);
}

.btn-primary:hover .btn-icon {
  transform: translateX(5px);
}

@media (max-width: 768px) {
  .dashboard {
    padding: 1.5rem;
  }

  .dashboard-title {
    font-size: var(--text-3xl);
  }

  .stats-summary {
    grid-template-columns: 1fr;
  }

  .completion-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .completion-status {
    align-self: flex-start;
  }
}

@media (max-width: 480px) {
  .dashboard {
    padding: 1rem;
  }

  .dashboard-title {
    font-size: var(--text-2xl);
  }

  .stat-number {
    font-size: var(--text-3xl);
  }

  .completion-item {
    padding: 1rem;
    gap: 1rem;
  }

  .completion-icon {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>

