<template>
  <div class="not-found-container">
    <div class="not-found-content fade-in-up">
      <div class="error-illustration">
        <div class="error-code">404</div>
      </div>

      <h1 class="error-title">找不到頁面</h1>
      <h2 class="error-subtitle">你訪問的頁面不存在</h2>

      <p class="error-message">
        或許這個頁面被張胖胖吃掉了，
        <br />
        請返回首頁繼續探索吧
      </p>

      <router-link to="/" class="back-home btn btn-primary">
        <span class="back-icon">←</span>
        返回首頁
      </router-link>

      <div class="decoration-dots">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, var(--bg) 0%, var(--secondary) 100%);
  position: relative;
  overflow: hidden;
}

.not-found-container::before {
  content: '🫖';
  position: absolute;
  font-size: 30rem;
  opacity: 0.02;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-15deg);
  pointer-events: none;
  animation: float 6s ease-in-out infinite;
}

.not-found-content {
  text-align: center;
  max-width: 600px;
  background: var(--white);
  padding: 4rem 3rem;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  border-top: 4px solid var(--primary);
  position: relative;
  overflow: hidden;
}

.not-found-content::before {
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

.error-illustration {
  position: relative;
  margin-bottom: 2rem;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.teacup {
  position: absolute;
  font-size: 8rem;
  top: -20px;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 10px 20px rgba(139, 115, 85, 0.2));
}

.error-code {
  font-size: 8rem;
  font-weight: 300;
  color: var(--accent);
  letter-spacing: 0.5rem;
  opacity: 0.15;
  position: absolute;
  animation: pulse 2s ease-in-out infinite;
}

.error-title {
  font-size: var(--text-4xl);
  font-weight: 300;
  color: var(--accent);
  margin-bottom: 0.75rem;
  letter-spacing: 2px;
}

.error-subtitle {
  font-size: var(--text-xl);
  font-weight: 400;
  color: var(--text);
  margin-bottom: 1.5rem;
  opacity: 0.8;
}

.error-message {
  font-size: var(--text-base);
  color: var(--text);
  opacity: 0.7;
  line-height: 1.8;
  margin-bottom: 2.5rem;
  padding: 0 1rem;
}

.back-home {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2.5rem;
  font-size: var(--text-lg);
  text-decoration: none;
  position: relative;
  z-index: 1;
}

.back-icon {
  font-size: 1.5rem;
  transition: var(--transition);
}

.back-home:hover .back-icon {
  transform: translateX(-5px);
}

.decoration-dots {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 2.5rem;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: bounce 1.5s ease-in-out infinite;
}

.dot:nth-child(1) {
  animation-delay: 0s;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.15;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.1;
  }
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
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

.fade-in-up {
  animation: fadeInUp 0.8s ease;
}

@media (max-width: 768px) {
  .not-found-content {
    padding: 3rem 2rem;
  }

  .error-illustration {
    height: 150px;
  }

  .teacup {
    font-size: 6rem;
  }

  .error-code {
    font-size: 6rem;
  }

  .error-title {
    font-size: var(--text-3xl);
  }

  .error-subtitle {
    font-size: var(--text-lg);
  }

  .error-message {
    font-size: var(--text-sm);
  }
}

@media (max-width: 480px) {
  .not-found-container {
    padding: 1rem;
  }

  .not-found-content {
    padding: 2rem 1.5rem;
  }

  .error-illustration {
    height: 120px;
  }

  .teacup {
    font-size: 5rem;
  }

  .error-code {
    font-size: 5rem;
    letter-spacing: 0.25rem;
  }

  .error-title {
    font-size: var(--text-2xl);
  }

  .error-subtitle {
    font-size: var(--text-base);
  }

  .error-message {
    padding: 0;
  }

  .back-home {
    padding: 0.875rem 2rem;
    font-size: var(--text-base);
  }
}

@media (hover: hover) {
  .not-found-content {
    transition: var(--transition);
  }

  .not-found-content:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }

  .teacup {
    transition: var(--transition);
  }

  .not-found-content:hover .teacup {
    transform: translateY(-10px) scale(1.1);
  }
}
</style>
