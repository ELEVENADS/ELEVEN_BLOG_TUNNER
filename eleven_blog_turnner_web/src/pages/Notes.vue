<template>
  <div class="notes-page">
    <t-card title="笔记管理" bordered>
      <template #actions>
        <t-button theme="primary" @click="showUploadDialog = true">
          <template #icon>
            <t-icon name="upload" />
          </template>
          导入笔记
        </t-button>
      </template>

      <t-table :data="notes" :columns="columns" row-key="id" hover :loading="loading">
        <template #word_count="{ row }">
          {{ row.word_count || 0 }} 字
        </template>
        <template #created_at="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
        <template #operations="{ row }">
          <t-space>
            <t-link @click="viewNote(row.id)">查看</t-link>
            <t-link theme="danger" @click="deleteNote(row.id)">删除</t-link>
          </t-space>
        </template>
      </t-table>

      <div class="pagination">
        <t-pagination
          v-model="pagination.page"
          v-model:total="pagination.total"
          :page-size="pagination.pageSize"
          @change="handlePageChange"
        />
      </div>
    </t-card>

    <t-dialog v-model:visible="showUploadDialog" header="导入笔记" :footer="false" width="500px">
      <t-form @submit="handleUpload">
        <t-form-item label="笔记文件">
          <t-upload
            v-model="uploadFiles"
            accept=".md,.txt,.pdf"
            :multiple="true"
            :auto-upload="false"
            @change="handleFileChange"
          />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="uploading">上传</t-button>
            <t-button @click="showUploadDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import apiClient from '@/utils/api'

interface Note {
  id: string
  title: string
  content: string
  word_count: number
  created_at: string
}

const loading = ref(false)
const notes = ref<Note[]>([])
const showUploadDialog = ref(false)
const uploadFiles = ref([])
const uploading = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const columns = [
  { colKey: 'title', title: '标题', width: '250' },
  { colKey: 'word_count', title: '字数', width: '100' },
  { colKey: 'created_at', title: '创建时间', width: '180' },
  { colKey: 'operations', title: '操作', width: '150' }
]

onMounted(() => {
  fetchNotes()
})

const fetchNotes = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/notes', {
      params: {
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    if (response.data?.data?.notes) {
      notes.value = response.data.data.notes
      pagination.total = response.data.data.total
    }
  } catch (error) {
    console.error('Failed to fetch notes:', error)
  } finally {
    loading.value = false
  }
}

const handleFileChange = (files: any) => {
  uploadFiles.value = files
}

const handleUpload = async () => {
  if (uploadFiles.value.length === 0) {
    MessagePlugin.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    uploadFiles.value.forEach((file: any) => {
      formData.append('file', file.raw || file)
    })

    await apiClient.post('/notes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    MessagePlugin.success('上传成功')
    showUploadDialog.value = false
    uploadFiles.value = []
    fetchNotes()
  } catch (error) {
    MessagePlugin.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const viewNote = (id: string) => {
  MessagePlugin.info(`查看笔记 ${id}`)
}

const deleteNote = async (id: string) => {
  try {
    await apiClient.delete(`/notes/${id}`)
    MessagePlugin.success('删除成功')
    fetchNotes()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

const handlePageChange = (pageInfo: { current: number; pageSize: number }) => {
  pagination.page = pageInfo.current
  pagination.pageSize = pageInfo.pageSize
  fetchNotes()
}
</script>

<style scoped>
.notes-page {
  max-width: 1400px;
  margin: 0 auto;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>