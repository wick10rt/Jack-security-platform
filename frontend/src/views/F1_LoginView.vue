<template>
  <div class="auth-container">
    <div class="auth-form-wrapper">
      <!-- 注册表单 -->
      <form v-if="isRegisterMode" @submit.prevent="handleRegister" key="register">
        <h2>创建您的帐号</h2>

        <div class="form-group">
          <label for="reg-username">使用者名称</label>
          <input id="reg-username" v-model="registerForm.username" type="text" required />
          <div v-if="registerErrors.username" class="error-list">
            <p v-for="error in registerErrors.username" :key="error">{{ error }}</p>
          </div>
        </div>

        <div class="form-group">
          <label for="reg-password">密码</label>
          <input id="reg-password" v-model="registerForm.password" type="password" required />
          <div v-if="registerErrors.password" class="error-list">
            <p v-for="error in registerErrors.password" :key="error">{{ error }}</p>
          </div>
        </div>

        <div v-if="registerErrors.non_field_errors" class="error-list">
          <p v-for="error in registerErrors.non_field_errors" :key="error">{{ error }}</p>
        </div>

        <button type="submit" class="submit-btn">注册</button>

        <p class="toggle-link">已经有帐号了？ <a @click="toggleMode">立即登入</a></p>
      </form>

      <!-- 登入表单 -->
      <form v-else @submit.prevent="handleLogin" key="login">
        <h2>登入您的平台</h2>

        <div class="form-group">
          <label for="login-username">使用者名称</label>
          <input id="login-username" v-model="loginForm.username" type="text" required />
        </div>

        <div class="form-group">
          <label for="login-password">密码</label>
          <input id="login-password" v-model="loginForm.password" type="password" required />
        </div>

        <p v-if="loginError" class="error-message">{{ loginError }}</p>

        <button type="submit" class="submit-btn">登入</button>

        <p class="toggle-link">还没有帐号？ <a @click="toggleMode">立即注册</a></p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const authStore = useAuthStore()
const router = useRouter()

// --- 状态切换逻辑 ---
const isRegisterMode = ref(false) // 预设为登入模式
const toggleMode = () => {
  isRegisterMode.value = !isRegisterMode.value
  // 切换模式时清空所有错误讯息
  loginError.value = null
  Object.keys(registerErrors).forEach(
    (key) => delete registerErrors[key as keyof typeof registerErrors],
  )
}

// --- 注册逻辑 (保持不变) ---
const registerForm = reactive({ username: '', password: '' })
const registerErrors = reactive<{
  username?: string[]
  password?: string[]
  non_field_errors?: string[]
}>({})

const handleRegister = async () => {
  Object.keys(registerErrors).forEach(
    (key) => delete registerErrors[key as keyof typeof registerErrors],
  )
  try {
    await authStore.register(registerForm.username, registerForm.password)
    alert('注册成功，请登入！')
    toggleMode() // 注册成功后自动切换到登入模式
  } catch (error) {
    if (axios.isAxiosError(error) && error.response && error.response.status === 400) {
      const backendErrors = error.response.data
      Object.assign(registerErrors, backendErrors)
    } else {
      registerErrors.non_field_errors = ['发生未知错误，请稍后重试。']
    }
  }
}

// --- 登入逻辑 (已包含管理员跳转) ---
const loginForm = reactive({ username: '', password: '' })
const loginError = ref<string | null>(null)

const handleLogin = async () => {
  loginError.value = null
  try {
    const redirectUrl = await authStore.login(loginForm.username, loginForm.password)

    if (redirectUrl === '/admin/') {
      // 如果是管理后台，这是一个由 Django 渲染的“外部”页面
      // 我们需要让浏览器进行一次完整的页面刷新和跳转
      window.location.href = 'http://127.0.0.1:8000/admin/' // 使用完整的后端 URL
    } else {
      // 如果是前端内部页面 (如 /dashboard)，使用 Vue Router 进行无刷新跳转
      await router.push(redirectUrl)
    }
  } catch (error) {
    loginError.value = '登入失败，请检查帐号或密码。'
  }
}
</script>
