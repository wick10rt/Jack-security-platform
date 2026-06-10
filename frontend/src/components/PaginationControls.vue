<template>
  <div v-if="totalPages > 1" class="pagination">
    <button class="page-btn" :disabled="!hasPrev" @click="$emit('prev')">‹ 上一頁</button>
    <span class="page-indicator">第 {{ currentPage }} / {{ totalPages }} 頁</span>
    <button class="page-btn" :disabled="!hasNext" @click="$emit('next')">下一頁 ›</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  currentPage: number
  totalPages: number
  hasPrev: boolean
  hasNext: boolean
}>()

defineEmits<{
  (e: 'prev'): void
  (e: 'next'): void
}>()
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 2rem;
}

.page-btn {
  padding: 0.6rem 1.25rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--white);
  color: var(--accent);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: var(--transition);
}

.page-btn:hover:not(:disabled) {
  background: var(--accent);
  color: var(--white);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-indicator {
  font-size: var(--text-sm);
  color: var(--text);
  opacity: 0.8;
  letter-spacing: 0.5px;
}
</style>
