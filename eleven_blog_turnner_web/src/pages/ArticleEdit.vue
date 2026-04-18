<template>
    <t-card class="article-edit-card">
        <template #actions>
            <t-space>
                <t-button @click="handleCancel">取消</t-button>
                <t-button theme="primary" @click="handleSave" :loading="saving">
                    保存
                </t-button>
            </t-space>
        </template>
        
        <div class="editor-wrapper">
            <MarkdownEditor
                v-model="articleData"
                placeholder="开始编写你的文章..."
            />
        </div>
    </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { fileTreeApi } from '@/api/fileTree'
import MarkdownEditor from '@/components/MarkdownEditor.vue'

const route = useRoute()
const router = useRouter()

const articleId = ref<string | null>(null)
const categoryId = ref<string | null>(null)
const saving = ref(false)
const articleData = ref({ title: '', content: '' })

onMounted(async () => {
    articleId.value = (route.params.id as string) || null
    categoryId.value = (route.query.category_id as string) || null

    if (articleId.value) {
        await loadArticle()
    } else if (categoryId.value) {
        articleData.value.title = '新建文章'
    } else {
        articleData.value.title = '新建文章'
    }
})

const loadArticle = async () => {
    if (!articleId.value) return

    try {
        const article = await fileTreeApi.getArticleDetail(articleId.value)
        if (article) {
            articleData.value = {
                title: article.title || '',
                content: article.content || ''
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
            await fileTreeApi.updateArticle(articleId.value, {
                title: articleData.value.title,
                content: articleData.value.content
            })
            MessagePlugin.success('文章更新成功')
        } else {
            await fileTreeApi.createArticle({
                title: articleData.value.title,
                content: articleData.value.content,
                category_id: categoryId.value || undefined
            })
            MessagePlugin.success('文章创建成功')
        }

        router.back()
    } catch (error) {
        console.error('保存文章失败:', error)
        MessagePlugin.error('保存失败')
    } finally {
        saving.value = false
    }
}

const handleCancel = () => {
    router.back()
}
</script>

<style scoped>
.article-edit-card {
    height: 100%;
}

.editor-wrapper {
    height: calc(100vh - 160px);
}
</style>
