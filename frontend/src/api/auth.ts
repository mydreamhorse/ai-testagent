import apiClient from './index'
import type { LoginCredentials, RegisterData, AuthResponse, User } from '@/types/auth'

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    const response = await apiClient.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response
  },
  
  register: async (userData: RegisterData): Promise<User> => {
    const response = await apiClient.post('/api/v1/auth/register', userData)
    return response
  },
  
  getMe: async (): Promise<User> => {
    const response = await apiClient.get('/api/v1/auth/me')
    return response
  }
}