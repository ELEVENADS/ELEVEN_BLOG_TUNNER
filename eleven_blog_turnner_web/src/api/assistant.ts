import apiClient from '@/utils/api'

// 辅助任务类型
export type AssistantTaskType =
  | 'continue'      // 续写
  | 'extract_style' // 提取风格
  | 'rewrite'       // 改写
  | 'polish'        // 润色
  | 'suggest'       // 生成建议
  | 'expand'        // 扩写
  | 'summarize'     // 总结

// 辅助任务请求
export interface AssistantTaskRequest {
  task_type: AssistantTaskType
  selected_text: string
  context?: string
  style?: string
  style_hint?: string
  length?: number
  target_length?: number
}

// 辅助任务响应
export interface AssistantTaskResponse {
  result: string
  task_type: AssistantTaskType
  metadata?: {
    style_analysis?: {
      language_style?: string
      tone?: string
      vocabulary_level?: string
      sentence_rhythm?: string
      rhetoric_devices?: string[]
      emotional_tendency?: string
      perspective?: string
      logic_structure?: string
      unique_habits?: string[]
      target_audience?: string
      domain_characteristics?: string
      writing_quirks?: string
    }
    suggestions?: string[]
    word_count?: number
  }
}

// 从编辑器提取风格请求
export interface ExtractStyleFromEditorRequest {
  content: string
  selection_start?: number
  selection_end?: number
  use_llm?: boolean
}

// 从编辑器提取风格响应
export interface ExtractStyleFromEditorResponse {
  style_name: string
  features: {
    statistical?: {
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
    semantic?: {
      language_style: string
      tone: string
      vocabulary_level: string
      sentence_rhythm: string
      rhetoric_devices: string[]
      emotional_tendency: string
      perspective: string
      logic_structure: string
      unique_habits: string[]
      target_audience: string
      domain_characteristics: string
      writing_quirks: string
    }
  }
  analysis_mode: {
    use_statistical: boolean
    use_semantic: boolean
    use_embedding: boolean
  }
}

export const assistantApi = {
  /**
   * 执行辅助任务
   */
  async executeTask(data: AssistantTaskRequest): Promise<AssistantTaskResponse> {
    const response = await apiClient.post('/assistant/execute', data)
    // API 返回 { code, data: AssistantTaskResponse, message }
    return response.data?.data
  },

  /**
   * 从编辑器内容提取风格
   */
  async extractStyleFromEditor(data: ExtractStyleFromEditorRequest): Promise<{ data: ExtractStyleFromEditorResponse }> {
    const response = await apiClient.post('/assistant/extract-style', data)
    return response.data?.data
  },

  /**
   * 智能续写
   */
  async continueWriting(
    selectedText: string,
    context?: string,
    options?: { style_hint?: string; length?: number }
  ): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'continue',
      selected_text: selectedText,
      context,
      style_hint: options?.style_hint,
      length: options?.length || 200
    })
  },

  /**
   * 提取选中内容的风格
   */
  async extractStyle(selectedText: string): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'extract_style',
      selected_text: selectedText
    })
  },

  /**
   * 改写内容
   */
  async rewrite(selectedText: string, style: string): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'rewrite',
      selected_text: selectedText,
      style
    })
  },

  /**
   * 润色内容
   */
  async polish(selectedText: string): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'polish',
      selected_text: selectedText
    })
  },

  /**
   * 生成写作建议
   */
  async generateSuggestions(selectedText: string, context?: string): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'suggest',
      selected_text: selectedText,
      context
    })
  },

  /**
   * 扩写内容
   */
  async expand(selectedText: string, targetLength: number = 300): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'expand',
      selected_text: selectedText,
      target_length: targetLength
    })
  },

  /**
   * 总结内容
   */
  async summarize(selectedText: string): Promise<AssistantTaskResponse> {
    return this.executeTask({
      task_type: 'summarize',
      selected_text: selectedText
    })
  }
}
