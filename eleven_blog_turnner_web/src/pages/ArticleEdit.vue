<template>
  <div class="article-edit-page">
    <t-card bordered>
      <template #title>
        <div class="edit-header">
          <t-input
            v-model="articleData.title"
            placeholder="请输入文章标题"
            size="large"
            class="title-input"
          />
        </div>
      </template>
      
      <template #actions>
        <t-space>
          <t-button theme="default" @click="handleCancel">取消</t-button>
          <t-button theme="primary" @click="handleSave" :loading="saving">
            保存
          </t-button>
          <t-button v-if="articleId" theme="success" @click="handlePolish" :loading="polishing">
            <template #icon>
              <t-icon name="brush" />
            </template>
            AI 润色
          </t-button>
        </t-space>
      </template>
      
      <div class="editor-container">
        <MarkdownEditor
          v-model="articleData"
          placeholder="开始编写你的文章..."
        />
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { articleApi } from '@/api/article'
import MarkdownEditor from '@/components/MarkdownEditor.vue'

const route = useRoute()
const router = useRouter()

const articleId = ref<string | null>(null)
const saving = ref(false)
const polishing = ref(false)
const articleData = ref({ title: '', content: '' })

onMounted(async () => {
  articleId.value = (route.params.id as string) || null

  if (articleId.value) {
    await loadArticle()
  } else {
    articleData.value.title = '新建文章'
  }
})

const loadArticle = async () => {
  if (!articleId.value) return

  try {
    const response = await articleApi.getArticleDetail(articleId.value)
    if (response.data) {
      articleData.value = {
        title: response.data.title || '',
        content: response.data.content || ''
      }
    }
  } catch (error) {
    console.error('加载文章失败:', error)
    MessagePlugin.error('加载文章失败')
  }
}

const handleSave = async () => {
  if (!articleData.value.title) {
    MessagePlugin.warning('请输入标题')
    return
  }

  saving.value = true
  try {
    if (articleId.value) {
      await articleApi.updateArticle(articleId.value, {
        content: articleData.value.content
      })
      MessagePlugin.success('文章更新成功')
    } else {
      const response = await articleApi.generateArticle({
        topic: articleData.value.title,
        metadata: {
          title: articleData.value.title,
          content: articleData.value.content
        }
      })
      if (response.data?.task_id) {
        articleId.value = response.data.task_id
        MessagePlugin.success('文章创建成功')
      }
    }
  } catch (error) {
    console.error('保存文章失败:', error)
    MessagePlugin.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handlePolish = async () => {
  if (!articleId.value) {
    MessagePlugin.warning('请先保存文章')
    return
  }

  polishing.value = true
  try {
    await articleApi.polishArticle(articleId.value)
    MessagePlugin.success('文章润色成功')
    // 重新加载文章
    await loadArticle()
  } catch (error) {
    console.error('润色文章失败:', error)
    MessagePlugin.error('润色失败')
  } finally {
    polishing.value = false
  }
}

const handleCancel = () => {
  router.push('/articles')
}
</script>

<style scoped>
.article-edit-page {
  height: 100%;
}

.edit-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-input {
  width: 400px;
}

.editor-container {
  height: calc(100vh - 200px);
  min-height: 500px;
}
</style>
