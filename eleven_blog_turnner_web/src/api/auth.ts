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
    const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> => {
    const response = await apiClient.post<ApiResponse<RegisterResponse>>('/auth/register', data)
    return response.data
  },

  logout: async (): Promise<ApiResponse<null>> => {
    const response = await apiClient.post<ApiResponse<null>>('/auth/logout')
    return response.data
  },

  getCurrentUser: async (): Promise<ApiResponse<AuthResponse['user']>> => {
    const response = await apiClient.get<ApiResponse<AuthResponse['user']>>('/users/me')
    return response.data
  }
}
