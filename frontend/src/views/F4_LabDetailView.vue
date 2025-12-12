<template>
  <div class="lab-detail-page">
    <!-- 載入狀態 -->
    <div v-if="isLoading" class="loading-state fade-in">
      <div class="spinner"></div>
      <p class="loading-text">正在載入實驗資料...</p>
    </div>

    <!-- 錯誤狀態 -->
    <div v-if="error" class="error-state fade-in">
      <div class="error-icon">⚠️</div>
      <h2>發生錯誤</h2>
      <p>{{ error }}</p>
      <RouterLink to="/labs" class="back-link">
        <span class="back-icon">←</span>
        返回實驗目錄
      </RouterLink>
    </div>

    <!-- 實驗內容 -->
    <article v-if="lab && !isLoading" class="lab-article fade-in-up">
      <!-- 實驗標題區 -->
      <header class="lab-header">
        <h1 class="lab-title">{{ lab.title }}</h1>
        <p class="lab-category">
          <span class="category-label">類別</span>
          <span class="category-value">{{ lab.category }}</span>
        </p>
      </header>

      <!-- 實驗說明 -->
      <section class="description-section card">
        <h2 class="section-title">
          <span class="section-icon">📖</span>
          實驗說明
        </h2>
        <div class="description-content" v-html="lab.description"></div>
      </section>

      <!-- 靶機控制區 -->
      <section class="actions-section card">
        <h2 class="section-title">
          <span class="section-icon">🎯</span>
          靶機管理
        </h2>

        <!-- EE-5 啟動靶機 -->
        <div v-if="instanceStatus === 'no-instance'" class="action-block">
          <button 
            @click="launchInstance" 
            :disabled="isLaunching"
            class="btn btn-primary launch-btn"
          >
            <span v-if="isLaunching" class="btn-loading">
              <span class="spinner-small"></span>
              靶機創建中...
            </span>
            <span v-else>
              <span class="btn-icon">🚀</span>
              啟動靶機
            </span>
          </button>
        </div>

        <!-- 有其他實驗的靶機在運行 -->
        <div v-else-if="instanceStatus === 'other-lab'" class="other-instance-block">
          <div class="warning-box">
            <div class="warning-icon">⚡</div>
            <p class="warning-message">你在其他實驗中有一個靶機正在運行</p>
            <p class="hint-text">關閉後才能在此實驗啟動新靶機</p>
          </div>
          <button 
            @click="terminateInstance" 
            :disabled="isTerminating" 
            class="btn btn-secondary terminate-btn"
          >
            <span v-if="isTerminating" class="btn-loading">
              <span class="spinner-small"></span>
              關閉中...
            </span>
            <span v-else>
              <span class="btn-icon">🛑</span>
              關閉其他靶機
            </span>
          </button>
        </div>

        <!-- 當前實驗靶機運行中 -->
        <div v-else-if="instanceStatus === 'current-lab'">
          <div v-if="instanceUrl === 'creating...'" class="creating-block">
            <div class="spinner-small"></div>
            <p>靶機創建中，請稍候...</p>
          </div>

          <div v-else class="instance-active-block">
            <div class="success-box">
              <div class="success-icon">✓</div>
              <p class="instance-url">靶機已啟動並準備就緒</p>
            </div>
            <div class="instance-actions">
              <button @click="accessInstance" class="btn btn-primary access-btn">
                <span class="btn-icon">→</span>
                進入靶機
              </button>
              <button 
                @click="terminateInstance" 
                :disabled="isTerminating" 
                class="btn btn-secondary terminate-btn"
              >
                <span v-if="isTerminating" class="btn-loading">
                  <span class="spinner-small"></span>
                  關閉中...
                </span>
                <span v-else>
                  <span class="btn-icon">🛑</span>
                  關閉靶機
                </span>
              </button>
            </div>
          </div>
        </div>

        <p v-if="launchError" class="error-message fade-in">{{ launchError }}</p>

        <!-- 分隔線 -->
        <div class="divider"></div>

        <!-- 提交答案 EE-6 -->
        <div
          v-if="submissionStatus !== 'pending_reflection' && submissionStatus !== 'already_completed'"
          class="answer-submission"
        >
          <h3 class="subsection-title">
            <span class="subsection-icon">✍️</span>
            提交答案
          </h3>
          <form @submit.prevent="submitAnswer" class="submission-form">
            <div class="form-group">
              <input
                v-model="answer"
                type="text"
                placeholder="在這邊提交答案"
                :disabled="isAnswerSubmitting"
                required
              />
            </div>
            <button type="submit" :disabled="isAnswerSubmitting" class="btn btn-primary">
              <span v-if="isAnswerSubmitting" class="btn-loading">
                <span class="spinner-small"></span>
                提交中...
              </span>
              <span v-else>提交答案</span>
            </button>
          </form>

          <div v-if="answerError" class="error-message fade-in">
            {{ answerError }}
          </div>
        </div>
      </section>

      <!-- 提交防禦表單 EE-7 -->
      <section
        v-if="submissionStatus === 'pending_reflection' || submissionStatus === 'already_completed'"
        class="reflection-section card"
      >
        <h2 class="section-title">
          <span class="section-icon">🛡️</span>
          你的防禦表單
        </h2>

        <div v-if="isReflectionLoading" class="loading-inline">
          <div class="spinner-small"></div>
          <span>正在獲取表單內容...</span>
        </div>

        <form @submit.prevent="submitReflection" v-else class="reflection-form">
          <div class="form-group">
            <label for="payload">
              <span class="label-icon">💻</span>
              你使用的 Payload
            </label>
            <input
              id="payload"
              v-model="reflectionForm.payload"
              type="text"
              placeholder="填入你使用的 Payload"
              :disabled="isReflectionSubmitting"
              required
            />
          </div>

          <div class="form-group">
            <label for="reflection">
              <span class="label-icon">💭</span>
              防禦省思
            </label>
            <textarea
              id="reflection"
              v-model="reflectionForm.reflection"
              rows="6"
              placeholder="你認為該怎麼樣才能防禦這個漏洞？"
              :disabled="isReflectionSubmitting"
              required
            ></textarea>
          </div>

          <button type="submit" :disabled="isReflectionSubmitting" class="btn btn-primary">
            <span v-if="isReflectionSubmitting" class="btn-loading">
              <span class="spinner-small"></span>
              提交中...
            </span>
            <span v-else>提交防禦表單</span>
          </button>

          <div v-if="reflectionError" class="error-message fade-in">
            {{ reflectionError }}
          </div>
        </form>
      </section>

      <!-- SE-10 實驗完成狀態 -->
      <section
        v-if="submissionSuccess || submissionStatus === 'already_completed'"
        class="completed-section card"
      >
        <div class="celebration-box">
          <div class="celebration-icon">🎉</div>
          <div class="completed-message">恭喜！你已成功完成了這個實驗！</div>
          <div class="completed-hint">想要修改防禦表單內容，只需再填一次表單即可</div>
        </div>

        <!-- 查看他人解法 EE-8 -->
        <div class="solutions-section">
          <button @click="toggleSolutions" class="solutions-toggle-btn btn btn-secondary">
            <span class="btn-icon">{{ showSolutions ? '👁️' : '👀' }}</span>
            {{ showSolutions ? '隱藏他人解法' : '查看他人解法' }}
          </button>

          <div v-if="showSolutions" class="solutions-content fade-in-up">
            <h3 class="solutions-title">
              <span class="solutions-icon">💡</span>
              其他人怎麼做的
            </h3>

            <div v-if="solutionsLoading" class="loading-inline">
              <div class="spinner-small"></div>
              <span>尋找數據中...</span>
            </div>

            <div v-if="solutionsError" class="error-message">{{ solutionsError }}</div>

            <ul v-if="solutions.length > 0" class="solutions-list">
              <li v-for="(solution, index) in solutions" :key="index" class="solution-item">
                <div class="solution-header">
                  <span class="solution-avatar">👤</span>
                  <h4 class="solution-author">匿名使用者 #{{ index + 1 }}</h4>
                </div>
                <div class="solution-content">
                  <div class="solution-payload">
                    <p class="solution-label">
                      <span class="label-icon">💻</span>
                      Payload
                    </p>
                    <pre><code>{{ solution.payload }}</code></pre>
                  </div>
                  <div class="solution-reflection">
                    <p class="solution-label">
                      <span class="label-icon">💭</span>
                      防禦省思
                    </p>
                    <p class="reflection-text">{{ solution.reflection }}</p>
                  </div>
                </div>
              </li>
            </ul>

            <div v-else-if="!solutionsLoading && !solutionsError" class="empty-solutions">
              <div class="empty-icon">📭</div>
              <p>這邊空空如也!!!</p>
            </div>
          </div>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { toRef, watch, type Ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { LabDetail } from '@/composables/B2_useGetDetail'
import { useSubmit } from '@/composables/B5_useSubmit'
import { useReflection } from '@/composables/B3_useReflection'
import { useSolutions } from '@/composables/B2_usesolutions'
import { useControllInstance } from '@/composables/B4_useControlInstance'

// EE-4 顯示實驗詳情
const route = useRoute()
const labId = toRef(route.params, 'id') as Ref<string>
const { lab, isLoading, error } = LabDetail(labId)

// EE-6 提交答案
const {
  answer,
  isSubmitting: isAnswerSubmitting,
  submissionError: answerError,
  submissionStatus,
  submitAnswer,
} = useSubmit(labId)

// EE-7 提交防禦表單
const {
  reflectionForm,
  isSubmitting: isReflectionSubmitting,
  submissionError: reflectionError,
  submissionSuccess,
  isLoading: isReflectionLoading,
  submitReflection,
} = useReflection(labId)

// EE-8 顯示他人解法
const {
  solutions,
  showSolutions,
  isLoading: solutionsLoading,
  error: solutionsError,
  toggleSolutions,
} = useSolutions(labId)

// EE-5 啟動靶機 / EE-11 手動關閉靶機
const {
  instanceUrl,
  instanceStatus,
  hasAnyInstance,
  isCurrentLabActive,
  isLaunching,
  isTerminating,
  launchError,
  launchInstance,
  terminateInstance,
  accessInstance,
} = useControllInstance(labId)
</script>

<style scoped>
.lab-detail-page {
  min-height: 100vh;
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  min-height: 400px;
}

.loading-text {
  margin-top: 1.5rem;
  color: var(--text);
  opacity: 0.7;
  font-size: var(--text-lg);
  letter-spacing: 1px;
}

.error-state {
  background: var(--white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  max-width: 600px;
  margin: 2rem auto;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-state h2 {
  color: #c76b6b;
  margin-bottom: 1rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--accent);
  color: var(--white);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.back-link:hover {
  background: var(--primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.back-icon {
  font-size: 1.25rem;
}

.lab-article {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.lab-header {
  text-align: center;
  padding: 3rem 2rem;
  background: var(--white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  border-top: 4px solid var(--primary);
  position: relative;
  overflow: hidden;
}

.lab-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--primary));
  background-size: 200% 100%;
  animation: shimmer 3s ease-in-out infinite;
}

.lab-badge {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: float 3s ease-in-out infinite;
}

.lab-title {
  font-size: var(--text-4xl);
  font-weight: 300;
  color: var(--accent);
  margin-bottom: 1rem;
  letter-spacing: 2px;
}

.lab-category {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1.5rem;
  background: rgba(139, 115, 85, 0.1);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.category-label {
  font-size: var(--text-sm);
  opacity: 0.7;
}

.category-value {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--accent);
}

.card {
  background: var(--white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  padding: 2rem;
  border-left: 4px solid var(--primary);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: var(--text-2xl);
  font-weight: 400;
  color: var(--accent);
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.section-icon {
  font-size: 1.75rem;
}

.subsection-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-lg);
  font-weight: 400;
  color: var(--accent);
  margin-bottom: 1rem;
}

.subsection-icon {
  font-size: 1.25rem;
}

.description-content {
  line-height: 1.8;
  color: var(--text);
}

.description-content :deep(h1),
.description-content :deep(h2),
.description-content :deep(h3) {
  color: var(--accent);
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.description-content :deep(p) {
  margin-bottom: 1rem;
}

.description-content :deep(code) {
  background: rgba(139, 115, 85, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.description-content :deep(pre) {
  background: rgba(139, 115, 85, 0.05);
  padding: 1rem;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  border: 1px solid var(--border);
}

.action-block,
.other-instance-block,
.creating-block,
.instance-active-block {
  margin-bottom: 1rem;
}

.warning-box,
.success-box {
  padding: 1.5rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  text-align: center;
}

.warning-box {
  background: rgba(212, 167, 115, 0.1);
  border: 1px solid rgba(212, 167, 115, 0.3);
  border-left: 4px solid #d4a773;
}

.success-box {
  background: rgba(139, 115, 85, 0.1);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
}

.warning-icon,
.success-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.warning-message,
.instance-url {
  font-size: var(--text-lg);
  font-weight: 500;
  color: var(--text);
  margin-bottom: 0.5rem;
}

.hint-text {
  font-size: var(--text-sm);
  opacity: 0.7;
  margin: 0;
}

.creating-block {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
  background: rgba(139, 115, 85, 0.05);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border);
}

.instance-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.launch-btn,
.access-btn {
  flex: 1;
  min-width: 200px;
}

.terminate-btn {
  flex: 1;
  min-width: 200px;
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 2rem 0;
}

.submission-form,
.reflection-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.5px;
}

.label-icon {
  font-size: 1.125rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: var(--text-base);
  background: var(--white);
  color: var(--text);
  transition: var(--transition);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(139, 115, 85, 0.1);
}

.form-group textarea {
  resize: vertical;
  line-height: 1.6;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-icon {
  font-size: 1.25rem;
}

.spinner-small {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: var(--white);
  border-radius: 50%;
  animation: rotate 0.8s linear infinite;
}

.loading-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--text);
  opacity: 0.7;
}

.loading-inline .spinner-small {
  border-color: rgba(139, 115, 85, 0.3);
  border-top-color: var(--accent);
}

.celebration-box {
  text-align: center;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(139, 115, 85, 0.05), rgba(212, 181, 160, 0.05));
  border-radius: var(--radius-sm);
  margin-bottom: 2rem;
  border: 1px solid var(--border);
}

.celebration-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: bounce 1s ease infinite;
}

.completed-message {
  font-size: var(--text-xl);
  font-weight: 500;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

.completed-hint {
  font-size: var(--text-sm);
  opacity: 0.7;
}

.solutions-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
}

.solutions-toggle-btn {
  width: 100%;
  margin-bottom: 1.5rem;
}

.solutions-content {
  margin-top: 1.5rem;
}

.solutions-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: var(--text-xl);
  font-weight: 400;
  color: var(--accent);
  margin-bottom: 1.5rem;
}

.solutions-icon {
  font-size: 1.5rem;
}

.solutions-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.solution-item {
  background: rgba(139, 115, 85, 0.03);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1.5rem;
  transition: var(--transition);
}

.solution-item:hover {
  background: rgba(139, 115, 85, 0.05);
  box-shadow: var(--shadow-sm);
}

.solution-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.solution-avatar {
  font-size: 2rem;
}

.solution-author {
  font-size: var(--text-lg);
  font-weight: 400;
  color: var(--accent);
  margin: 0;
}

.solution-content {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.solution-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

.solution-payload pre {
  background: rgba(139, 115, 85, 0.08);
  padding: 1rem;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--border);
}

.solution-payload code {
  font-family: 'Courier New', monospace;
  font-size: var(--text-sm);
  color: var(--text);
}

.reflection-text {
  line-height: 1.8;
  color: var(--text);
  margin: 0;
}

.empty-solutions {
  text-align: center;
  padding: 3rem 2rem;
  background: rgba(139, 115, 85, 0.03);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border);
}

.empty-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.error-message {
  padding: 1rem;
  background: rgba(199, 107, 107, 0.1);
  border: 1px solid rgba(199, 107, 107, 0.3);
  border-left: 4px solid #c76b6b;
  border-radius: var(--radius-sm);
  color: #c76b6b;
  font-size: var(--text-sm);
  margin-top: 1rem;
}

@media (max-width: 768px) {
  .lab-detail-page {
    padding: 1.5rem;
  }

  .lab-title {
    font-size: var(--text-3xl);
  }

  .card {
    padding: 1.5rem;
  }

  .section-title {
    font-size: var(--text-xl);
  }

  .instance-actions {
    flex-direction: column;
  }

  .launch-btn,
  .access-btn,
  .terminate-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .lab-detail-page {
    padding: 1rem;
  }

  .lab-header {
    padding: 2rem 1rem;
  }

  .lab-badge {
    font-size: 3rem;
  }

  .lab-title {
    font-size: var(--text-2xl);
  }

  .card {
    padding: 1.25rem;
  }

  .celebration-icon {
    font-size: 3rem;
  }

  .completed-message {
    font-size: var(--text-lg);
  }

  .solution-item {
    padding: 1rem;
  }
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-15px);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
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

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn 0.6s ease;
}

.fade-in-up {
  animation: fadeInUp 0.8s ease;
}
</style>