import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
})

axiosInstance.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.accessToken;

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {

    const originalRequest = error.config;
    const authStore = useAuthStore();

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; 
      try {
        console.log('Access token expired. Attempting to refresh...');
        await authStore.refreshTokenAction();
        console.log('Token refreshed successfully.');
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        console.error('Failed to refresh token. Logging out.');
        authStore.logout();
        window.location.href = '/login'; 
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
export default axiosInstance;