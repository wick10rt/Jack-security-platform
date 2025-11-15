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

      <!-- TODO 靶機放這裡 -->
      <section class="actions">
        <button>啟動靶機</button>
        <form>
          <input type="text" placeholder="在這邊提交答案" />
          <button type="submit">提交</button>
        </form>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { toRef, type Ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { LabDetail } from '@/composables/useGetDetail_B2'

const route = useRoute()
const labId = toRef(route.params, 'id') as Ref<string>

const { lab, isLoading, error } = LabDetail(labId)
</script>
