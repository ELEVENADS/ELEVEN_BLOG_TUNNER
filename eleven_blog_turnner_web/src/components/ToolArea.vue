<template>
  <t-card title="智能工具区" :bordered="false" :header-style="{ padding: '12px' }">
    <div class="tool-area-content">
      <!-- 选中文本预览 -->
      <div v-if="editorStore.hasSelection" class="selected-text-preview">
        <div class="preview-header">
          <t-icon name="quote" />
          <span>选中的文本 ({{ editorStore.selectionLength }} 字符)</span>
        </div>
        <div class="preview-content">
          {{ editorStore.selectedText.substring(0, 100) }}
          <span v-if="editorStore.selectedText.length > 100">...</span>
        </div>
      </div>
      <div v-else class="no-selection-tip">
        <t-icon name="tips" />
        <span>在编辑器中选中文本以使用智能工具</span>
      </div>

      <!-- 结果显示区域（显示在选中文本预览下方） -->
      <div class="tool-result" v-if="toolResult || loading.any">
        <div class="result-header">
          <div class="result-title">
            <t-icon name="assignment" />
            <span>{{ resultTitle }}</span>
          </div>
          <div class="result-actions" v-show="toolResult && !loading.any">
            <!-- 续写、总结：在选区后插入 -->
            <template v-if="currentTaskType === 'continue' || currentTaskType === 'summarize'">
              <t-button theme="primary" size="small" @click="insertAfterSelection">
                <template #icon>
                  <t-icon name="insert" />
                </template>
                插入选区后
              </t-button>
            </template>
            <!-- 润色、扩写、改写：替换选中的内容 -->
            <template v-else-if="currentTaskType === 'polish' || currentTaskType === 'expand' || currentTaskType === 'rewrite'">
              <t-button theme="primary" size="small" @click="replaceResult">
                <template #icon>
                  <t-icon name="refresh" />
                </template>
                替换选中文本
              </t-button>
            </template>
            <!-- 其他：在文档末尾插入 -->
            <template v-else>
              <t-button theme="primary" size="small" @click="insertResult">
                <template #icon>
                  <t-icon name="insert" />
                </template>
                插入编辑器
              </t-button>
            </template>
            <t-button theme="default" size="small" variant="outline" @click="copyResult">
              <template #icon>
                <t-icon name="copy" />
              </template>
              复制
            </t-button>
            <t-button theme="danger" size="small" variant="text" @click="clearResultAndShowTools">
              <template #icon>
                <t-icon name="close" />
              </template>
              关闭
            </t-button>
          </div>
        </div>
        <div class="result-content" v-show="!loading.any && toolResult">
          <pre v-if="isCodeResult">{{ toolResult }}</pre>
          <div v-else class="result-text">{{ toolResult }}</div>
        </div>
        <div class="result-loading" v-show="loading.any">
          <t-loading text="AI 正在生成内容..." size="small"></t-loading>
        </div>
      </div>

      <!-- 功能按钮区（有结果时隐藏） -->
      <template v-if="!toolResult && !loading.any">
        <!-- 选中文本操作 -->
        <t-divider align="left">选中文本操作</t-divider>
        <div class="button-grid">
          <t-button theme="primary" size="small" @click="handleContinueWriting" :loading="loading.continue">
            <template #icon>
              <t-icon name="edit" />
            </template>
            续写
          </t-button>
          <t-button theme="default" size="small" @click="handleExtractStyle" :loading="loading.extract">
            <template #icon>
              <t-icon name="palette" />
            </template>
            提取风格
          </t-button>
          <t-button theme="default" size="small" @click="handlePolish" :loading="loading.polish">
            <template #icon>
              <t-icon name="brush" />
            </template>
            润色
          </t-button>
          <t-button theme="default" size="small" @click="handleExpand" :loading="loading.expand">
            <template #icon>
              <t-icon name="maximize" />
            </template>
            扩写
          </t-button>
          <t-button theme="default" size="small" @click="handleSummarize" :loading="loading.summarize">
            <template #icon>
              <t-icon name="file" />
            </template>
            总结
          </t-button>
          <t-button theme="default" size="small" @click="handleSuggest" :loading="loading.suggest">
            <template #icon>
              <t-icon name="tips" />
            </template>
            建议
          </t-button>
        </div>

        <!-- 改写选项 -->
      <t-divider align="left">改写风格</t-divider>
      <div class="rewrite-section">
        <t-select
          v-model="rewriteStyle"
          :loading="loadingStyles"
          placeholder="选择系统风格"
          size="small"
          style="width: 100%"
        >
          <t-option
            v-for="style in systemStyles"
            :key="style.name"
            :label="style.name"
            :value="style.name"
          />
        </t-select>
        <t-button
          theme="default"
          size="small"
          @click="handleRewrite"
          :loading="loading.rewrite"
          :disabled="!rewriteStyle"
          style="width: 100%; margin-top: 8px;"
        >
          <template #icon>
            <t-icon name="refresh" />
          </template>
          改写为{{ rewriteStyleText }}
        </t-button>
        <t-link
          v-if="systemStyles.length === 0"
          theme="primary"
          size="small"
          @click="loadSystemStyles"
          style="margin-top: 4px; display: block; text-align: center;"
        >
          重新加载风格列表
        </t-link>
      </div>

        <!-- 编辑器操作 -->
        <t-divider align="left">编辑器操作</t-divider>
        <t-button theme="default" size="small" @click="handleExtractEditorStyle" :loading="loading.editorExtract" style="width: 100%">
          <template #icon>
            <t-icon name="scan" />
          </template>
          从编辑器提取风格
        </t-button>
      </template>

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
import { ref, reactive, computed, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { assistantApi, type AssistantTaskType, type ExtractStyleFromEditorResponse } from '@/api/assistant'
import { styleApi, type Style } from '@/api/style'
import { useEditorStore } from '@/stores/editor'

// Pinia Store - 从全局状态获取编辑器内容和选区
const editorStore = useEditorStore()

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

// 系统风格列表
const systemStyles = ref<Style[]>([])
const loadingStyles = ref(false)

// 改写风格（使用系统风格名称）
const rewriteStyle = ref('')
const rewriteStyleText = computed(() => {
  const style = systemStyles.value.find(s => s.name === rewriteStyle.value)
  return style?.name || '选择风格'
})

// 加载系统风格列表
const loadSystemStyles = async () => {
  loadingStyles.value = true
  try {
    const response = await styleApi.getStyleList()
    if (response?.data?.styles) {
      systemStyles.value = response.data.styles as Style[]
      // 默认选择第一个风格
      if (systemStyles.value.length > 0 && !rewriteStyle.value) {
        rewriteStyle.value = systemStyles.value[0].name
      }
    }
  } catch (error) {
    console.error('加载风格列表失败:', error)
  } finally {
    loadingStyles.value = false
  }
}

onMounted(() => {
  loadSystemStyles()
})

// 风格详情弹窗
const showStyleDialog = ref(false)
const extractedStyle = ref<ExtractStyleFromEditorResponse | null>(null)

// 获取当前选中的文本
const getSelectedText = (): string => {
  return editorStore.selectedText || ''
}

// 获取上下文
const getContext = (): string => {
  return editorStore.editorContent || ''
}

// 检查是否有选中文本
const hasSelection = (): boolean => {
  return editorStore.hasSelection
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
  // 注意：不要在开始加载时清空结果，这样用户可以看到上一次的结果直到新结果生成
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

    // 处理响应数据
    // API 返回 AssistantTaskResponse { result, task_type, metadata }
    console.log('[ToolArea] API 响应:', response)
    // response 直接是 AssistantTaskResponse
    const resultData = response.result
    console.log('[ToolArea] 提取的结果:', resultData)
    if (resultData && typeof resultData === 'string') {
      toolResult.value = resultData
      console.log('[ToolArea] 已设置 toolResult:', toolResult.value.substring(0, 50))
      MessagePlugin.success(`${title}完成`)
    } else {
      console.error('[ToolArea] 返回数据格式错误:', response)
      throw new Error('返回数据格式错误: 未找到 result 字段')
    }
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || error.message || `${title}失败`)
    // 错误时保留之前的结果，只显示错误提示
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
      selection_start: editorStore.selectionStart ?? undefined,
      selection_end: editorStore.selectionEnd ?? undefined,
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

// 插入结果（在文档末尾追加）
const insertResult = () => {
  if (toolResult.value) {
    editorStore.requestInsertContent(toolResult.value)
    MessagePlugin.success('已插入')
  }
}

// 替换选中的内容
const replaceResult = () => {
  if (toolResult.value) {
    editorStore.requestReplaceContent(toolResult.value)
    MessagePlugin.success('已替换选中的内容')
  }
}

// 在选区后插入内容
const insertAfterSelection = () => {
  if (toolResult.value) {
    editorStore.requestInsertAfterSelection(toolResult.value)
    MessagePlugin.success('已在选区后插入')
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

// 清空结果并显示工具区
const clearResultAndShowTools = () => {
  toolResult.value = ''
  MessagePlugin.success('结果已关闭，可以重新选择功能')
}



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
  max-width: 100%;
  box-sizing: border-box;
}

/* 按钮网格布局 */
.button-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
}

.button-grid .t-button {
  width: 100%;
  justify-content: center;
  padding: 4px 8px;
  font-size: 12px;
}

/* 改写区域 */
.rewrite-section {
  width: 100%;
}

.rewrite-section .t-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.rewrite-section .t-radio-button {
  flex: 1;
  min-width: 60px;
  text-align: center;
  font-size: 12px;
  padding: 4px 8px;
}

/* 选中文本预览 */
.selected-text-preview {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #1890ff;
  font-weight: 500;
  margin-bottom: 8px;
}

.preview-content {
  font-size: 13px;
  color: #333;
  line-height: 1.5;
  max-height: 80px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.no-selection-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 6px;
  color: #999;
  font-size: 13px;
  justify-content: center;
}

/* 结果显示区域 */
.tool-result {
  margin-top: 16px;
  padding: 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
  font-size: 14px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-end;
}

.result-actions .t-button {
  font-size: 12px;
  padding: 4px 8px;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #52c41a;
}

.result-content {
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.8;
  background: #fff;
  padding: 12px;
  border-radius: 4px;
}

.result-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  color: #333;
}

.result-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
}

.result-loading {
  padding: 24px 0;
  text-align: center;
  color: #999;
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
