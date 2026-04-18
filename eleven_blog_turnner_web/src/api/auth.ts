import apiClient, { type ApiResponse } from '../utils/api'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    username: string
    email: string
    avatar_url?: string
    is_active: boolean
    is_superuser: boolean
  }
}

export interface RegisterResponse {
  id: string
  username: string
  email: string
  created_at: string
}

export interface AuthResponse {
  token: string
  user: {
    id: string
    username: string
    email: string
  }
}

export const authApi = {
  login: async (data: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
    const response = await apiClient.post<any, ApiResponse<LoginResponse>>('/auth/login', data)
    return response
  },

  register: async (data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> => {
    const response = await apiClient.post<any, ApiResponse<RegisterResponse>>('/auth/register', data)
    return response
  },

  logout: async (): Promise<ApiResponse<null>> => {
    const response = await apiClient.post<any, ApiResponse<null>>('/auth/logout')
    return response
  },

  getCurrentUser: async (): Promise<ApiResponse<AuthResponse['user']>> => {
    const response = await apiClient.get<any, ApiResponse<AuthResponse['user']>>('/users/me')
    return response
  }
}