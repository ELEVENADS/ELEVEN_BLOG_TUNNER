import apiClient, { type ApiResponse } from '../utils/api'

export interface StyleFeature {
  vocabulary_diversity: number
  average_word_length: number
  unique_words_ratio: number
  average_sentence_length: number
  sentence_complexity: number
  punctuation_density: number
  paragraph_average_length: number
  transition_words_ratio: number
  passive_voice_ratio: number
  first_person_ratio: number
  emoji_usage: number
}

export interface Style {
  name: string
  features: StyleFeature
  vector: number[]
  metadata?: Record<string, any>
}

export interface LearnStyleRequest {
  text: string
  style_name: string
  metadata?: Record<string, any>
}

export const styleApi = {
  learnStyle: async (data: LearnStyleRequest): Promise<ApiResponse<Style>> => {
    const response = await apiClient.post<ApiResponse<Style>>('/styles/learn', data)
    return response.data
  },

  getStyleList: async (): Promise<ApiResponse<{ styles: string[] }>> => {
    const response = await apiClient.get<ApiResponse<{ styles: string[] }>>('/styles/list')
    return response.data
  },

  getStyleDetail: async (styleName: string): Promise<ApiResponse<Style>> => {
    const response = await apiClient.get<ApiResponse<Style>>(`/styles/${styleName}`)
    return response.data
  },

  deleteStyle: async (styleName: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.delete<ApiResponse<null>>(`/styles/${styleName}`)
    return response.data
  },

  getStyleReferences: async (styleName: string, topK: number = 5): Promise<ApiResponse<{ references: { content: string; score: number }[] }>> => {
    const response = await apiClient.get<ApiResponse<{ references: { content: string; score: number }[] }>>(`/styles/${styleName}/references?top_k=${topK}`)
    return response.data
  }
}
