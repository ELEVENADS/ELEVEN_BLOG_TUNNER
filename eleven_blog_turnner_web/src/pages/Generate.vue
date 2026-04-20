<template>
  <div class="generate-page">
    <t-card title="生成文章" bordered>
      <t-form ref="formRef" :data="formData" :rules="rules" label-width="120px">
        <!-- 生成模式选择 -->
        <t-form-item label="生成模式" name="mode">
          <t-radio-group v-model="formData.mode">
            <t-radio value="note_integration">笔记整合模式</t-radio>
            <t-radio value="style_topic">风格+主题模式</t-radio>
          </t-radio-group>
          <div class="mode-hint">
            <t-tag v-if="formData.mode === 'note_integration'" theme="primary" variant="light">
              基于笔记内容检索和整合生成文章
            </t-tag>
            <t-tag v-else theme="warning" variant="light">
              基于风格配置和主题生成文章
            </t-tag>
          </div>
        </t-form-item>

        <t-form-item label="文章主题" name="topic">
          <t-textarea
            v-model="formData.topic"
            placeholder="请输入文章主题或关键词"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>

        <!-- 笔记整合模式特有选项 -->
        <template v-if="formData.mode === 'note_integration'">
          <t-form-item label="笔记选择方式" name="note_selection_mode">
            <t-radio-group v-model="noteSelectionMode">
              <t-radio value="auto">自动检索相关笔记</t-radio>
              <t-radio value="manual">手动选择笔记</t-radio>
            </t-radio-group>
          </t-form-item>

          <!-- 自动检索设置 -->
          <template v-if="noteSelectionMode === 'auto'">
            <t-form-item label="检索策略" name="retrieval_strategy">
              <t-select v-model="formData.retrieval_strategy" placeholder="选择检索策略">
                <t-option value="hybrid" label="混合检索（推荐）" />
                <t-option value="vector" label="向量检索（语义相似）" />
                <t-option value="keyword" label="关键词检索" />
              </t-select>
              <div class="strategy-hint">
                <p v-if="formData.retrieval_strategy === 'hybrid'">结合语义相似度和关键词匹配，效果最佳</p>
                <p v-else-if="formData.retrieval_strategy === 'vector'">基于语义相似度，适合概念性主题</p>
                <p v-else>基于关键词精确匹配，适合具体主题</p>
              </div>
            </t-form-item>

            <t-form-item label="检索数量" name="top_k">
              <t-slider v-model="formData.top_k" :min="5" :max="20" :step="1" show-value />
              <div class="slider-hint">检索 {{ formData.top_k }} 个最相关的笔记片段</div>
            </t-form-item>

            <!-- 预览相关笔记 -->
            <t-form-item v-if="relatedNotes.length > 0" label="相关笔记">
              <t-list class="related-notes-list">
                <t-list-item v-for="note in relatedNotes" :key="note.note_id">
                  <template #content>
                    <div class="related-note-item">
                      <t-checkbox v-model="selectedNoteIds" :value="note.note_id">
                        <span class="note-title">{{ note.note_title }}</span>
                        <t-tag size="small" theme="primary" variant="light">
                          相关度: {{ (note.relevance_score * 100).toFixed(1) }}%
                        </t-tag>
                      </t-checkbox>
                    </div>
                  </template>
                </t-list-item>
              </t-list>
              <div class="preview-hint">
                <t-button theme="primary" variant="outline" size="small" @click="searchRelatedNotes">
                  <t-icon name="search" /> 检索相关笔记
                </t-button>
                <span class="hint-text">基于主题自动检索相关笔记</span>
              </div>
            </t-form-item>
          </template>

          <!-- 手动选择笔记 -->
          <template v-if="noteSelectionMode === 'manual'">
            <t-form-item label="选择笔记" name="note_ids">
              <t-transfer
                v-model="formData.note_ids"
                :data="noteList"
                :title="['可选笔记', '已选笔记']"
                :searchable="true"
                :operation="['移除', '添加']"
              />
            </t-form-item>
          </template>
        </template>

        <t-form-item label="选择风格" name="style_name">
          <t-select v-model="formData.style_name" placeholder="请选择写作风格（可选）" filterable clearable>
            <t-option v-for="style in styleList" :key="style.name" :value="style.name" :label="style.name" />
          </t-select>
          <div class="style-hint">
            <t-tag v-if="formData.mode === 'note_integration'" theme="default" variant="light">
              在笔记整合基础上应用风格（可选）
            </t-tag>
            <t-tag v-else theme="warning" variant="light">
              风格为必选项
            </t-tag>
          </div>
        </t-form-item>

        <t-form-item label="目标字数" name="target_length">
          <t-input-number v-model="formData.target_length" :min="100" :max="10000" :step="100" />
        </t-form-item>

        <t-form-item label="文章大纲" name="outline">
          <div class="outline-editor">
            <div v-for="(section, index) in formData.outline" :key="index" class="outline-item">
              <t-input v-model="section.title" placeholder="章节标题" />
              <t-input v-model="section.description" placeholder="章节描述" />
              <t-input-number v-model="section.word_count" :min="50" :max="2000" placeholder="字数" />
              <t-button theme="danger" variant="outline" @click="removeOutline(index)">
                <t-icon name="delete" />
              </t-button>
            </div>
            <t-button theme="primary" variant="outline" @click="addOutline">
              <t-icon name="add" /> 添加章节
            </t-button>
          </div>
        </t-form-item>

        <t-form-item>
          <t-space>
            <t-button theme="primary" type="submit" :loading="generating" @click="handleGenerate">
              开始生成
            </t-button>
            <t-button theme="default" @click="handleReset">重置</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-card>

    <t-card v-if="taskId" title="生成进度" class="progress-card" bordered>
      <t-progress :percentage="progress" :label="false" :color="progressColor" />
      <p class="progress-text">{{ progressText }}</p>
      <div v-if="progress === 100" class="progress-actions">
        <t-button theme="primary" @click="viewArticle">
          查看文章
        </t-button>
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { articleApi, type GenerationMode, type RetrievalStrategy } from '@/api/article'
import { styleApi } from '@/api/style'
import { taskApi } from '@/api/task'
import { notesApi, type NoteItem } from '@/api/notes'

const router = useRouter()

const loading = ref(false)
const generating = ref(false)
const taskId = ref<string | null>(null)
const progress = ref(0)
const progressText = ref('')
const styleList = ref<Array<{ name: string; created_at: string; updated_at: string; sample_count: number; total_chars: number }>>([])
const noteList = ref<Array<{ label: string; value: string; disabled?: boolean }>>([])
const relatedNotes = ref<Array<{ note_id: string; note_title: string; relevance_score: number }>>([])
const selectedNoteIds = ref<string[]>([])
const noteSelectionMode = ref<'auto' | 'manual'>('auto')

const formData = reactive({
  mode: 'note_integration' as GenerationMode,
  topic: '',
  style_name: '',
  note_ids: [] as string[],
  retrieval_strategy: 'hybrid' as RetrievalStrategy,
  top_k: 10,
  target_length: 1000,
  outline: [] as { title: string; description: string; word_count: number }[]
})

const rules = computed(() => ({
  topic: [{ required: true, message: '请输入文章主题', type: 'error' }],
  style_name: formData.mode === 'style_topic'
    ? [{ required: true, message: '请选择写作风格', type: 'error' }]
    : []
}))

const progressColor = computed(() => {
  if (progress.value === 100) return '#00a870'
  if (progress.value > 50) return '#0052d9'
  return '#ffc300'
})

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await Promise.all([
    fetchStyles(),
    fetchNotes()
  ])
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})

const fetchStyles = async () => {
  try {
    const response = await styleApi.getStyleList()
    if (response.data?.styles) {
      styleList.value = response.data.styles
    }
  } catch (error) {
    console.error('Failed to fetch styles:', error)
  }
}

const fetchNotes = async () => {
  try {
    const response = await notesApi.getNotes({ limit: 100 })
    if (response?.notes) {
      noteList.value = response.notes.map((note: NoteItem) => ({
        label: note.title,
        value: note.id,
        disabled: false
      }))
    }
  } catch (error) {
    console.error('Failed to fetch notes:', error)
  }
}

const searchRelatedNotes = async () => {
  if (!formData.topic) {
    MessagePlugin.warning('请先输入文章主题')
    return
  }

  loading.value = true
  try {
    const response = await articleApi.searchNotesForTopic(
      formData.topic,
      formData.retrieval_strategy,
      formData.top_k
    )

    if (response.data?.notes) {
      relatedNotes.value = response.data.notes
      // 默认选中所有相关笔记
      selectedNoteIds.value = response.data.notes.map((n: { note_id: string }) => n.note_id)
      MessagePlugin.success(`找到 ${response.data.total_notes} 篇相关笔记`)
    } else {
      relatedNotes.value = []
      selectedNoteIds.value = []
      MessagePlugin.info('未找到相关笔记')
    }
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '检索失败')
  } finally {
    loading.value = false
  }
}

const addOutline = () => {
  formData.outline.push({ title: '', description: '', word_count: 200 })
}

const removeOutline = (index: number) => {
  formData.outline.splice(index, 1)
}

const handleReset = () => {
  formData.mode = 'note_integration'
  formData.topic = ''
  formData.style_name = ''
  formData.note_ids = []
  formData.retrieval_strategy = 'hybrid'
  formData.top_k = 10
  formData.target_length = 1000
  formData.outline = []
  relatedNotes.value = []
  selectedNoteIds.value = []
  noteSelectionMode.value = 'auto'
}

const handleGenerate = async () => {
  if (!formData.topic) {
    MessagePlugin.warning('请填写文章主题')
    return
  }

  if (formData.mode === 'style_topic' && !formData.style_name) {
    MessagePlugin.warning('风格+主题模式需要选择写作风格')
    return
  }

  // 笔记整合模式下，如果使用自动检索且已选择笔记，则使用选中的笔记
  if (formData.mode === 'note_integration' && noteSelectionMode.value === 'auto' && selectedNoteIds.value.length > 0) {
    formData.note_ids = selectedNoteIds.value
  }

  generating.value = true
  taskId.value = null
  progress.value = 0
  progressText.value = '正在创建任务...'

  try {
    const response = await articleApi.generateArticleV2({
      topic: formData.topic,
      mode: formData.mode,
      style_name: formData.style_name || undefined,
      note_ids: formData.note_ids.length > 0 ? formData.note_ids : undefined,
      retrieval_strategy: formData.retrieval_strategy,
      top_k: formData.top_k,
      outline: formData.outline.length > 0 ? formData.outline : undefined,
      target_length: formData.target_length
    })

    if (response.data?.task_id) {
      taskId.value = response.data.task_id
      progressText.value = '任务已创建，等待处理...'
      startPolling()
    }
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '生成失败')
    generating.value = false
  }
}

const startPolling = () => {
  pollTimer = setInterval(async () => {
    if (!taskId.value) return

    try {
      const response = await taskApi.getTaskStatus(taskId.value)
      const task = response.data

      if (task.status === 'completed') {
        progress.value = 100
        progressText.value = '生成完成！'
        generating.value = false
        if (pollTimer) clearInterval(pollTimer)
      } else if (task.status === 'failed') {
        progressText.value = '生成失败'
        generating.value = false
        if (pollTimer) clearInterval(pollTimer)
      } else {
        progress.value = task.progress || 0
        progressText.value = `处理中... ${progress.value}%`
      }
    } catch (error) {
      console.error('Failed to poll task status:', error)
    }
  }, 2000)
}

const viewArticle = () => {
  if (taskId.value) {
    router.push(`/articles?task_id=${taskId.value}`)
  }
}
</script>

<style scoped>
.generate-page {
  max-width: 1000px;
  margin: 0 auto;
}

.progress-card {
  margin-top: 24px;
}

.progress-text {
  margin-top: 12px;
  color: #666;
}

.progress-actions {
  margin-top: 16px;
}

.outline-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.outline-item {
  display: flex;
  gap: 12px;
  align-items: center;
}

.mode-hint {
  margin-top: 8px;
}

.strategy-hint {
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}

.strategy-hint p {
  margin: 0;
}

.slider-hint {
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}

.style-hint {
  margin-top: 8px;
}

.related-notes-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e7e7e7;
  border-radius: 4px;
  padding: 8px;
}

.related-note-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-title {
  font-weight: 500;
  margin-right: 8px;
}

.preview-hint {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.hint-text {
  color: #666;
  font-size: 12px;
}
</style>
