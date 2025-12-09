<template>
  <div class="auth-container">
    <div class="auth-form-wrapper">
      <!-- EE-0 使用者註冊 -->
      <form v-if="isRegisterMode" @submit.prevent="handleRegister">
        <h2>創建你的帳號</h2>
        <div class="form-group">
          <label for="reg-username">使用者名稱</label>
          <input id="reg-username" v-model="registerForm.username" type="text" required />
          <div v-if="registerErrors.username" class="error-list">
            <p v-for="error in registerErrors.username" :key="error">{{ error }}</p>
          </div>
        </div>
        <div class="form-group">
          <label for="reg-password">密碼</label>
          <input id="reg-password" v-model="registerForm.password" type="password" required />
          <div v-if="registerErrors.password" class="error-list">
            <p v-for="error in registerErrors.password" :key="error">{{ error }}</p>
          </div>
        </div>
        <div v-if="registerErrors.non_field_errors" class="error-list">
          <p v-for="error in registerErrors.non_field_errors" :key="error">{{ error }}</p>
        </div>
        <button type="submit" class="submit-btn" :disabled="isRegistering">
          {{ isRegistering ? '註冊中...' : '確定' }}
        </button>
        <p class="toggle-link">已經有帳號了? <a @click="toggleMode">立即登入</a></p>
      </form>

      <!-- EE-1 使用者登入 -->
      <form v-else @submit.prevent="handleLogin">
        <h2>登入你的帳號</h2>
        <div class="form-group">
          <label for="login-username">使用者名稱</label>
          <input id="login-username" v-model="loginForm.username" type="text" required />
        </div>
        <div class="form-group">
          <label for="login-password">密碼</label>
          <input id="login-password" v-model="loginForm.password" type="password" required />
        </div>
        <p v-if="loginError" class="error-message">{{ loginError }}</p>
        <button type="submit" class="submit-btn" :disabled="isLoggingIn">
          {{ isLoggingIn ? '登入中...' : '登入' }}
        </button>
        <p class="toggle-link">還沒有帳號? <a @click="toggleMode">立即註冊</a></p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthForm } from '@/composables/useAuthForm_B1'

const {
  isRegisterMode,
  toggleMode,
  loginForm,
  loginError,
  isLoggingIn,
  handleLogin,
  registerForm,
  registerErrors,
  isRegistering,
  handleRegister,
} = useAuthForm()
</script>
