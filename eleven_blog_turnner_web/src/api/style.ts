import apiClient, { type ApiResponse } from '@/utils/api'

export interface Style {
    name: string
    features: {
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
    vector: number[]
    metadata?: Record<string, any>
    created_at?: string
    updated_at?: string
    sample_count?: number
    total_chars?: number
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

export const styleApi = {
    async getStyleList(): Promise<{ data: StyleListResponse }> {
        const response = await apiClient.get('/styles/list')
        return response.data?.data
    },

    async getStyleDetail(name: string): Promise<{ data: Style }> {
        const response = await apiClient.get(`/styles/${name}`)
        return response.data?.data
    },

    async learnStyle(data: {
        text: string
        style_name: string
        metadata?: Record<string, any>
    }): Promise<{ data: Style }> {
        const response = await apiClient.post('/styles/learn', data)
        return response.data?.data
    },

    async learnStyleFromFile(file: File, styleName: string): Promise<{ data: { style_name: string } }> {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('style_name', styleName)
        const response = await apiClient.post('/styles/learn-from-file', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        return response.data?.data
    },

    async extractFromNote(noteId: string, styleName: string): Promise<{ data: Style }> {
        const response = await apiClient.post('/styles/extract-from-note', {
            note_id: noteId,
            style_name: styleName
        })
        return response.data?.data
    },

    async extractFromArticle(articleId: string, styleName: string): Promise<{ data: Style }> {
        const response = await apiClient.post('/styles/extract-from-article', {
            article_id: articleId,
            style_name: styleName
        })
        return response.data?.data
    },

    async deleteStyle(name: string): Promise<void> {
        await apiClient.delete(`/styles/${name}`)
    },

    async getStyleReferences(name: string, topK: number = 5): Promise<{ data: { references: Array<{ content: string; char_count: number; added_at: string }> } }> {
        const response = await apiClient.get(`/styles/${name}/references`, {
            params: { top_k: topK }
        })
        return response.data?.data
    },

    async previewStyle(file: File, styleName?: string): Promise<{ data: { features: any; vector_length: number; similarity?: number } }> {
        const formData = new FormData()
        formData.append('file', file)
        if (styleName) {
            formData.append('style_name', styleName)
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
