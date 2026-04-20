<template>
  <div class="generate-page">
    <t-card title="生成文章" bordered>
      <t-form ref="formRef" :data="formData" :rules="rules" label-width="120px">
        <t-form-item label="文章主题" name="topic">
          <t-textarea
            v-model="formData.topic"
            placeholder="请输入文章主题或关键词"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>

        <t-form-item label="选择风格" name="style_name">
          <t-select v-model="formData.style_name" placeholder="请选择写作风格" filterable>
            <t-option v-for="style in styleList" :key="style.name" :value="style.name" :label="style.name" />
          </t-select>
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
      <t-progress :percentage="progress" :label="false" :color="'#0052d9'" />
      <p class="progress-text">{{ progressText }}</p>
      <t-button v-if="progress === 100" theme="primary" @click="viewArticle">
        查看文章
      </t-button>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { articleApi } from '@/api/article'
import { styleApi } from '@/api/style'
import { taskApi } from '@/api/task'

const router = useRouter()

const formRef = ref()
const generating = ref(false)
const taskId = ref<string | null>(null)
const progress = ref(0)
const progressText = ref('')
const styleList = ref<Array<{ name: string; created_at: string; updated_at: string; sample_count: number; total_chars: number }>>([])

const formData = reactive({
  topic: '',
  style_name: '',
  target_length: 1000,
  outline: [] as { title: string; description: string; word_count: number }[]
})

const rules = {
  topic: [{ required: true, message: '请输入文章主题', type: 'error' }],
  style_name: [{ required: true, message: '请选择写作风格', type: 'error' }]
}

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  try {
    const response = await styleApi.getStyleList()
    if (response.data?.styles) {
      styleList.value = response.data.styles
    }
  } catch (error) {
    console.error('Failed to fetch styles:', error)
  }
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})

const addOutline = () => {
  formData.outline.push({ title: '', description: '', word_count: 200 })
}

const removeOutline = (index: number) => {
  formData.outline.splice(index, 1)
}

const handleReset = () => {
  formData.topic = ''
  formData.style_name = ''
  formData.target_length = 1000
  formData.outline = []
}

const handleGenerate = async () => {
  if (!formData.topic || !formData.style_name) {
    MessagePlugin.warning('请填写完整信息')
    return
  }

  generating.value = true
  taskId.value = null
  progress.value = 0
  progressText.value = '正在创建任务...'

  try {
    const response = await articleApi.generateArticle({
      topic: formData.topic,
      style_name: formData.style_name,
      outline: formData.outline,
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
  max-width: 900px;
  margin: 0 auto;
}

.progress-card {
  margin-top: 24px;
}

.progress-text {
  margin-top: 12px;
  color: #666;
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
</style>
