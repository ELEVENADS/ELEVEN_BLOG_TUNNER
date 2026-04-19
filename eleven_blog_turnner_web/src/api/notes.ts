import apiClient, { type ApiResponse } from '@/utils/api'

interface NoteItem {
  id: string
  title: string
  word_count: number
  source_type: string
  category_id: string | null
  status: string
  is_vectorized: boolean
  created_at: string | null
  updated_at: string | null
}

interface NoteDetail {
  id: string
  title: string
  content: string
  category_id: string | null
  word_count: number
  source_type: string
  created_at: string | null
  updated_at: string | null
}

interface NoteListParams {
  skip?: number
  limit?: number
  category_id?: string
  keyword?: string
}

interface NoteListResponse {
  notes: NoteItem[]
  total: number
  skip: number
  limit: number
}

interface NoteCreateData {
  title: string
  content: string
  category_id?: string
}

interface NoteUpdateData {
  title?: string
  content?: string
  category_id?: string
}

interface NoteUploadResponse {
  id: string
  title: string
  word_count: number
}

interface NoteImportFile {
  path: string
  content: string
  category_id?: string
}

interface NoteImportRequest {
  files: NoteImportFile[]
  auto_create_folders: boolean
}

interface NoteImportResponse {
  success: boolean
  imported_count: number
  notes: Array<{ id: string; title: string }>
}

export const notesApi = {
    async getNotes(params?: NoteListParams): Promise<NoteListResponse> {
        const response = await apiClient.get<ApiResponse<NoteListResponse>>('/notes', {
            params
        })
        return response.data?.data
    },

    async getNoteDetail(noteId: string): Promise<NoteDetail> {
        const response = await apiClient.get<ApiResponse<NoteDetail>>(`/notes/${noteId}`)
        return response.data?.data
    },

    async createNote(data: NoteCreateData): Promise<{ id: string; title: string; category_id?: string }> {
        const response = await apiClient.post<ApiResponse<{
            id: string
            title: string
            category_id?: string
        }>>('/notes', data)
        return response.data?.data
    },

    async updateNote(noteId: string, data: NoteUpdateData): Promise<{
        id: string
        title: string
        category_id?: string
    }> {
        const response = await apiClient.put<ApiResponse<{
            id: string
            title: string
            category_id?: string
        }>>(`/notes/${noteId}`, data)
        return response.data?.data
    },

    async deleteNote(noteId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/notes/${noteId}`)
        return response.data?.data
    },

    async uploadNote(file: File, categoryId?: string): Promise<NoteUploadResponse> {
        const formData = new FormData()
        formData.append('file', file)
        if (categoryId) {
            formData.append('category_id', categoryId)
        }
        const response = await apiClient.post<ApiResponse<NoteUploadResponse>>(
            '/notes/upload',
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } }
        )
        return response.data?.data
    },

    async importNotes(data: NoteImportRequest): Promise<NoteImportResponse> {
        const response = await apiClient.post<ApiResponse<NoteImportResponse>>('/notes/import', data)
        return response.data?.data
    }
}

export type {
    NoteItem,
    NoteDetail,
    NoteListParams,
    NoteListResponse,
    NoteCreateData,
    NoteUpdateData,
    NoteUploadResponse,
    NoteImportFile,
    NoteImportRequest,
    NoteImportResponse
}
