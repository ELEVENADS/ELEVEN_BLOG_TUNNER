<template>
  <div class="articles-page">
    <t-card title="文章管理" bordered>
      <template #actions>
        <t-button theme="primary" @click="$router.push('/generate')">
          <template #icon>
            <t-icon name="add" />
          </template>
          生成新文章
        </t-button>
      </template>

      <div class="filter-row">
        <t-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 200px">
          <t-option value="" label="全部状态" />
          <t-option value="draft" label="草稿" />
          <t-option value="generating" label="生成中" />
          <t-option value="reviewing" label="审核中" />
          <t-option value="approved" label="已通过" />
          <t-option value="rejected" label="已拒绝" />
          <t-option value="published" label="已发布" />
        </t-select>
      </div>

      <t-table :data="articles" :columns="columns" row-key="id" hover :loading="loading">
        <template #status="{ row }">
          <t-tag :theme="getStatusTheme(row.status)">
            {{ getStatusText(row.status) }}
          </t-tag>
        </template>
        <template #word_count="{ row }">
          {{ row.word_count || 0 }} 字
        </template>
        <template #quality_score="{ row }">
          {{ row.quality_score ? `${row.quality_score}/100` : '-' }}
        </template>
        <template #operations="{ row }">
          <t-space>
            <t-link @click="viewArticle(row.id)">查看</t-link>
            <t-link v-if="row.status === 'approved'" @click="publishArticle(row.id)">发布</t-link>
            <t-link v-if="row.status === 'draft'" @click="deleteArticle(row.id)">删除</t-link>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { articleApi, type Article } from '@/api/article'

const router = useRouter()

const loading = ref(false)
const articles = ref<Article[]>([])
const filterStatus = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const columns = [
  { colKey: 'title', title: '标题', width: '200' },
  { colKey: 'topic', title: '主题', width: '150' },
  { colKey: 'style_name', title: '风格', width: '100' },
  { colKey: 'status', title: '状态', width: '100' },
  { colKey: 'word_count', title: '字数', width: '100' },
  { colKey: 'quality_score', title: '质量分', width: '100' },
  { colKey: 'created_at', title: '创建时间', width: '180' },
  { colKey: 'operations', title: '操作', width: '150' }
]

onMounted(() => {
  fetchArticles()
})

watch(filterStatus, () => {
  pagination.page = 1
  fetchArticles()
})

const fetchArticles = async () => {
  loading.value = true
  try {
    const response = await articleApi.getArticleList({
      status: filterStatus.value || undefined,
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    })
    if (response.data?.articles) {
      articles.value = response.data.articles
      pagination.total = response.data.total
    }
  } catch (error) {
    console.error('Failed to fetch articles:', error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (pageInfo: { current: number; pageSize: number }) => {
  pagination.page = pageInfo.current
  pagination.pageSize = pageInfo.pageSize
  fetchArticles()
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

const viewArticle = (id: string) => {
  router.push(`/articles/${id}`)
}

const publishArticle = async (id: string) => {
  try {
    await articleApi.approveArticle(id)
    MessagePlugin.success('文章已发布')
    fetchArticles()
  } catch (error) {
    MessagePlugin.error('发布失败')
  }
}

const deleteArticle = async (id: string) => {
  try {
    await articleApi.deleteArticle(id)
    MessagePlugin.success('删除成功')
    fetchArticles()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}
</script>

<style scoped>
.articles-page {
  max-width: 1400px;
  margin: 0 auto;
}

.filter-row {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>