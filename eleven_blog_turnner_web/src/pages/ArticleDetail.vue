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
          <t-button v-if="article.status === 'draft'" theme="primary" @click="submitReview">提交审核</t-button>
          <t-button v-if="article.status === 'approved'" theme="success" @click="publishArticle">发布</t-button>
          <t-button theme="default" @click="handleBack">返回</t-button>
        </t-space>
      </template>

      <div class="article-meta">
        <t-space>
          <span>主题: {{ article.topic }}</span>
          <span>风格: {{ article.style_name }}</span>
          <span>字数: {{ article.word_count }}</span>
          <span v-if="article.quality_score">质量分: {{ article.quality_score }}/100</span>
        </t-space>
      </div>

      <t-divider />

      <div class="article-content">
        <div v-html="renderedContent"></div>
      </div>

      <t-divider />

      <div class="article-actions">
        <t-form v-if="editing" :data="editForm" @submit="handleSave">
          <t-form-item label="文章内容">
            <t-textarea
              v-model="editForm.content"
              :autosize="{ minRows: 10, maxRows: 20 }"
            />
          </t-form-item>
          <t-form-item label="修改原因">
            <t-input v-model="editForm.reason" placeholder="请输入修改原因" />
          </t-form-item>
          <t-form-item>
            <t-space>
              <t-button type="submit" theme="primary">保存</t-button>
              <t-button @click="editing = false">取消</t-button>
            </t-space>
          </t-form-item>
        </t-form>
        <t-button v-else theme="default" @click="startEditing">
          <t-icon name="edit" /> 编辑文章
        </t-button>
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

const router = useRouter()
const route = useRoute()

const article = ref<Article | null>(null)
const editing = ref(false)

const editForm = reactive({
  content: '',
  reason: ''
})

const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  return article.value.content.replace(/\n/g, '<br>')
})

onMounted(async () => {
  const id = route.params.id as string
  if (id) {
    try {
      const response = await articleApi.getArticleDetail(id)
      if (response.data) {
        article.value = response.data
      }
    } catch (error) {
      console.error('Failed to fetch article:', error)
    }
  }
})

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

const startEditing = () => {
  if (article.value) {
    editForm.content = article.value.content
    editing.value = true
  }
}

const handleSave = async () => {
  if (!article.value) return
  try {
    await articleApi.updateArticle(article.value.id, editForm)
    MessagePlugin.success('保存成功')
    if (article.value) {
      article.value.content = editForm.content
    }
    editing.value = false
  } catch (error) {
    MessagePlugin.error('保存失败')
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

const handleBack = () => {
  router.push('/articles')
}
</script>

<style scoped>
.article-detail {
  max-width: 1000px;
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
}

.article-content {
  line-height: 1.8;
  font-size: 16px;
  padding: 20px 0;
}
</style>