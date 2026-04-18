import apiClient, { type ApiResponse } from '@/utils/api'

interface TreeNode {
  id: string
  label: string
  type: 'folder' | 'note' | 'article'
  children?: TreeNode[]
  data?: any
}

interface FolderCreate {
  name: string
  type: 'note' | 'article'
  parent_id?: string
}

interface CategoryUpdate {
  name?: string
  parent_id?: string
  sort_order?: number
}

interface NoteUpdate {
  title?: string
  category_id?: string
}

interface ArticleUpdate {
  title?: string
  category_id?: string
}

interface MoveNodeRequest {
  node_id: string
  node_type: 'category' | 'note' | 'article'
  target_parent_id?: string
  position?: number
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

export const fileTreeApi = {
    /**
     * 获取文件树
     */
    async getFileTree(): Promise<TreeNode[]> {
        const response = await apiClient.get<ApiResponse<{ tree: TreeNode[] }>>('/file-tree')
        return response.data?.data?.tree || []
    },

    /**
     * 创建文件夹
     */
    async createFolder(data: FolderCreate): Promise<{
        id: string
        name: string
        type: string
        parent_id: string | undefined
    }> {
        const response = await apiClient.post<ApiResponse<{
            id: string
            name: string
            type: string
            parent_id: string | undefined
        }>>('/categories', data)
        return response.data?.data
    },

    /**
     * 更新文件夹（重命名/移动）
     */
    async updateCategory(categoryId: string, data: CategoryUpdate): Promise<{
        id: string
        name: string
        parent_id: string | undefined
    }> {
        const response = await apiClient.put<ApiResponse<{
            id: string
            name: string
            parent_id: string | undefined
        }>>(`/categories/${categoryId}`, data)
        return response.data?.data
    },

    /**
     * 删除文件夹
     */
    async deleteFolder(folderId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/categories/${folderId}`)
        return response.data?.data
    },

    /**
     * 获取笔记详情
     */
    async getNoteDetail(noteId: string): Promise<any> {
        const response = await apiClient.get<ApiResponse<any>>(`/notes/${noteId}`)
        return response.data?.data
    },

    /**
     * 创建笔记
     */
    async createNote(data: {
        title: string
        content: string
        category_id?: string
    }): Promise<{
        id: string
        title: string
        category_id?: string
    }> {
        const response = await apiClient.post<ApiResponse<{
            id: string
            title: string
            category_id?: string
        }>>('/notes', data)
        return response.data?.data
    },

    /**
     * 更新笔记（重命名/移动/编辑内容）
     */
    async updateNote(noteId: string, data: {
        title?: string
        content?: string
        category_id?: string
    }): Promise<{
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

    /**
     * 删除笔记
     */
    async deleteNote(noteId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/notes/${noteId}`)
        return response.data?.data
    },

    /**
     * 获取文章详情
     */
    async getArticleDetail(articleId: string): Promise<any> {
        const response = await apiClient.get<ApiResponse<any>>(`/articles/${articleId}`)
        return response.data?.data
    },

    /**
     * 创建文章
     */
    async createArticle(data: {
        title: string
        content?: string
        style_id?: string
        category_id?: string
    }): Promise<{
        id: string
        title: string
        category_id?: string
    }> {
        const response = await apiClient.post<ApiResponse<{
            id: string
            title: string
            category_id?: string
        }>>('/articles', data)
        return response.data?.data
    },

    /**
     * 更新文章（重命名/移动/编辑内容）
     */
    async updateArticle(articleId: string, data: {
        title?: string
        content?: string
        category_id?: string
    }): Promise<{
        id: string
        title: string
        category_id?: string
    }> {
        const response = await apiClient.put<ApiResponse<{
            id: string
            title: string
            category_id?: string
        }>>(`/articles/${articleId}`, data)
        return response.data?.data
    },

    /**
     * 删除文章
     */
    async deleteArticle(articleId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/articles/${articleId}`)
        return response.data?.data
    },

    /**
     * 移动节点（通用接口）
     */
    async moveNode(data: MoveNodeRequest): Promise<{ message: string }> {
        const response = await apiClient.post<ApiResponse<{ message: string }>>('/file-tree/move', data)
        return response.data?.data
    },

    /**
     * 批量导入笔记
     */
    async importNotes(data: NoteImportRequest): Promise<NoteImportResponse> {
        const response = await apiClient.post<ApiResponse<NoteImportResponse>>('/notes/import', data)
        return response.data?.data
    }
}
