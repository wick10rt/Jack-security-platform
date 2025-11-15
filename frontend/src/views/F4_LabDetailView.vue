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

        <form @submit.prevent="submitAnswer" class="submission-form">
          <input
            v-model="answer"
            type="text"
            placeholder="在這邊提交答案"
            :disabled="isSubmitting"
            required
          />
          <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '提交' }}
          </button>
        </form>

        <div v-if="submissionError" class="error-message">
          {{ submissionError }}
        </div>
        <div v-if="submissionStatus === 'pending_reflection'" class="success-message">
          回答正確! 請完成防禦省思
        </div>
        <div v-if="submissionStatus === 'already_completed'" class="info-message">
          恭喜你完成了這個實驗
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { toRef, type Ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { LabDetail } from '@/composables/useGetDetail_B2'
import { useSubmit } from '@/composables/useSubmit_B5'

const route = useRoute()
const labId = toRef(route.params, 'id') as Ref<string>
const { lab, isLoading, error } = LabDetail(labId)

const { answer, isSubmitting, submissionError, submissionStatus, submitAnswer } = useSubmit(labId)
</script>
