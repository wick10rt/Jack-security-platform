<template>
  <div class="dashboard">
    <h1>我的学习进度</h1>

    <!-- 显示加载状态 -->
    <div v-if="isLoading">
      <p>正在加载进度...</p>
    </div>

    <!-- 显示错误讯息 -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchProgress">重试</button>
    </div>

    <!-- 显示进度列表 -->
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

    <!-- 显示空状态 -->
    <div v-else>
      <p>
        您还没有完成任何实验，快去
        <RouterLink to="/labs">Lab 目录</RouterLink> 开始您的第一个挑战吧！
      </p>
    </div>

    <hr />
    <RouterLink to="/labs">
      <button>进入 Lab 目录</button>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useProgress } from '@/composables/B3_userProgress'

// 调用 Composable，获取所有需要的数据和方法
const { completions, isLoading, error, fetchProgress } = useProgress()
</script>

<style scoped>
.dashboard {
  max-width: 800px;
  margin: 0 auto;
}
.error {
  color: red;
}
.completed {
  color: green;
  font-weight: bold;
}
.pending_reflection {
  color: orange;
}
</style>
