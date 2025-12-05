<template>
  <div class="lab-detail-page">
    <div v-if="isLoading" class="loading">正在載入實驗資料...</div>

    <div v-if="error" class="error">
      <h2>發生錯誤</h2>
      <p>{{ error }}</p>
      <RouterLink to="/labs">返回實驗目錄</RouterLink>
    </div>

    <article v-if="lab && !isLoading">
      <header>
        <h1>{{ lab.title }}</h1>
        <p class="category">類別：{{ lab.category }}</p>
      </header>

      <section class="description">
        <h2>實驗說明</h2>
        <div v-html="lab.description"></div>
      </section>

      <!-- 靶機操作 -->
      <section class="actions">
        <div v-if="!instanceUrl">
          <button @click="launchInstance" :disabled="isLaunching">
            {{
              isLaunching ? (isPolling ? '靶機創建中，請稍候...' : '正在派發任務...') : '啟動靶機'
            }}
          </button>
        </div>
        <div v-else class="instance-info">
          <p class="instance-url">靶機已啟動：</p>
          <button @click="accessInstance">進入靶機</button>
          <button @click="terminateInstance" :disabled="isTerminating" class="terminate-btn">
            {{ isTerminating ? '關閉中...' : '關閉靶機' }}
          </button>
        </div>
        <p v-if="launchError" class="error-message">{{ launchError }}</p>
        <hr />

        <!-- 提交答案 EE-6 -->
        <div
          v-if="
            submissionStatus !== 'pending_reflection' && submissionStatus !== 'already_completed'
          "
        >
          <form @submit.prevent="submitAnswer" class="submission-form">
            <input
              v-model="answer"
              type="text"
              placeholder="在這邊提交答案"
              :disabled="isAnswerSubmitting"
              required
            />
            <button type="submit" :disabled="isAnswerSubmitting">
              {{ isAnswerSubmitting ? '提交中...' : '提交' }}
            </button>
          </form>

          <div v-if="answerError" class="error-message">
            {{ answerError }}
          </div>
        </div>
      </section>

      <!-- 提交防禦表單 EE-7 -->
      <section
        v-if="submissionStatus === 'pending_reflection' || submissionStatus === 'already_completed'"
        class="reflection-section"
      >
        <h2>你的防禦表單</h2>
        <div v-if="isReflectionLoading">正在獲取表單內容</div>

        <form @submit.prevent="submitReflection" v-else>
          <div>
            <label for="payload">你使用的 Payload:</label>
            <input
              id="payload"
              v-model="reflectionForm.payload"
              type="text"
              placeholder="填入你使用的 Payload"
              :disabled="isReflectionSubmitting"
              required
            />
          </div>
          <div>
            <label for="reflection">防禦省思:</label>
            <textarea
              id="reflection"
              v-model="reflectionForm.reflection"
              rows="5"
              placeholder="你認為該怎麼樣才能防禦這個漏洞？？"
              :disabled="isReflectionSubmitting"
              required
            ></textarea>
          </div>
          <button type="submit" :disabled="isReflectionSubmitting">
            {{ isReflectionSubmitting ? '提交中...' : '提交' }}
          </button>
          <div v-if="reflectionError" class="error-message">
            {{ reflectionError }}
          </div>
        </form>
      </section>

      <!-- SE-10 實驗完成狀態 -->
      <section
        v-if="submissionSuccess || submissionStatus === 'already_completed'"
        class="completed-section"
      >
        <div class="completed-message">恭喜！你已成功完成了這個實驗！</div>
        <div class="completed-message">想要修改防禦表單內容，只需再填一次表單即可</div>

        <!-- 查看他人解法 EE-8 -->
        <div class="solutions-section">
          <button @click="toggleSolutions" class="solutions-toggle-btn">
            {{ showSolutions ? '隱藏他人解法' : '查看他人解法' }}
          </button>

          <div v-if="showSolutions" class="solutions-content">
            <h3>其他人怎麼做的</h3>
            <div v-if="solutionsLoading">尋找數據中...</div>
            <div v-if="solutionsError" class="error-message">{{ solutionsError }}</div>

            <ul v-if="solutions.length > 0">
              <li v-for="(solution, index) in solutions" :key="index">
                <h4>匿名使用者 #{{ index + 1 }}</h4>
                <p><strong>Payload:</strong></p>
                <pre><code>{{ solution.payload }}</code></pre>
                <p><strong>防禦省思:</strong></p>
                <p>{{ solution.reflection }}</p>
              </li>
            </ul>
            <p v-else-if="!solutionsLoading && !solutionsError">這邊空空如也!!!</p>
          </div>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { toRef, watch, type Ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { LabDetail } from '@/composables/useGetDetail_B2'
import { useSubmit } from '@/composables/useSubmit_B5'
import { useReflection } from '@/composables/useReflection_B3'
import { useSolutions } from '@/composables/usesolutions_B2'
import { useControllInstance } from '@/composables/useControlInstance_B4'

// IE-4 實驗詳情
const route = useRoute()
const labId = toRef(route.params, 'id') as Ref<string>
const { lab, isLoading, error } = LabDetail(labId)

// IE-6 提交答案
const {
  answer,
  isSubmitting: isAnswerSubmitting,
  submissionError: answerError,
  submissionStatus,
  submitAnswer,
} = useSubmit(labId)

// IE-7 防禦表單
const {
  reflectionForm,
  isSubmitting: isReflectionSubmitting,
  submissionError: reflectionError,
  submissionSuccess,
  isLoading: isReflectionLoading,
  submitReflection,
} = useReflection(labId)

// IE-8 解法清單
const {
  solutions,
  showSolutions,
  isLoading: solutionsLoading,
  error: solutionsError,
  toggleSolutions,
} = useSolutions(labId)

// 啟動關閉靶機
const {
  instanceUrl,
  isLaunching,
  launchError,
  isTerminating,
  isPolling,
  launchInstance,
  terminateInstance,
  accessInstance,
} = useControllInstance(labId)
</script>
