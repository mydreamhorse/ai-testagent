import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginCredentials } from '@/types/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)
  
  const isAuthenticated = computed(() => !!token.value)
  
  const login = async (credentials: LoginCredentials) => {
    loading.value = true
    try {
      const response = await authApi.login(credentials)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      
      // Get user info
      const userInfo = await authApi.getMe()
      user.value = userInfo
      
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.message }
    } finally {
      loading.value = false
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }
  
  const register = async (userData: any) => {
    loading.value = true
    try {
      const response = await authApi.register(userData)
      return { success: true, data: response }
    } catch (error: any) {
      return { success: false, error: error.message }
    } finally {
      loading.value = false
    }
  }
  
  const fetchUserInfo = async () => {
    if (!token.value) return
    
    try {
      const userInfo = await authApi.getMe()
      user.value = userInfo
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      logout()
    }
  }
  
  // Initialize user info if token exists
  if (token.value) {
    fetchUserInfo()
  }
  
  return {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    logout,
    register,
    fetchUserInfo
  }
})