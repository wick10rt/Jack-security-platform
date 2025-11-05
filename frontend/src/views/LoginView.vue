<template>
  <div class="login-page">
    <!-- 注册表单 -->
    <form @submit.prevent="handleRegister">
      <h2>注册</h2>
      <input v-model="registerForm.username" type="text" placeholder="使用者名称" required />
      <input v-model="registerForm.password" type="password" placeholder="密码" required />
      <button type="submit">注册</button>
      <p v-if="registerError" class="error">{{ registerError }}</p>
    </form>

    <hr />

    <!-- 登入表单 -->
    <form @submit.prevent="handleLogin">
      <h2>登入</h2>
      <input v-model="loginForm.username" type="text" placeholder="使用者名称" required />
      <input v-model="loginForm.password" type="password" placeholder="密码" required />
      <button type="submit">登入</button>
      <p v-if="loginError" class="error">{{ loginError }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();

// 注册逻辑
const registerForm = reactive({ username: '', password: '' });
const registerError = ref<string | null>(null);
const handleRegister = async () => {
  registerError.value = null;
  try {
    await authStore.register(registerForm.username, registerForm.password);
    alert('注册成功，请登入！');
  } catch (error) {
    registerError.value = '注册失败，使用者名称可能已存在。';
  }
};

// 登入逻辑
const loginForm = reactive({ username: '', password: '' });
const loginError = ref<string | null>(null);
const handleLogin = async () => {
  loginError.value = null;
  try {
    const redirectUrl = await authStore.login(loginForm.username, loginForm.password);
    await router.push(redirectUrl);
  } catch (error) {
    loginError.value = '登入失败，请检查帐号或密码。';
  }
};
</script>

<style scoped>
.error {
  color: red;
}
</style>