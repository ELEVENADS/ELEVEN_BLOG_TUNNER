import apiClient, { type ApiResponse } from '../utils/api'

export interface ArticleOutline {
  title: string
  description?: string
  word_count?: string
}

export interface Article {
  id: string
  title: string
  content: string
  topic: string
  style_name: string
  status: 'draft' | 'generating' | 'reviewing' | 'approved' | 'rejected' | 'published'
  outline: ArticleOutline[]
  quality_score?: number
  word_count: number
  version: number
  created_at: string
  updated_at: string
}

export interface GenerateArticleRequest {
  topic: string
  style_name: string
  outline?: ArticleOutline[]
  target_length?: number
  metadata?: Record<string, any>
}

export interface ArticleListQuery {
  status?: string
  style_name?: string
  skip?: number
  limit?: number
}

export const articleApi = {
  generateArticle: async (data: GenerateArticleRequest): Promise<ApiResponse<{ task_id: string; status: string }>> => {
    const response = await apiClient.post<any, ApiResponse<{ task_id: string; status: string }>>('/articles/generate', data)
    return response
  },

  getArticleList: async (query?: ArticleListQuery): Promise<ApiResponse<{ articles: Article[]; total: number }>> => {
    const params = new URLSearchParams()
    if (query?.status) params.append('status', query.status)
    if (query?.style_name) params.append('style_name', query.style_name)
    if (query?.skip) params.append('skip', String(query.skip))
    if (query?.limit) params.append('limit', String(query.limit))
    const response = await apiClient.get<any, ApiResponse<{ articles: Article[]; total: number }>>(`/articles?${params.toString()}`)
    return response
  },

  getArticleDetail: async (articleId: string): Promise<ApiResponse<Article>> => {
    const response = await apiClient.get<any, ApiResponse<Article>>(`/articles/${articleId}`)
    return response
  },

  updateArticle: async (articleId: string, data: { content: string; reason?: string }): Promise<ApiResponse<Article>> => {
    const response = await apiClient.put<any, ApiResponse<Article>>(`/articles/${articleId}`, data)
    return response
  },

  deleteArticle: async (articleId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.delete<any, ApiResponse<null>>(`/articles/${articleId}`)
    return response
  },

  submitReview: async (articleId: string): Promise<ApiResponse<{ status: string }>> => {
    const response = await apiClient.post<any, ApiResponse<{ status: string }>>(`/articles/${articleId}/review`)
    return response
  },

  approveArticle: async (articleId: string): Promise<ApiResponse<{ status: string }>> => {
    const response = await apiClient.post<any, ApiResponse<{ status: string }>>(`/articles/${articleId}/approve`)
    return response
  },

  rejectArticle: async (articleId: string, reason?: string): Promise<ApiResponse<{ status: string; reason?: string }>> => {
    const response = await apiClient.post<any, ApiResponse<{ status: string; reason?: string }>>(`/articles/${articleId}/reject`, { reason })
    return response
  }
}