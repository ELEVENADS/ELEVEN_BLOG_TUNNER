<template>
  <div class="notes-page">
    <t-card title="笔记管理" bordered>
      <template #actions>
        <t-space>
          <t-input
            v-model="searchKeyword"
            placeholder="搜索笔记标题"
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @enter="handleSearch"
          >
            <template #suffix-icon>
              <t-icon name="search" @click="handleSearch" />
            </template>
          </t-input>
          <t-button theme="primary" @click="handleCreateNote">
            <template #icon>
              <t-icon name="add" />
            </template>
            新建笔记
          </t-button>
          <t-button variant="outline" @click="showUploadDialog = true">
            <template #icon>
              <t-icon name="upload" />
            </template>
            导入笔记
          </t-button>
        </t-space>
      </template>

      <t-table :data="notes" :columns="columns" row-key="id" hover :loading="loading">
        <template #word_count="{ row }">
          {{ row.word_count || 0 }} 字
        </template>
        <template #source_type="{ row }">
          <t-tag theme="default" size="small">
            {{ sourceTypeMap[row.source_type] || row.source_type }}
          </t-tag>
        </template>
        <template #created_at="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
        <template #operations="{ row }">
          <t-space>
            <t-link @click="viewNote(row.id)">查看</t-link>
            <t-link @click="editNote(row.id)">编辑</t-link>
            <t-link theme="danger" @click="confirmDelete(row)">删除</t-link>
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

    <t-dialog
      v-model:visible="showDeleteConfirm"
      header="确认删除"
      :confirm-btn="{ theme: 'danger', content: '删除' }"
      :on-confirm="handleDelete"
    >
      <p>确定要删除笔记「{{ deleteTarget?.title }}」吗？此操作不可恢复。</p>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { notesApi, type NoteItem } from '@/api/notes'

const router = useRouter()

const loading = ref(false)
const notes = ref<NoteItem[]>([])
const showUploadDialog = ref(false)
const showDeleteConfirm = ref(false)
const uploadFiles = ref<any[]>([])
const uploading = ref(false)
const searchKeyword = ref('')
const deleteTarget = ref<NoteItem | null>(null)

const sourceTypeMap: Record<string, string> = {
  markdown: 'Markdown',
  txt: '纯文本',
  pdf: 'PDF'
}

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const columns = [
  { colKey: 'title', title: '标题', ellipsis: true },
  { colKey: 'word_count', title: '字数', width: '100' },
  { colKey: 'source_type', title: '来源', width: '120' },
  { colKey: 'created_at', title: '创建时间', width: '180' },
  { colKey: 'operations', title: '操作', width: '200' }
]

onMounted(() => {
  fetchNotes()
})

const fetchNotes = async () => {
  loading.value = true
  try {
    const result = await notesApi.getNotes({
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      keyword: searchKeyword.value || undefined
    })
    if (result) {
      notes.value = result.notes
      pagination.total = result.total
    }
  } catch (error) {
    console.error('获取笔记列表失败:', error)
    MessagePlugin.error('获取笔记列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchNotes()
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
    for (const file of uploadFiles.value) {
      const rawFile = file.raw || file
      await notesApi.uploadNote(rawFile)
    }

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

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const handleCreateNote = () => {
  router.push({ name: 'NoteNew' })
}

const viewNote = (id: string) => {
  router.push({ name: 'NoteEdit', params: { id } })
}

const editNote = (id: string) => {
  router.push({ name: 'NoteEdit', params: { id } })
}

const confirmDelete = (row: NoteItem) => {
  deleteTarget.value = row
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTarget.value) return

  try {
    await notesApi.deleteNote(deleteTarget.value.id)
    MessagePlugin.success('删除成功')
    showDeleteConfirm.value = false
    deleteTarget.value = null
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
