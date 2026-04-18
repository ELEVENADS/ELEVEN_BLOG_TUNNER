import apiClient, { type ApiResponse } from '../utils/api'

export interface Task {
  task_id: string
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  input_data: string
  user_id: string
  created_at: string
  updated_at: string
  result?: any
  error?: string
}

export interface CreateTaskRequest {
  task_type: string
  input_data: string
  user_id?: string
}

export const taskApi = {
  createTask: async (data: CreateTaskRequest): Promise<ApiResponse<{ task_id: string; status: string }>> => {
    const response = await apiClient.post<any, ApiResponse<{ task_id: string; status: string }>>('/gateway/tasks', data)
    return response
  },

  getTaskList: async (): Promise<ApiResponse<{ tasks: Task[]; total: number }>> => {
    const response = await apiClient.get<any, ApiResponse<{ tasks: Task[]; total: number }>>('/gateway/tasks')
    return response
  },

  getTaskStatus: async (taskId: string): Promise<ApiResponse<Task>> => {
    const response = await apiClient.get<any, ApiResponse<Task>>(`/gateway/tasks/${taskId}`)
    return response
  },

  getTaskResult: async (taskId: string): Promise<ApiResponse<Task>> => {
    const response = await apiClient.get<any, ApiResponse<Task>>(`/gateway/tasks/${taskId}/result`)
    return response
  },

  cancelTask: async (taskId: string): Promise<ApiResponse<{ task_id: string; status: string }>> => {
    const response = await apiClient.delete<any, ApiResponse<{ task_id: string; status: string }>>(`/gateway/tasks/${taskId}`)
    return response
  }
}