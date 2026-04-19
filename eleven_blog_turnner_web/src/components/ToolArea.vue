<template>
  <t-card title="智能工具区" :bordered="false" :header-style="{ padding: '12px' }">
    <div class="tool-area-content">
      <!-- 选中文本操作 -->
      <t-divider align="left">选中文本操作</t-divider>
      <t-space direction="vertical" style="width: 100%">
        <t-space>
          <t-button theme="primary" @click="handleContinueWriting" :loading="loading.continue">
            <template #icon>
              <t-icon name="edit" />
            </template>
            续写
          </t-button>
          <t-button theme="default" @click="handleExtractStyle" :loading="loading.extract">
            <template #icon>
              <t-icon name="palette" />
            </template>
            提取风格
          </t-button>
          <t-button theme="default" @click="handlePolish" :loading="loading.polish">
            <template #icon>
              <t-icon name="brush" />
            </template>
            润色
          </t-button>
        </t-space>
        <t-space>
          <t-button theme="default" @click="handleExpand" :loading="loading.expand">
            <template #icon>
              <t-icon name="maximize" />
            </template>
            扩写
          </t-button>
          <t-button theme="default" @click="handleSummarize" :loading="loading.summarize">
            <template #icon>
              <t-icon name="file" />
            </template>
            总结
          </t-button>
          <t-button theme="default" @click="handleSuggest" :loading="loading.suggest">
            <template #icon>
              <t-icon name="tips" />
            </template>
            生成建议
          </t-button>
        </t-space>
      </t-space>

      <!-- 改写选项 -->
      <t-divider align="left">改写风格</t-divider>
      <t-space direction="vertical" style="width: 100%">
        <t-radio-group v-model="rewriteStyle" variant="default-filled">
          <t-radio-button value="professional">专业</t-radio-button>
          <t-radio-button value="casual">轻松</t-radio-button>
          <t-radio-button value="academic">学术</t-radio-button>
          <t-radio-button value="literary">文艺</t-radio-button>
          <t-radio-button value="humorous">幽默</t-radio-button>
        </t-radio-group>
        <t-button theme="default" @click="handleRewrite" :loading="loading.rewrite" style="width: 100%">
          <template #icon>
            <t-icon name="refresh" />
          </template>
          改写为{{ rewriteStyleText }}
        </t-button>
      </t-space>

      <!-- 编辑器操作 -->
      <t-divider align="left">编辑器操作</t-divider>
      <t-space direction="vertical" style="width: 100%">
        <t-button theme="default" @click="handleExtractEditorStyle" :loading="loading.editorExtract" style="width: 100%">
          <template #icon>
            <t-icon name="scan" />
          </template>
          从编辑器提取风格
        </t-button>
      </t-space>

      <!-- 结果显示区域 -->
      <div class="tool-result" v-if="toolResult || loading.any">
        <div class="result-header">
          <h4>{{ resultTitle }}</h4>
          <t-space v-if="toolResult">
            <t-button theme="primary" size="small" @click="insertResult">
              <template #icon>
                <t-icon name="insert" />
              </template>
              插入
            </t-button>
            <t-button theme="default" size="small" @click="copyResult">
              <template #icon>
                <t-icon name="copy" />
              </template>
              复制
            </t-button>
            <t-button theme="danger" size="small" variant="text" @click="clearResult">
              <template #icon>
                <t-icon name="close" />
              </template>
            </t-button>
          </t-space>
        </div>
        <div class="result-content" v-if="!loading.any">
          <pre v-if="isCodeResult">{{ toolResult }}</pre>
          <div v-else v-html="formattedResult"></div>
        </div>
        <div class="result-loading" v-else>
          <t-loading text="处理中..."></t-loading>
        </div>
      </div>

      <!-- 风格详情弹窗 -->
      <t-dialog v-model:visible="showStyleDialog" header="提取的风格特征" width="700px">
        <div v-if="extractedStyle" class="style-detail">
          <t-tabs default-value="semantic">
            <t-tab-panel value="semantic" label="语义特征">
              <t-descriptions :column="1" layout="vertical" v-if="extractedStyle.features?.semantic">
                <t-descriptions-item label="语言风格">
                  {{ extractedStyle.features.semantic.language_style || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="语气特征">
                  {{ extractedStyle.features.semantic.tone || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="词汇水平">
                  {{ extractedStyle.features.semantic.vocabulary_level || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="句式节奏">
                  {{ extractedStyle.features.semantic.sentence_rhythm || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="修辞手法">
                  <t-space v-if="extractedStyle.features.semantic.rhetoric_devices?.length" size="small">
                    <t-tag v-for="device in extractedStyle.features.semantic.rhetoric_devices" :key="device" theme="primary" variant="light">
                      {{ device }}
                    </t-tag>
                  </t-space>
                  <span v-else>未识别</span>
                </t-descriptions-item>
                <t-descriptions-item label="情感倾向">
                  {{ extractedStyle.features.semantic.emotional_tendency || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="叙述视角">
                  {{ extractedStyle.features.semantic.perspective || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="逻辑结构">
                  {{ extractedStyle.features.semantic.logic_structure || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="独特表达习惯">
                  <t-space v-if="extractedStyle.features.semantic.unique_habits?.length" direction="vertical">
                    <div v-for="habit in extractedStyle.features.semantic.unique_habits" :key="habit" class="habit-item">
                      • {{ habit }}
                    </div>
                  </t-space>
                  <span v-else>未识别</span>
                </t-descriptions-item>
                <t-descriptions-item label="目标读者">
                  {{ extractedStyle.features.semantic.target_audience || '未识别' }}
                </t-descriptions-item>
                <t-descriptions-item label="领域特征">
                  {{ extractedStyle.features.semantic.domain_characteristics || '未识别' }}
                </t-descriptions-item>
              </t-descriptions>
            </t-tab-panel>
            <t-tab-panel value="statistical" label="统计特征">
              <t-descriptions :column="2" v-if="extractedStyle.features?.statistical">
                <t-descriptions-item label="词汇多样性">
                  {{ formatPercent(extractedStyle.features.statistical.vocabulary_diversity) }}
                </t-descriptions-item>
                <t-descriptions-item label="平均词长">
                  {{ extractedStyle.features.statistical.average_word_length?.toFixed(2) }}
                </t-descriptions-item>
                <t-descriptions-item label="独特词比例">
                  {{ formatPercent(extractedStyle.features.statistical.unique_words_ratio) }}
                </t-descriptions-item>
                <t-descriptions-item label="平均句长">
                  {{ extractedStyle.features.statistical.average_sentence_length?.toFixed(1) }}
                </t-descriptions-item>
                <t-descriptions-item label="句式复杂度">
                  {{ extractedStyle.features.statistical.sentence_complexity?.toFixed(2) }}
                </t-descriptions-item>
                <t-descriptions-item label="标点密度">
                  {{ formatPercent(extractedStyle.features.statistical.punctuation_density) }}
                </t-descriptions-item>
              </t-descriptions>
            </t-tab-panel>
          </t-tabs>
        </div>
      </t-dialog>
    </div>
  </t-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { assistantApi, type AssistantTaskType, type ExtractStyleFromEditorResponse } from '@/api/assistant'

// Props - 从父组件传入编辑器内容和选区
const props = defineProps<{
  editorContent?: string
  selectedText?: string
  selectionStart?: number
  selectionEnd?: number
}>()

// Emits - 向父组件发送结果
const emit = defineEmits<{
  (e: 'insert', text: string): void
  (e: 'replace', text: string, start: number, end: number): void
}>()

// 加载状态
const loading = reactive({
  continue: false,
  extract: false,
  polish: false,
  expand: false,
  summarize: false,
  suggest: false,
  rewrite: false,
  editorExtract: false,
  any: computed(() =>
    loading.continue ||
    loading.extract ||
    loading.polish ||
    loading.expand ||
    loading.summarize ||
    loading.suggest ||
    loading.rewrite ||
    loading.editorExtract
  )
})

// 结果相关
const toolResult = ref('')
const resultTitle = ref('')
const currentTaskType = ref<AssistantTaskType>('continue')
const isCodeResult = ref(false)

// 改写风格
const rewriteStyle = ref('professional')
const rewriteStyleText = computed(() => {
  const map: Record<string, string> = {
    professional: '专业风格',
    casual: '轻松风格',
    academic: '学术风格',
    literary: '文艺风格',
    humorous: '幽默风格'
  }
  return map[rewriteStyle.value] || '专业风格'
})

// 风格详情弹窗
const showStyleDialog = ref(false)
const extractedStyle = ref<ExtractStyleFromEditorResponse | null>(null)

// 获取当前选中的文本
const getSelectedText = (): string => {
  return props.selectedText || ''
}

// 获取上下文
const getContext = (): string => {
  return props.editorContent || ''
}

// 检查是否有选中文本
const hasSelection = (): boolean => {
  const text = getSelectedText()
  return text.length > 0
}

// 执行辅助任务
const executeTask = async (
  taskType: AssistantTaskType,
  title: string,
  loadingKey: keyof typeof loading
) => {
  const selectedText = getSelectedText()

  if (!selectedText && taskType !== 'extract_style') {
    MessagePlugin.warning('请先选中文本')
    return
  }

  if (taskType === 'extract_style' && selectedText.length < 50) {
    MessagePlugin.warning('选中的文本太短，无法提取风格（至少需要50字符）')
    return
  }

  loading[loadingKey] = true
  currentTaskType.value = taskType
  resultTitle.value = title
  toolResult.value = ''
  isCodeResult.value = false

  try {
    const context = getContext()
    let response

    switch (taskType) {
      case 'continue':
        response = await assistantApi.continueWriting(selectedText, context, { length: 200 })
        break
      case 'extract_style':
        response = await assistantApi.extractStyle(selectedText)
        isCodeResult.value = true
        break
      case 'polish':
        response = await assistantApi.polish(selectedText)
        break
      case 'expand':
        response = await assistantApi.expand(selectedText, 300)
        break
      case 'summarize':
        response = await assistantApi.summarize(selectedText)
        break
      case 'suggest':
        response = await assistantApi.generateSuggestions(selectedText, context)
        isCodeResult.value = true
        break
      case 'rewrite':
        response = await assistantApi.rewrite(selectedText, rewriteStyle.value)
        break
      default:
        throw new Error('未知的任务类型')
    }

    if (response.data?.result) {
      toolResult.value = response.data.result
      MessagePlugin.success(`${title}完成`)
    }
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || `${title}失败`)
    toolResult.value = ''
  } finally {
    loading[loadingKey] = false
  }
}

// 处理续写
const handleContinueWriting = () => {
  executeTask('continue', '续写', 'continue')
}

// 处理提取风格
const handleExtractStyle = () => {
  executeTask('extract_style', '风格提取', 'extract')
}

// 处理润色
const handlePolish = () => {
  executeTask('polish', '润色', 'polish')
}

// 处理扩写
const handleExpand = () => {
  executeTask('expand', '扩写', 'expand')
}

// 处理总结
const handleSummarize = () => {
  executeTask('summarize', '总结', 'summarize')
}

// 处理生成建议
const handleSuggest = () => {
  executeTask('suggest', '生成建议', 'suggest')
}

// 处理改写
const handleRewrite = () => {
  executeTask('rewrite', '改写', 'rewrite')
}

// 从编辑器提取风格
const handleExtractEditorStyle = async () => {
  const content = getContext()

  if (!content || content.length < 100) {
    MessagePlugin.warning('编辑器内容太短，无法提取风格（至少需要100字符）')
    return
  }

  loading.editorExtract = true

  try {
    const response = await assistantApi.extractStyleFromEditor({
      content,
      selection_start: props.selectionStart,
      selection_end: props.selectionEnd,
      use_llm: true
    })

    if (response.data) {
      extractedStyle.value = response.data
      showStyleDialog.value = true
      MessagePlugin.success('风格提取成功')
    }
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '风格提取失败')
  } finally {
    loading.editorExtract = false
  }
}

// 插入结果
const insertResult = () => {
  if (toolResult.value) {
    emit('insert', toolResult.value)
    MessagePlugin.success('已插入')
  }
}

// 复制结果
const copyResult = () => {
  if (toolResult.value) {
    navigator.clipboard.writeText(toolResult.value)
    MessagePlugin.success('已复制到剪贴板')
  }
}

// 清空结果
const clearResult = () => {
  toolResult.value = ''
}

// 格式化结果（将换行符转为HTML）
const formattedResult = computed(() => {
  if (!toolResult.value) return ''
  return toolResult.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
})

// 格式化百分比
const formatPercent = (value: number | undefined) => {
  if (value === undefined || value === null) return '0%'
  return (value * 100).toFixed(1) + '%'
}
</script>

<style scoped>
.tool-area-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-result {
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: bold;
}

.result-content {
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.6;
}

.result-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
}

.result-loading {
  padding: 40px 0;
  text-align: center;
}

.style-detail {
  padding: 16px 0;
}

.habit-item {
  padding: 2px 0;
  color: #666;
}

:deep(.t-divider__inner-text) {
  font-size: 12px;
  color: #999;
}
</style>
