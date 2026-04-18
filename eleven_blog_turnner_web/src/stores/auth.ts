import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, type LoginRequest, type RegisterRequest, type AuthResponse } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthResponse['user'] | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isAuthenticated = ref<boolean>(!!token.value)

  const setAuth = (authToken: string, authUser: AuthResponse['user']) => {
    token.value = authToken
    user.value = authUser
    isAuthenticated.value = true
    localStorage.setItem('token', authToken)
  }

  const clearAuth = () => {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
  }

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authApi.login(credentials)
      if (response.code === '200') {
        setAuth(response.data.access_token, response.data.user)
        return { success: true }
      }
      return { success: false, message: response.message }
    } catch (error: any) {
      return { success: false, message: error.response?.data?.message || '登录失败' }
    }
  }

  const register = async (data: RegisterRequest) => {
    try {
      const response = await authApi.register(data)
      if (response.code === '200') {
        return { success: true }
      }
      return { success: false, message: response.message }
    } catch (error: any) {
      return { success: false, message: error.response?.data?.message || '注册失败' }
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      // 忽略错误
    }
    clearAuth()
  }

  const fetchCurrentUser = async () => {
    if (!token.value) return
    try {
      const response = await authApi.getCurrentUser()
      if (response.data) {
        user.value = response.data
      }
    } catch (error) {
      clearAuth()
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout,
    fetchCurrentUser,
    clearAuth
  }
})
