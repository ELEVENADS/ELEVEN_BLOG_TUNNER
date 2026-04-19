<template>
    <t-card class="note-edit-card">
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
                v-model="noteData"
                placeholder="开始编写你的笔记..."
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

const noteId = ref<string | null>(null)
const categoryId = ref<string | null>(null)
const saving = ref(false)
const noteData = ref({ title: '', content: '' })

onMounted(async () => {
    noteId.value = (route.params.id as string) || null
    categoryId.value = (route.query.category_id as string) || null

    if (noteId.value) {
        await loadNote()
    } else if (categoryId.value) {
        noteData.value.title = '新建笔记'
    } else {
        noteData.value.title = '新建笔记'
    }
})

const loadNote = async () => {
    if (!noteId.value) return

    try {
        const note = await fileTreeApi.getNoteDetail(noteId.value)
        if (note) {
            noteData.value = {
                title: note.title || '',
                content: note.content || ''
            }
        }
    } catch (error) {
        console.error('加载笔记失败:', error)
        MessagePlugin.error('加载笔记失败')
    }
}

const handleSave = async () => {
    console.log('[NoteEdit] 保存前 noteData:', JSON.parse(JSON.stringify(noteData.value)))

    if (!noteData.value.title) {
        MessagePlugin.warning('请输入标题')
        return
    }

    saving.value = true
    try {
        const payload = noteId.value
            ? { title: noteData.value.title, content: noteData.value.content }
            : { title: noteData.value.title, content: noteData.value.content, category_id: categoryId.value || undefined }

        console.log('[NoteEdit] 发送给接口的 payload:', JSON.parse(JSON.stringify(payload)))

        if (noteId.value) {
            await fileTreeApi.updateNote(noteId.value, {
                title: noteData.value.title,
                content: noteData.value.content
            })
            MessagePlugin.success('笔记更新成功')
        } else {
            await fileTreeApi.createNote({
                title: noteData.value.title,
                content: noteData.value.content,
                category_id: categoryId.value || undefined
            })
            MessagePlugin.success('笔记创建成功')
        }

        router.back()
    } catch (error) {
        console.error('[NoteEdit] 保存笔记失败:', error)
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
.note-edit-card {
    height: 100%;
}

.editor-wrapper {
    height: calc(100vh - 160px);
}
</style>
