<template>
  <div class="dashboard">
    <h1>你的學習進度</h1>

    <div v-if="isLoading">
      <p>正在獲取數據...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="completions.length > 0">
      <ul>
        <li v-for="completion in completions" :key="completion.id">
          <strong>{{ completion.lab }}</strong> -
          <span :class="completion.status">
            {{ completion.status === 'completed' ? '已完成' : '待完成省思' }}
          </span>
        </li>
      </ul>
    </div>

    <div v-else>
      <p>這裡空空如也!!!</p>
    </div>

    <RouterLink to="/labs">
      <button>進入 Lab 目錄</button>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useProgress } from '@/composables/useGetProgress_B3'

const { completions, isLoading, error } = useProgress()
</script>
