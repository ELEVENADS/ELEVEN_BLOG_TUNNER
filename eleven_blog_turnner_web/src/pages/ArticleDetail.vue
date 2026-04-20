<template>
  <div class="article-detail">
    <t-card v-if="article" bordered>
      <template #title>
        <div class="article-header">
          <h2>{{ article.title }}</h2>
          <t-tag :theme="getStatusTheme(article.status)">
            {{ getStatusText(article.status) }}
          </t-tag>
        </div>
      </template>
      
      <template #actions>
        <t-space>
          <t-button theme="default" @click="handleBack">返回</t-button>
          <t-button theme="primary" @click="handleEdit">编辑</t-button>
          <t-button v-if="article.status === 'draft'" theme="warning" @click="submitReview">
            提交审核
          </t-button>
          <t-button v-if="article.status === 'approved'" theme="success" @click="publishArticle">
            发布
          </t-button>
        </t-space>
      </template>

      <div class="article-meta">
        <t-space>
          <span>主题: {{ article.topic || '-' }}</span>
          <span>风格: {{ article.style_name || '-' }}</span>
          <span>字数: {{ article.word_count || 0 }}</span>
          <span v-if="article.quality_score">质量分: {{ article.quality_score }}/100</span>
          <span>版本: v{{ article.version || 1 }}</span>
        </t-space>
      </div>

      <t-divider />

      <!-- 预览模式 -->
      <div v-if="!editing" class="article-content-preview">
        <div class="markdown-body" v-html="renderedContent"></div>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="article-edit-mode">
        <MarkdownEditor
          v-model="editData"
          placeholder="编辑文章内容..."
        />
        <div class="edit-actions">
          <t-space>
            <t-button theme="primary" @click="handleSave" :loading="saving">保存修改</t-button>
            <t-button theme="default" @click="cancelEdit">取消</t-button>
          </t-space>
        </div>
      </div>

      <t-divider />

      <!-- 版本历史 -->
      <div class="version-history">
        <h3>版本历史</h3>
        <t-timeline v-if="versions.length > 0">
          <t-timeline-item v-for="version in versions" :key="version.version">
            <div class="version-item">
              <span class="version-number">版本 {{ version.version }}</span>
              <span class="version-time">{{ formatTime(version.created_at) }}</span>
              <span v-if="version.reason" class="version-reason">{{ version.reason }}</span>
              <t-link theme="primary" @click="restoreVersion(version.version)">恢复此版本</t-link>
            </div>
          </t-timeline-item>
        </t-timeline>
        <t-empty v-else description="暂无版本历史" />
      </div>
    </t-card>

    <t-card v-else bordered>
      <t-empty description="文章不存在或加载中" />
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { articleApi, type Article } from '@/api/article'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import { marked } from 'marked'

const router = useRouter()
const route = useRoute()

const article = ref<Article | null>(null)
const editing = ref(false)
const saving = ref(false)
const versions = ref<Array<{version: number; created_at: number; reason?: string}>>([])

const editData = reactive({
  title: '',
  content: ''
})

const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  return marked.parse(article.value.content, { breaks: true })
})

onMounted(async () => {
  const id = route.params.id as string
  if (id) {
    await loadArticle(id)
    await loadVersions(id)
  }
})

const loadArticle = async (id: string) => {
  try {
    const response = await articleApi.getArticleDetail(id)
    if (response.data) {
      article.value = response.data
      editData.title = response.data.title
      editData.content = response.data.content
    }
  } catch (error) {
    console.error('Failed to fetch article:', error)
    MessagePlugin.error('加载文章失败')
  }
}

const loadVersions = async (id: string) => {
  try {
    const response = await articleApi.getArticleVersions(id)
    if (response.data?.versions) {
      versions.value = response.data.versions
    }
  } catch (error) {
    console.error('Failed to fetch versions:', error)
  }
}

const getStatusTheme = (status: string) => {
  const themes: Record<string, any> = {
    draft: 'default',
    generating: 'primary',
    reviewing: 'warning',
    approved: 'success',
    rejected: 'danger',
    published: 'success'
  }
  return themes[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    draft: '草稿',
    generating: '生成中',
    reviewing: '审核中',
    approved: '已通过',
    rejected: '已拒绝',
    published: '已发布'
  }
  return texts[status] || status
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString()
}

const handleEdit = () => {
  editing.value = true
}

const cancelEdit = () => {
  editing.value = false
  if (article.value) {
    editData.title = article.value.title
    editData.content = article.value.content
  }
}

const handleSave = async () => {
  if (!article.value) return
  
  saving.value = true
  try {
    await articleApi.updateArticle(article.value.id, editData.content, '手动编辑')
    MessagePlugin.success('保存成功')
    await loadArticle(article.value.id)
    await loadVersions(article.value.id)
    editing.value = false
  } catch (error) {
    MessagePlugin.error('保存失败')
  } finally {
    saving.value = false
  }
}

const submitReview = async () => {
  if (!article.value) return
  try {
    await articleApi.submitReview(article.value.id)
    MessagePlugin.success('提交审核成功')
    if (article.value) {
      article.value.status = 'reviewing'
    }
  } catch (error) {
    MessagePlugin.error('提交审核失败')
  }
}

const publishArticle = async () => {
  if (!article.value) return
  try {
    await articleApi.approveArticle(article.value.id)
    MessagePlugin.success('发布成功')
    if (article.value) {
      article.value.status = 'published'
    }
  } catch (error) {
    MessagePlugin.error('发布失败')
  }
}

const restoreVersion = async (version: number) => {
  if (!article.value) return
  try {
    await articleApi.restoreVersion(article.value.id, version)
    MessagePlugin.success(`已恢复到版本 ${version}`)
    await loadArticle(article.value.id)
    await loadVersions(article.value.id)
  } catch (error) {
    MessagePlugin.error('恢复失败')
  }
}

const handleBack = () => {
  router.push('/articles')
}
</script>

<style scoped>
.article-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.article-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.article-header h2 {
  margin: 0;
  font-size: 20px;
}

.article-meta {
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.article-content-preview {
  min-height: 300px;
  padding: 20px 0;
}

.article-edit-mode {
  min-height: 500px;
}

.edit-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e7e7e7;
}

.version-history {
  margin-top: 24px;
}

.version-history h3 {
  margin-bottom: 16px;
  font-size: 16px;
}

.version-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.version-number {
  font-weight: 600;
}

.version-time {
  color: #999;
  font-size: 12px;
}

.version-reason {
  color: #666;
  font-size: 13px;
}

.markdown-body {
  line-height: 1.8;
  font-size: 16px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(p) {
  margin-bottom: 16px;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-bottom: 16px;
  padding-left: 24px;
}

.markdown-body :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

.markdown-body :deep(pre) {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin-bottom: 16px;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #ddd;
  padding-left: 16px;
  margin-left: 0;
  color: #666;
}
</style>
