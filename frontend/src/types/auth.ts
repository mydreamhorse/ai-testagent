export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}