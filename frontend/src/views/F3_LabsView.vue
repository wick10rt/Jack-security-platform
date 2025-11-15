<template>
  <div class="lab-list-page">
    <h1>實驗列表</h1>

    <div v-if="isLoading" class="loading">正在載入實驗列表...</div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="!isLoading && !error" class="lab-grid">
      <div v-for="lab in labs" :key="lab.id" class="lab-card">
        <h3>{{ lab.title }}</h3>
        <p class="category">{{ lab.category }}</p>
        <RouterLink :to="{ name: 'lab-detail', params: { id: lab.id } }">
          <button>進入實驗</button>
        </RouterLink>
      </div>
      <p v-if="labs.length === 0">目前沒有可用的實驗</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { getLabList } from '@/composables/useGetLabs_B2'

const { labs, isLoading, error } = getLabList()
</script>
