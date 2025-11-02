import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/axios'
import { jwtDecode } from 'jwt-decode'

interface Userinfo {
  username: string
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAdmin = ref<Boolean>(localStorage.getItem('isAdmin') === 'true')
})
