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

// 生成模式
export type GenerationMode = 'note_integration' | 'style_topic'

// 检索策略
export type RetrievalStrategy = 'vector' | 'keyword' | 'hybrid'

// V2 文章生成请求 - 支持笔记整合模式
export interface GenerateArticleRequestV2 {
  topic: string
  mode?: GenerationMode           // 默认: note_integration
  style_name?: string             // 可选的风格名称
  note_ids?: string[]             // 指定笔记ID列表
  retrieval_strategy?: RetrievalStrategy  // 默认: hybrid
  top_k?: number                  // 默认: 10
  outline?: ArticleOutline[]
  target_length?: number          // 默认: 1000
  metadata?: Record<string, any>
}

// 笔记搜索结果
export interface NoteSearchResult {
  topic: string
  total_notes: number
  total_chunks: number
  strategy: string
  notes: Array<{
    note_id: string
    note_title: string
    relevance_score: number
  }>
  chunks: Array<{
    content: string
    note_title: string
    score: number
  }>
}

export interface ArticleListQuery {
  status?: string
  style_name?: string
  skip?: number
  limit?: number
}

export const articleApi = {
  generateArticle: async (data: GenerateArticleRequest): Promise<ApiResponse<{ task_id: string; status: string }>> => {
    const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/articles/generate', data)
    return response.data
  },

  // V2 文章生成 - 支持笔记整合模式
  generateArticleV2: async (data: GenerateArticleRequestV2): Promise<ApiResponse<{ task_id: string; status: string }>> => {
    const response = await apiClient.post<ApiResponse<{ task_id: string; status: string }>>('/articles/generate-v2', data)
    return response.data
  },

  // 根据主题搜索相关笔记
  searchNotesForTopic: async (
    topic: string,
    strategy: RetrievalStrategy = 'hybrid',
    top_k: number = 10
  ): Promise<ApiResponse<NoteSearchResult>> => {
    const params = new URLSearchParams()
    params.append('topic', topic)
    params.append('strategy', strategy)
    params.append('top_k', top_k.toString())
    
    const response = await apiClient.get<ApiResponse<NoteSearchResult>>(
      `/articles/search-notes-for-topic?${params.toString()}`
    )
    return response.data
  },

  getArticleList: async (query?: ArticleListQuery): Promise<ApiResponse<{ articles: Article[]; total: number }>> => {
    const params = new URLSearchParams()
    if (query?.status) params.append('status', query.status)
    if (query?.style_name) params.append('style_name', query.style_name)
    if (query?.skip) params.append('skip', String(query.skip))
    if (query?.limit) params.append('limit', String(query.limit))
    const response = await apiClient.get<ApiResponse<{ articles: Article[]; total: number }>>(`/articles?${params.toString()}`)
    return response.data
  },

  getArticleDetail: async (articleId: string): Promise<ApiResponse<Article>> => {
    const response = await apiClient.get<ApiResponse<Article>>(`/articles/${articleId}`)
    return response.data
  },

  updateArticle: async (articleId: string, data: { content: string; reason?: string }): Promise<ApiResponse<Article>> => {
    const response = await apiClient.put<ApiResponse<Article>>(`/articles/${articleId}`, data)
    return response.data
  },

  deleteArticle: async (articleId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.delete<ApiResponse<null>>(`/articles/${articleId}`)
    return response.data
  },

  submitReview: async (articleId: string): Promise<ApiResponse<{ status: string }>> => {
    const response = await apiClient.post<ApiResponse<{ status: string }>>(`/articles/${articleId}/review`)
    return response.data
  },

  approveArticle: async (articleId: string): Promise<ApiResponse<{ status: string }>> => {
    const response = await apiClient.post<ApiResponse<{ status: string }>>(`/articles/${articleId}/approve`)
    return response.data
  },

  rejectArticle: async (articleId: string, reason?: string): Promise<ApiResponse<{ status: string; reason?: string }>> => {
    const response = await apiClient.post<ApiResponse<{ status: string; reason?: string }>>(`/articles/${articleId}/reject`, { reason })
    return response.data
  },

  getArticleVersions: async (articleId: string): Promise<ApiResponse<{ versions: Array<{ version: number; content: string; created_at: number; reason?: string }> }>> => {
    const response = await apiClient.get<ApiResponse<{ versions: Array<{ version: number; content: string; created_at: number; reason?: string }> }>>(`/articles/${articleId}/versions`)
    return response.data
  },

  restoreVersion: async (articleId: string, version: number): Promise<ApiResponse<{ current_version: number }>> => {
    const response = await apiClient.post<ApiResponse<{ current_version: number }>>(`/articles/${articleId}/versions/${version}/restore`)
    return response.data
  },

  polishArticle: async (articleId: string, styleName?: string): Promise<ApiResponse<Article>> => {
    const response = await apiClient.post<ApiResponse<Article>>(`/articles/${articleId}/polish`, { style_name: styleName })
    return response.data
  }
}
