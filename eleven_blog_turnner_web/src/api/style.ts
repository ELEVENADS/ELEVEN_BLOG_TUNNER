import apiClient, { type ApiResponse } from '@/utils/api'

// 统计特征接口
export interface StatisticalFeatures {
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

// 语义特征接口
export interface SemanticFeatures {
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

// 完整特征接口
export interface StyleFeatures {
    statistical?: StatisticalFeatures
    semantic?: SemanticFeatures
}

// 分析模式接口
export interface AnalysisMode {
    use_statistical: boolean
    use_semantic: boolean
    use_embedding: boolean
}

// 风格接口（新版本）
export interface Style {
    name: string
    features?: StyleFeatures
    vector?: number[]
    metadata?: Record<string, any>
    created_at?: string
    updated_at?: string
    sample_count?: number
    total_chars?: number
    analysis_mode?: AnalysisMode
}

export interface StyleListResponse {
    styles: Array<{
        name: string
        created_at?: string
        updated_at?: string
        sample_count?: number
        total_chars?: number
    }>
}

// 学习风格请求参数
export interface LearnStyleRequest {
    text: string
    style_name: string
    metadata?: Record<string, any>
    use_statistical?: boolean
    use_semantic?: boolean
    use_embedding?: boolean
}

// 从笔记提取风格请求参数
export interface ExtractFromNoteRequest {
    note_id: string
    style_name: string
    use_statistical?: boolean
    use_semantic?: boolean
    use_embedding?: boolean
}

// 从文章提取风格请求参数
export interface ExtractFromArticleRequest {
    article_id: string
    style_name: string
    use_statistical?: boolean
    use_semantic?: boolean
    use_embedding?: boolean
}

// 预览风格响应
export interface PreviewStyleResponse {
    features: StyleFeatures
    vector_length: number
    similarity?: number
    analysis_mode?: AnalysisMode
}

export const styleApi = {
    async getStyleList(): Promise<{ data: StyleListResponse }> {
        const response = await apiClient.get('/styles/list')
        return response.data
    },

    async getStyleDetail(name: string): Promise<{ data: Style }> {
        const response = await apiClient.get(`/styles/${name}`)
        return response.data
    },

    async learnStyle(data: LearnStyleRequest): Promise<{ data: Style }> {
        const response = await apiClient.post('/styles/learn', data)
        return response.data?.data
    },

    async learnStyleFromFile(
        file: File,
        styleName: string,
        options?: { use_statistical?: boolean; use_semantic?: boolean; use_embedding?: boolean }
    ): Promise<{ data: { style_name: string } }> {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('style_name', styleName)
        if (options?.use_statistical !== undefined) {
            formData.append('use_statistical', String(options.use_statistical))
        }
        if (options?.use_semantic !== undefined) {
            formData.append('use_semantic', String(options.use_semantic))
        }
        if (options?.use_embedding !== undefined) {
            formData.append('use_embedding', String(options.use_embedding))
        }
        const response = await apiClient.post('/styles/learn-from-file', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        return response.data?.data
    },

    async extractFromNote(data: ExtractFromNoteRequest): Promise<{ data: Style }> {
        const response = await apiClient.post('/styles/extract-from-note', data)
        return response.data?.data
    },

    async extractFromArticle(data: ExtractFromArticleRequest): Promise<{ data: Style }> {
        const response = await apiClient.post('/styles/extract-from-article', data)
        return response.data?.data
    },

    async deleteStyle(name: string): Promise<void> {
        await apiClient.delete(`/styles/${name}`)
    },

    async updateStyle(name: string, data: { style_name?: string; features?: Partial<StyleFeatures> }): Promise<{ data: Style }> {
        const response = await apiClient.put(`/styles/${name}`, data)
        return response.data?.data
    },

    async getStyleReferences(name: string, topK: number = 5): Promise<{ data: { references: Array<{ content: string; char_count: number; added_at: string }> } }> {
        const response = await apiClient.get(`/styles/${name}/references`, {
            params: { top_k: topK }
        })
        return response.data?.data
    },

    async previewStyle(
        file: File,
        styleName?: string,
        options?: { use_statistical?: boolean; use_semantic?: boolean; use_embedding?: boolean }
    ): Promise<{ data: PreviewStyleResponse }> {
        const formData = new FormData()
        formData.append('file', file)
        if (styleName) {
            formData.append('style_name', styleName)
        }
        if (options?.use_statistical !== undefined) {
            formData.append('use_statistical', String(options.use_statistical))
        }
        if (options?.use_semantic !== undefined) {
            formData.append('use_semantic', String(options.use_semantic))
        }
        if (options?.use_embedding !== undefined) {
            formData.append('use_embedding', String(options.use_embedding))
        }
        const response = await apiClient.post('/styles/preview', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        return response.data?.data
    },

    async addStyleSample(name: string, text: string): Promise<{ data: { sample_count: number } }> {
        const response = await apiClient.post(`/styles/${name}/add-sample`, { text })
        return response.data?.data
    },

    async compareStyles(name1: string, name2: string): Promise<{ data: { similarity: number } }> {
        const response = await apiClient.get(`/styles/${name1}/compare/${name2}`)
        return response.data?.data
    }
}
