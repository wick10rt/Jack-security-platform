<template>
  <div class="auth-container">
    <div class="auth-form-wrapper fade-in-up">
      <!-- EE-0 使用者註冊 -->
      <form v-if="isRegisterMode" @submit.prevent="handleRegister" class="auth-form">
        <h2 class="auth-title">創建你的帳號</h2>
        <p class="auth-subtitle">加入我們和張胖胖一起成長</p>

        <div class="form-group">
          <label for="reg-username">使用者名稱</label>
          <input
            id="reg-username"
            v-model="registerForm.username"
            type="text"
            required
            placeholder="請輸入使用者名稱"
          />
          <div v-if="registerErrors.username" class="error-list">
            <p v-for="error in registerErrors.username" :key="error" class="error-item">
              {{ error }}
            </p>
          </div>
        </div>

        <div class="form-group">
          <label for="reg-password">密碼</label>
          <input
            id="reg-password"
            v-model="registerForm.password"
            type="password"
            required
            placeholder="請輸入密碼"
            @input="checkPasswordMatch"
          />
          <div v-if="registerErrors.password" class="error-list">
            <p v-for="error in registerErrors.password" :key="error" class="error-item">
              {{ error }}
            </p>
          </div>
        </div>

        <div class="form-group">
          <label for="reg-password-confirm">確認密碼</label>
          <input
            id="reg-password-confirm"
            v-model="registerForm.passwordConfirm"
            type="password"
            required
            placeholder="請再次輸入密碼"
            @input="checkPasswordMatch"
          />
          <div v-if="passwordMismatch" class="error-list">
            <p class="error-item">兩次輸入的密碼不一樣</p>
          </div>
        </div>

        <div v-if="registerErrors.non_field_errors" class="error-list">
          <p v-for="error in registerErrors.non_field_errors" :key="error" class="error-item">
            {{ error }}
          </p>
        </div>

        <button type="submit" class="btn submit-btn" :disabled="isRegistering || passwordMismatch">
          <span v-if="isRegistering" class="btn-loading">
            <span class="spinner-small"></span>
            註冊中...
          </span>
          <span v-else>確定</span>
        </button>

        <p class="toggle-link">
          已經有帳號了?
          <a @click="toggleMode" class="link-accent">立即登入</a>
        </p>
      </form>

      <!-- EE-1 使用者登入 -->
      <form v-else @submit.prevent="handleLogin" class="auth-form">
        <h2 class="auth-title">登入你的帳號</h2>
        <p class="auth-subtitle">張胖胖歡迎你</p>

        <div class="form-group">
          <label for="login-username">使用者名稱</label>
          <input
            id="login-username"
            v-model="loginForm.username"
            type="text"
            required
            placeholder="請輸入使用者名稱"
          />
        </div>

        <div class="form-group">
          <label for="login-password">密碼</label>
          <input
            id="login-password"
            v-model="loginForm.password"
            type="password"
            required
            placeholder="請輸入密碼"
          />
        </div>

        <p v-if="loginError" class="error-message fade-in">{{ loginError }}</p>

        <button type="submit" class="btn submit-btn" :disabled="isLoggingIn">
          <span v-if="isLoggingIn" class="btn-loading">
            <span class="spinner-small"></span>
            登入中...
          </span>
          <span v-else>登入</span>
        </button>

        <p class="toggle-link">
          還沒有帳號?
          <a @click="toggleMode" class="link-accent">立即註冊</a>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthForm } from '@/composables/B1_useAuthForm'

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
  passwordMismatch,
  checkPasswordMatch,
} = useAuthForm()
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, var(--bg) 0%, var(--secondary) 100%);
  position: relative;
  overflow: hidden;
}

.auth-container::before {
  content: '☕';
  position: absolute;
  font-size: 20rem;
  opacity: 0.03;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-15deg);
  pointer-events: none;
}

.auth-form-wrapper {
  background: var(--white);
  padding: 3rem;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 450px;
  border-top: 4px solid var(--primary);
  position: relative;
}

.auth-form-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary), var(--accent), var(--primary));
  background-size: 200% 100%;
  animation: shimmer 3s ease-in-out infinite;
}

.auth-form {
  animation: fadeIn 0.6s ease;
}

.auth-title {
  font-size: var(--text-3xl);
  font-weight: 300;
  color: var(--accent);
  margin-bottom: 0.5rem;
  text-align: center;
  letter-spacing: 2px;
}

.auth-subtitle {
  text-align: center;
  color: var(--text);
  opacity: 0.7;
  margin-bottom: 2rem;
  font-size: var(--text-sm);
  letter-spacing: 1px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--accent);
  font-size: var(--text-sm);
  letter-spacing: 0.5px;
  font-weight: 400;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: var(--text-base);
  background: var(--white);
  color: var(--text);
  transition: all 0.3s ease;
}

.form-group input::placeholder {
  color: rgba(58, 58, 58, 0.4);
  font-size: var(--text-sm);
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(139, 115, 85, 0.1);
  transform: translateY(-2px);
}

.error-list {
  margin-top: 0.5rem;
}

.error-item {
  color: #c76b6b;
  font-size: var(--text-sm);
  margin-bottom: 0.25rem;
  padding-left: 1rem;
  position: relative;
  animation: fadeInLeft 0.3s ease;
}

.error-item::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #c76b6b;
}

.error-message {
  color: #c76b6b;
  font-size: var(--text-sm);
  text-align: center;
  padding: 0.75rem;
  background: rgba(199, 107, 107, 0.1);
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  border-left: 3px solid #c76b6b;
}

.submit-btn {
  width: 100%;
  margin-top: 1rem;
  padding: 1rem;
  font-size: var(--text-base);
  font-weight: 400;
  position: relative;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.submit-btn:disabled:hover {
  background: var(--accent);
  color: var(--white);
  box-shadow: none;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.spinner-small {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: var(--white);
  border-radius: 50%;
  animation: rotate 0.8s linear infinite;
}

.toggle-link {
  text-align: center;
  margin-top: 1.5rem;
  font-size: var(--text-sm);
  color: var(--text);
  opacity: 0.8;
}

.link-accent {
  color: var(--accent);
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition);
  text-decoration: none;
  border-bottom: 1px solid transparent;
}

.link-accent:hover {
  border-bottom-color: var(--accent);
  opacity: 1;
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.fade-in-up {
  animation: fadeInUp 0.8s ease;
}

.fade-in {
  animation: fadeIn 0.6s ease;
}

@media (max-width: 480px) {
  .auth-container {
    padding: 1rem;
  }

  .auth-form-wrapper {
    padding: 2rem 1.5rem;
  }

  .auth-title {
    font-size: var(--text-2xl);
  }
}
</style>

