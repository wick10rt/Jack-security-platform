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

      <section class="actions">
        <button>啟動靶機</button>

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
        <h2
          v-if="submissionStatus === 'pending_reflection' && !submissionSuccess"
          class="success-message"
        >
          答案正確！請完成防禦表單
        </h2>

        <h2 v-else>你的防禦表單</h2>
        <div v-if="isReflectionLoading">正在獲取表單內容</div>

        <form @submit.prevent="submitReflection" v-else>
          <div>
            <label for="payload">你使用的 Payload:</label>
            <input
              id="payload"
              v-model="reflectionForm.payload"
              type="text"
              placeholder="請在這邊填入你的 Payload"
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

      <div
        v-if="submissionSuccess || submissionStatus === 'already_completed'"
        class="completed-message"
      >
        恭喜你！ 你已經完成了這個實驗 想要修改防禦表單內容只需在填一次表單即可
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { toRef, watch, type Ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { LabDetail } from '@/composables/useGetDetail_B2'
import { useSubmit } from '@/composables/useSubmit_B5'
import { useReflection } from '@/composables/useReflection_B3'

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
  fetchMySolution,
  submitReflection,
} = useReflection(labId)

watch(
  submissionStatus,
  (newStatus) => {
    if (newStatus === 'already_completed') {
      fetchMySolution()
    }
  },
  { immediate: true },
)
</script>
