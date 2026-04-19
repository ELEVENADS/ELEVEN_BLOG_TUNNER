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
        <template #operations="{ row }">
          <t-space>
            <t-link @click="viewStyle(row.name)">查看</t-link>
            <t-link theme="primary" @click="showAddSampleDialog(row.name)">添加样本</t-link>
            <t-link theme="danger" @click="deleteStyle(row.name)">删除</t-link>
          </t-space>
        </template>
      </t-table>
    </t-card>

    <t-dialog v-model:visible="showLearnDialog" header="学习新风格" :footer="false" width="600px">
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
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="learning">开始学习</t-button>
            <t-button @click="showLearnDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

    <t-dialog v-model:visible="showExtractDialog" header="从笔记/文章提取风格" :footer="false" width="600px">
      <t-form :data="extractForm" @submit="handleExtract">
        <t-form-item label="提取来源" name="source_type">
          <t-radio-group v-model="extractForm.source_type">
            <t-radio value="note">笔记</t-radio>
            <t-radio value="article">文章</t-radio>
          </t-radio-group>
        </t-form-item>
        <t-form-item label="选择来源" name="source_id">
          <t-select
            v-model="extractForm.source_id"
            :placeholder="extractForm.source_type === 'note' ? '请选择笔记' : '请选择文章'"
            filterable
          >
            <t-option
              v-for="item in extractForm.source_type === 'note' ? notes : articles"
              :key="item.id"
              :value="item.id"
              :label="item.title"
            />
          </t-select>
        </t-form-item>
        <t-form-item label="风格名称" name="style_name">
          <t-input v-model="extractForm.style_name" placeholder="请输入风格名称" />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="extracting">开始提取</t-button>
            <t-button @click="showExtractDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>

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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { styleApi, type Style } from '@/api/style'
import { notesApi } from '@/api/notes'
import { articleApi } from '@/api/article'

const loading = ref(false)
const styles = ref<Style[]>([])
const showLearnDialog = ref(false)
const learning = ref(false)
const showExtractDialog = ref(false)
const extracting = ref(false)
const notes = ref<any[]>([])
const articles = ref<any[]>([])
const showAddSampleDialogVisible = ref(false)
const adding = ref(false)

const learnForm = reactive({
  style_name: '',
  text: ''
})

const extractForm = reactive({
  source_type: 'note',
  source_id: '',
  style_name: ''
})

const sampleForm = reactive({
  style_name: '',
  text: ''
})

const columns = [
  { colKey: 'name', title: '风格名称', width: '150' },
  { colKey: 'metadata', title: '来源', width: '150' },
  { colKey: 'sample_count', title: '样本数', width: '100' },
  { colKey: 'total_chars', title: '总字符数', width: '120' },
  { colKey: 'updated_at', title: '更新时间', width: '200' },
  { colKey: 'operations', title: '操作', width: '250' }
]

onMounted(() => {
  fetchStyles()
})

const fetchStyles = async () => {
  loading.value = true
  try {
    const response = await styleApi.getStyleList()
    if (response.data?.styles) {
      styles.value = response.data.styles as Style[]
    }
  } catch (error) {
    console.error('Failed to fetch styles:', error)
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
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '学习失败')
  } finally {
    learning.value = false
  }
}

const loadSources = async () => {
  try {
    const [notesRes, articlesRes] = await Promise.all([
      notesApi.listNotes(),
      articleApi.getArticleList()
    ])
    notes.value = notesRes.data?.notes || []
    articles.value = articlesRes.data?.articles || []
  } catch (error) {
    console.error('Failed to load sources:', error)
  }
}

const handleExtract = async () => {
  if (!extractForm.source_id || !extractForm.style_name) {
    MessagePlugin.warning('请选择来源并填写风格名称')
    return
  }

  extracting.value = true
  try {
    if (extractForm.source_type === 'note') {
      await styleApi.extractFromNote(extractForm.source_id, extractForm.style_name)
    } else {
      await styleApi.extractFromArticle(extractForm.source_id, extractForm.style_name)
    }
    MessagePlugin.success('风格提取成功')
    showExtractDialog.value = false
    extractForm.source_id = ''
    extractForm.style_name = ''
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '提取失败')
  } finally {
    extracting.value = false
  }
}

const viewStyle = async (name: string) => {
  try {
    const response = await styleApi.getStyleDetail(name)
    if (response.data) {
      MessagePlugin.success(`风格详情: ${JSON.stringify(response.data.features)}`)
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
  await loadSources()
  showExtractDialog.value = true
}
</script>

<style scoped>
.styles-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
