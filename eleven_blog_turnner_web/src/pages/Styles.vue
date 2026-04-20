<template>
  <div class="styles-page">
    <t-card title="风格管理" bordered>
      <template #actions>
        <t-space>
          <t-button theme="primary" @click="showLearnDialog = true">
            <template #icon>
              <t-icon name="add" />
            </template>
            学习新风格
          </t-button>
          <t-button theme="primary" variant="outline" @click="openExtractDialog">
            <template #icon>
              <t-icon name="download" />
            </template>
            从笔记/文章提取
          </t-button>
        </t-space>
      </template>

      <t-table :data="styles" :columns="columns" row-key="name" hover :loading="loading">
        <template #metadata="{ row }">
          <span>{{ row.metadata?.source || row.metadata?.source_file || '手动输入' }}</span>
        </template>
        <template #analysis_mode="{ row }">
          <t-space size="small">
            <t-tag v-if="row.analysis_mode?.use_statistical" theme="success" variant="light">统计</t-tag>
            <t-tag v-if="row.analysis_mode?.use_semantic" theme="primary" variant="light">语义</t-tag>
            <t-tag v-if="row.analysis_mode?.use_embedding" theme="warning" variant="light">向量</t-tag>
          </t-space>
        </template>
        <template #operations="{ row }">
          <t-space>
            <t-link @click="viewStyle(row)">查看</t-link>
            <t-link theme="primary" @click="showEditDialog(row)">编辑</t-link>
            <t-link theme="primary" @click="showAddSampleDialog(row.name)">添加样本</t-link>
            <t-link theme="danger" @click="deleteStyle(row.name)">删除</t-link>
          </t-space>
        </template>
      </t-table>
    </t-card>

    <!-- 学习新风格对话框 -->
    <t-dialog v-model:visible="showLearnDialog" header="学习新风格" :footer="false" width="700px">
      <t-form :data="learnForm" @submit="handleLearn">
        <t-form-item label="风格名称" name="style_name">
          <t-input v-model="learnForm.style_name" placeholder="请输入风格名称" />
        </t-form-item>
        <t-form-item label="示例文本" name="text">
          <t-textarea
            v-model="learnForm.text"
            placeholder="请粘贴您的写作样本，段落越多学习效果越好"
            :autosize="{ minRows: 5, maxRows: 10 }"
          />
        </t-form-item>

        <!-- 分析模式选择 -->
        <t-form-item label="分析模式">
          <t-space direction="vertical">
            <t-checkbox v-model="learnForm.use_statistical">使用规则统计特征（快速）</t-checkbox>
            <t-checkbox v-model="learnForm.use_semantic">使用 LLM 语义分析（深度）</t-checkbox>
            <t-checkbox v-model="learnForm.use_embedding">使用 Embedding 向量</t-checkbox>
          </t-space>
        </t-form-item>

        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="learning">开始学习</t-button>
            <t-button @click="showLearnDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 从笔记/文章提取对话框 -->
    <t-dialog v-model:visible="showExtractDialog" header="从笔记/文章提取风格" :footer="false" width="800px">
      <t-form :data="extractForm" @submit="handleExtract">
        <t-form-item label="提取来源" name="source_type">
          <t-radio-group v-model="extractForm.source_type" variant="default-filled">
            <t-radio-button value="note">笔记</t-radio-button>
            <t-radio-button value="article">文章</t-radio-button>
          </t-radio-group>
        </t-form-item>

        <!-- 文件列表选择 -->
        <t-form-item label="选择文件">
          <t-card :bordered="true" :shadow="false" style="max-height: 300px; overflow-y: auto;">
            <t-list v-if="filteredFileList.length > 0" size="small">
              <t-list-item
                v-for="file in filteredFileList"
                :key="file.id"
                :class="{ 'is-active': selectedFile?.id === file.id }"
                @click="selectFile(file)"
              >
                <t-space>
                  <t-icon :name="file.type === 'folder' ? 'folder' : 'file'" />
                  <span>{{ file.label }}</span>
                  <t-tag v-if="file.type === 'note'" theme="primary" variant="light" size="small">笔记</t-tag>
                  <t-tag v-if="file.type === 'article'" theme="success" variant="light" size="small">文章</t-tag>
                </t-space>
              </t-list-item>
            </t-list>
            <t-empty v-else description="暂无数据" />
          </t-card>
        </t-form-item>

        <!-- 已选择显示 -->
        <t-form-item label="已选择" v-if="selectedFile">
          <t-alert theme="info">
            <template #title>
              {{ selectedFile.label }}
            </template>
            <template #default>
              类型: {{ selectedFile.type === 'note' ? '笔记' : '文章' }}
            </template>
          </t-alert>
        </t-form-item>

        <t-form-item label="风格名称" name="style_name">
          <t-input v-model="extractForm.style_name" placeholder="请输入风格名称" />
        </t-form-item>

        <!-- 分析模式选择 -->
        <t-form-item label="分析模式">
          <t-space direction="vertical">
            <t-checkbox v-model="extractForm.use_statistical">使用规则统计特征（快速）</t-checkbox>
            <t-checkbox v-model="extractForm.use_semantic">使用 LLM 语义分析（深度）</t-checkbox>
            <t-checkbox v-model="extractForm.use_embedding">使用 Embedding 向量</t-checkbox>
          </t-space>
        </t-form-item>

        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="extracting">开始提取</t-button>
            <t-button @click="showExtractDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 添加风格样本对话框 -->
    <t-dialog v-model:visible="showAddSampleDialogVisible" header="添加风格样本" :footer="false" width="600px">
      <t-form :data="sampleForm" @submit="handleAddSample">
        <t-form-item label="样本内容" name="text">
          <t-textarea
            v-model="sampleForm.text"
            placeholder="请粘贴新的写作样本"
            :autosize="{ minRows: 5, maxRows: 10 }"
          />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="adding">添加</t-button>
            <t-button @click="showAddSampleDialogVisible = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 编辑风格对话框 -->
    <t-dialog v-model:visible="showEditDialogVisible" header="编辑风格" :footer="false" width="700px">
      <t-form :data="editForm" @submit="handleEdit">
        <t-form-item label="风格名称" name="name">
          <t-input v-model="editForm.name" placeholder="请输入风格名称" />
        </t-form-item>
        <t-form-item label="语义特征 - 语言风格" name="language_style">
          <t-input v-model="editForm.semantic.language_style" placeholder="如：专业、轻松、学术等" />
        </t-form-item>
        <t-form-item label="语义特征 - 语气特征" name="tone">
          <t-input v-model="editForm.semantic.tone" placeholder="如：正式、随意、幽默等" />
        </t-form-item>
        <t-form-item label="语义特征 - 词汇水平" name="vocabulary_level">
          <t-input v-model="editForm.semantic.vocabulary_level" placeholder="如：高、中、低等" />
        </t-form-item>
        <t-form-item label="语义特征 - 句式节奏" name="sentence_rhythm">
          <t-input v-model="editForm.semantic.sentence_rhythm" placeholder="如：长短结合、平稳等" />
        </t-form-item>
        <t-form-item label="语义特征 - 情感倾向" name="emotional_tendency">
          <t-input v-model="editForm.semantic.emotional_tendency" placeholder="如：积极、中性、消极等" />
        </t-form-item>
        <t-form-item label="语义特征 - 叙述视角" name="perspective">
          <t-input v-model="editForm.semantic.perspective" placeholder="如：第一人称、第三人称等" />
        </t-form-item>
        <t-form-item label="语义特征 - 逻辑结构" name="logic_structure">
          <t-input v-model="editForm.semantic.logic_structure" placeholder="如：总分总、并列等" />
        </t-form-item>
        <t-form-item label="语义特征 - 目标读者" name="target_audience">
          <t-input v-model="editForm.semantic.target_audience" placeholder="如：专业人士、普通读者等" />
        </t-form-item>
        <t-form-item label="语义特征 - 领域特征" name="domain_characteristics">
          <t-input v-model="editForm.semantic.domain_characteristics" placeholder="如：科技、文学、商业等" />
        </t-form-item>
        <t-form-item label="语义特征 - 其他特点" name="writing_quirks">
          <t-textarea
            v-model="editForm.semantic.writing_quirks"
            placeholder="其他写作特点描述"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
        </t-form-item>
        <t-form-item label="独特表达习惯" name="unique_habits">
          <t-textarea
            v-model="editForm.uniqueHabitsText"
            placeholder="每行一个习惯，如：
喜欢使用排比句
善用比喻修辞
段落开头常用设问"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="editing">保存修改</t-button>
            <t-button @click="showEditDialogVisible = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 风格详情抽屉 -->
    <t-drawer v-model:visible="showDetailDrawer" :header="`风格详情: ${currentStyle?.name}`" size="800px">
      <div v-if="currentStyle" class="style-detail">
        <!-- 基本信息 -->
        <t-card title="基本信息" class="detail-section">
          <t-descriptions :column="2">
            <t-descriptions-item label="风格名称">{{ currentStyle.name }}</t-descriptions-item>
            <t-descriptions-item label="样本数">{{ currentStyle.sample_count || 1 }}</t-descriptions-item>
            <t-descriptions-item label="总字符数">{{ currentStyle.total_chars || 0 }}</t-descriptions-item>
            <t-descriptions-item label="创建时间">{{ formatDate(currentStyle.created_at) }}</t-descriptions-item>
            <t-descriptions-item label="更新时间">{{ formatDate(currentStyle.updated_at) }}</t-descriptions-item>
            <t-descriptions-item label="分析模式">
              <t-space size="small">
                <t-tag v-if="currentStyle.analysis_mode?.use_statistical" theme="success" variant="light">统计</t-tag>
                <t-tag v-if="currentStyle.analysis_mode?.use_semantic" theme="primary" variant="light">语义</t-tag>
                <t-tag v-if="currentStyle.analysis_mode?.use_embedding" theme="warning" variant="light">向量</t-tag>
              </t-space>
            </t-descriptions-item>
          </t-descriptions>
        </t-card>

        <!-- 统计特征 -->
        <t-card v-if="currentStyle.features?.statistical" title="统计特征" class="detail-section">
          <t-descriptions :column="2">
            <t-descriptions-item label="词汇多样性">
              {{ formatPercent(currentStyle.features.statistical.vocabulary_diversity) }}
            </t-descriptions-item>
            <t-descriptions-item label="平均词长">
              {{ currentStyle.features.statistical.average_word_length?.toFixed(2) }}
            </t-descriptions-item>
            <t-descriptions-item label="独特词比例">
              {{ formatPercent(currentStyle.features.statistical.unique_words_ratio) }}
            </t-descriptions-item>
            <t-descriptions-item label="平均句长">
              {{ currentStyle.features.statistical.average_sentence_length?.toFixed(1) }}
            </t-descriptions-item>
            <t-descriptions-item label="句式复杂度">
              {{ currentStyle.features.statistical.sentence_complexity?.toFixed(2) }}
            </t-descriptions-item>
            <t-descriptions-item label="标点密度">
              {{ formatPercent(currentStyle.features.statistical.punctuation_density) }}
            </t-descriptions-item>
            <t-descriptions-item label="平均段落长度">
              {{ currentStyle.features.statistical.paragraph_average_length?.toFixed(1) }}
            </t-descriptions-item>
            <t-descriptions-item label="过渡词比例">
              {{ formatPercent(currentStyle.features.statistical.transition_words_ratio) }}
            </t-descriptions-item>
            <t-descriptions-item label="被动语态比例">
              {{ formatPercent(currentStyle.features.statistical.passive_voice_ratio) }}
            </t-descriptions-item>
            <t-descriptions-item label="第一人称比例">
              {{ formatPercent(currentStyle.features.statistical.first_person_ratio) }}
            </t-descriptions-item>
            <t-descriptions-item label="表情符号使用率">
              {{ formatPercent(currentStyle.features.statistical.emoji_usage) }}
            </t-descriptions-item>
          </t-descriptions>
        </t-card>

        <!-- 语义特征 -->
        <t-card v-if="currentStyle.features?.semantic" title="语义特征（LLM 分析）" class="detail-section">
          <t-descriptions :column="1" layout="vertical">
            <t-descriptions-item label="语言风格">
              {{ currentStyle.features.semantic.language_style || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="语气特征">
              {{ currentStyle.features.semantic.tone || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="词汇水平">
              {{ currentStyle.features.semantic.vocabulary_level || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="句式节奏">
              {{ currentStyle.features.semantic.sentence_rhythm || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="修辞手法">
              <t-space v-if="currentStyle.features.semantic.rhetoric_devices?.length" size="small">
                <t-tag v-for="device in currentStyle.features.semantic.rhetoric_devices" :key="device" theme="primary" variant="light">
                  {{ device }}
                </t-tag>
              </t-space>
              <span v-else>未识别</span>
            </t-descriptions-item>
            <t-descriptions-item label="情感倾向">
              {{ currentStyle.features.semantic.emotional_tendency || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="叙述视角">
              {{ currentStyle.features.semantic.perspective || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="逻辑结构">
              {{ currentStyle.features.semantic.logic_structure || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="独特表达习惯">
              <t-space v-if="currentStyle.features.semantic.unique_habits?.length" direction="vertical">
                <div v-for="habit in currentStyle.features.semantic.unique_habits" :key="habit" class="habit-item">
                  • {{ habit }}
                </div>
              </t-space>
              <span v-else>未识别</span>
            </t-descriptions-item>
            <t-descriptions-item label="目标读者">
              {{ currentStyle.features.semantic.target_audience || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="领域特征">
              {{ currentStyle.features.semantic.domain_characteristics || '未识别' }}
            </t-descriptions-item>
            <t-descriptions-item label="其他特点">
              {{ currentStyle.features.semantic.writing_quirks || '无' }}
            </t-descriptions-item>
          </t-descriptions>
        </t-card>

        <!-- 向量信息 -->
        <t-card title="向量信息" class="detail-section">
          <t-descriptions :column="1">
            <t-descriptions-item label="向量维度">
              {{ currentStyle.vector?.length || 0 }} 维
            </t-descriptions-item>
            <t-descriptions-item label="向量预览">
              <div class="vector-preview">
                {{ currentStyle.vector?.slice(0, 10).map(v => v.toFixed(4)).join(', ') }}...
              </div>
            </t-descriptions-item>
          </t-descriptions>
        </t-card>
      </div>
    </t-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { styleApi, type Style, type LearnStyleRequest } from '@/api/style'
import { fileTreeApi, type TreeNode } from '@/api/fileTree'

const loading = ref(false)
const styles = ref<Style[]>([])
const showLearnDialog = ref(false)
const learning = ref(false)
const showExtractDialog = ref(false)
const extracting = ref(false)
const showAddSampleDialogVisible = ref(false)
const adding = ref(false)
const showDetailDrawer = ref(false)
const currentStyle = ref<Style | null>(null)
const showEditDialogVisible = ref(false)
const editing = ref(false)

// 文件列表相关
const fileTreeData = ref<TreeNode[]>([])
const selectedFile = ref<TreeNode | null>(null)

// 过滤后的文件列表（只显示指定类型的文件，不显示文件夹）
const filteredFileList = computed(() => {
  const result: TreeNode[] = []
  const traverse = (nodes: TreeNode[]) => {
    for (const node of nodes) {
      // 只添加匹配类型的文件（笔记或文章），不添加文件夹
      if (node.type !== 'folder' && node.type === extractForm.source_type) {
        result.push(node)
      }
      // 递归遍历子节点
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    }
  }
  traverse(fileTreeData.value)
  return result
})

const learnForm = reactive<LearnStyleRequest>({
  style_name: '',
  text: '',
  use_statistical: true,
  use_semantic: true,
  use_embedding: true
})

const extractForm = reactive<{
  source_type: 'note' | 'article'
  source_id: string
  style_name: string
  use_statistical: boolean
  use_semantic: boolean
  use_embedding: boolean
}>({
  source_type: 'note',
  source_id: '',
  style_name: '',
  use_statistical: true,
  use_semantic: true,
  use_embedding: true
})

const sampleForm = reactive({
  style_name: '',
  text: ''
})

// 编辑表单
const editForm = reactive({
  originalName: '', // 原始名称，用于 API 调用
  name: '', // 新名称
  semantic: {
    language_style: '',
    tone: '',
    vocabulary_level: '',
    sentence_rhythm: '',
    emotional_tendency: '',
    perspective: '',
    logic_structure: '',
    target_audience: '',
    domain_characteristics: '',
    writing_quirks: ''
  },
  uniqueHabitsText: ''
})

const columns = [
  { colKey: 'name', title: '风格名称', width: '150' },
  { colKey: 'metadata', title: '来源', width: '120' },
  { colKey: 'analysis_mode', title: '分析模式', width: '180' },
  { colKey: 'sample_count', title: '样本数', width: '80' },
  { colKey: 'total_chars', title: '总字符数', width: '100' },
  { colKey: 'updated_at', title: '更新时间', width: '180' },
  { colKey: 'operations', title: '操作', width: '300' }
]

onMounted(() => {
  fetchStyles()
})

const fetchStyles = async () => {
  loading.value = true
  try {
    const response = await styleApi.getStyleList()
    if (response?.data?.styles) {
      styles.value = response.data.styles as Style[]
    } else {
      styles.value = []
    }
  } catch (error) {
    console.error('Failed to fetch styles:', error)
    styles.value = []
  } finally {
    loading.value = false
  }
}

const handleLearn = async () => {
  if (!learnForm.style_name || !learnForm.text) {
    MessagePlugin.warning('请填写完整信息')
    return
  }

  learning.value = true
  try {
    await styleApi.learnStyle(learnForm)
    MessagePlugin.success('风格学习成功')
    showLearnDialog.value = false
    learnForm.style_name = ''
    learnForm.text = ''
    learnForm.use_statistical = true
    learnForm.use_semantic = true
    learnForm.use_embedding = true
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '学习失败')
  } finally {
    learning.value = false
  }
}

// 加载文件树
const loadFileTree = async () => {
  try {
    const tree = await fileTreeApi.getFileTree()
    console.log('File tree loaded:', tree)
    if (Array.isArray(tree)) {
      fileTreeData.value = tree
    } else {
      console.error('Invalid file tree data:', tree)
      fileTreeData.value = []
      MessagePlugin.error('文件树数据格式错误')
    }
  } catch (error) {
    console.error('Failed to load file tree:', error)
    fileTreeData.value = []
    MessagePlugin.error('加载文件树失败')
  }
}

// 选择文件
const selectFile = (file: TreeNode) => {
  selectedFile.value = file
  extractForm.source_id = file.id
  extractForm.source_type = file.type as 'note' | 'article'
}

const handleExtract = async () => {
  if (!extractForm.source_id || !extractForm.style_name) {
    MessagePlugin.warning('请选择文件并填写风格名称')
    return
  }

  extracting.value = true
  try {
    if (extractForm.source_type === 'note') {
      await styleApi.extractFromNote({
        note_id: extractForm.source_id,
        style_name: extractForm.style_name,
        use_statistical: extractForm.use_statistical,
        use_semantic: extractForm.use_semantic,
        use_embedding: extractForm.use_embedding
      })
    } else {
      await styleApi.extractFromArticle({
        article_id: extractForm.source_id,
        style_name: extractForm.style_name,
        use_statistical: extractForm.use_statistical,
        use_semantic: extractForm.use_semantic,
        use_embedding: extractForm.use_embedding
      })
    }
    MessagePlugin.success('风格提取成功')
    showExtractDialog.value = false
    extractForm.source_id = ''
    extractForm.style_name = ''
    extractForm.use_statistical = true
    extractForm.use_semantic = true
    extractForm.use_embedding = true
    selectedFile.value = null
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '提取失败')
  } finally {
    extracting.value = false
  }
}

const viewStyle = async (style: Style) => {
  try {
    const response = await styleApi.getStyleDetail(style.name)
    if (response.data) {
      currentStyle.value = response.data
      showDetailDrawer.value = true
    }
  } catch (error) {
    MessagePlugin.error('获取风格详情失败')
  }
}

const deleteStyle = async (name: string) => {
  try {
    await styleApi.deleteStyle(name)
    MessagePlugin.success('删除成功')
    fetchStyles()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}

const showAddSampleDialog = (styleName: string) => {
  sampleForm.style_name = styleName
  sampleForm.text = ''
  showAddSampleDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = async (style: Style) => {
  try {
    const response = await styleApi.getStyleDetail(style.name)
    if (response.data) {
      const detail = response.data
      editForm.originalName = detail.name // 保存原始名称
      editForm.name = detail.name // 当前名称（可修改）
      editForm.semantic.language_style = detail.features?.semantic?.language_style || ''
      editForm.semantic.tone = detail.features?.semantic?.tone || ''
      editForm.semantic.vocabulary_level = detail.features?.semantic?.vocabulary_level || ''
      editForm.semantic.sentence_rhythm = detail.features?.semantic?.sentence_rhythm || ''
      editForm.semantic.emotional_tendency = detail.features?.semantic?.emotional_tendency || ''
      editForm.semantic.perspective = detail.features?.semantic?.perspective || ''
      editForm.semantic.logic_structure = detail.features?.semantic?.logic_structure || ''
      editForm.semantic.target_audience = detail.features?.semantic?.target_audience || ''
      editForm.semantic.domain_characteristics = detail.features?.semantic?.domain_characteristics || ''
      editForm.semantic.writing_quirks = detail.features?.semantic?.writing_quirks || ''
      editForm.uniqueHabitsText = detail.features?.semantic?.unique_habits?.join('\n') || ''
      showEditDialogVisible.value = true
    }
  } catch (error) {
    MessagePlugin.error('获取风格详情失败')
  }
}

// 处理编辑提交
const handleEdit = async () => {
  if (!editForm.name) {
    MessagePlugin.warning('风格名称不能为空')
    return
  }

  editing.value = true
  try {
    // 将文本框中的习惯转换为数组
    const uniqueHabits = editForm.uniqueHabitsText
      .split('\n')
      .map(h => h.trim())
      .filter(h => h.length > 0)

    // 调用更新风格的 API，传入原始名称和新名称
    await styleApi.updateStyle(editForm.originalName, {
      style_name: editForm.name, // 新名称
      features: {
        semantic: {
          language_style: editForm.semantic.language_style,
          tone: editForm.semantic.tone,
          vocabulary_level: editForm.semantic.vocabulary_level,
          sentence_rhythm: editForm.semantic.sentence_rhythm,
          emotional_tendency: editForm.semantic.emotional_tendency,
          perspective: editForm.semantic.perspective,
          logic_structure: editForm.semantic.logic_structure,
          target_audience: editForm.semantic.target_audience,
          domain_characteristics: editForm.semantic.domain_characteristics,
          writing_quirks: editForm.semantic.writing_quirks,
          unique_habits: uniqueHabits
        }
      }
    })

    MessagePlugin.success('风格更新成功')
    showEditDialogVisible.value = false
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '更新失败')
  } finally {
    editing.value = false
  }
}

const handleAddSample = async () => {
  if (!sampleForm.style_name || !sampleForm.text) {
    MessagePlugin.warning('请填写完整信息')
    return
  }

  adding.value = true
  try {
    await styleApi.addStyleSample(sampleForm.style_name, sampleForm.text)
    MessagePlugin.success('样本添加成功，风格已更新')
    showAddSampleDialogVisible.value = false
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '添加失败')
  } finally {
    adding.value = false
  }
}

const openExtractDialog = async () => {
  await loadFileTree()
  // 重置选择
  selectedFile.value = null
  extractForm.source_id = ''
  extractForm.style_name = ''
  extractForm.use_statistical = true
  extractForm.use_semantic = true
  extractForm.use_embedding = true
  showExtractDialog.value = true
}

// 格式化百分比
const formatPercent = (value: number | undefined) => {
  if (value === undefined || value === null) return '0%'
  return (value * 100).toFixed(1) + '%'
}

// 格式化日期
const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.styles-page {
  max-width: 1400px;
  margin: 0 auto;
}

.detail-section {
  margin-bottom: 20px;
}

.habit-item {
  padding: 4px 0;
  color: #666;
}

.vector-preview {
  font-family: monospace;
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

:deep(.t-list-item) {
  cursor: pointer;
  transition: background-color 0.2s;
}

:deep(.t-list-item:hover) {
  background-color: #f5f5f5;
}

:deep(.t-list-item.is-active) {
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}
</style>
