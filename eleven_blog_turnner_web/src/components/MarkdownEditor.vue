<template>
    <div class="markdown-editor">
        <div class="editor-header">
            <t-input
                v-model="title"
                placeholder="请输入标题"
                size="large"
                class="title-input"
            />
        </div>
        <div class="editor-content">
            <div class="editor-pane">
                <div class="pane-header">编辑</div>
                <Editor
                    :value="content"
                    :plugins="plugins"
                    :placeholder="placeholder"
                    @change="handleChange"
                />
            </div>
            <div class="preview-pane">
                <div class="pane-header">预览</div>
                <Viewer
                    :value="content"
                    :plugins="plugins"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Editor, Viewer } from '@bytemd/vue-next'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'
import { useEditorStore } from '@/stores/editor'

import 'bytemd/dist/index.css'
import 'highlight.js/styles/github.css'

interface Props {
    modelValue: {
        title: string
        content: string
    }
    placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
    placeholder: '请输入内容...'
})

const emit = defineEmits(['update:modelValue', 'change'])

const editorStore = useEditorStore()
const plugins = [gfm(), highlight()]
const title = ref(props.modelValue.title)
const content = ref(props.modelValue.content)
const editorRef = ref<HTMLElement | null>(null)

watch(title, (newTitle) => {
    console.log('[MarkdownEditor] title 变化:', newTitle, '当前 content:', content.value)
    emit('update:modelValue', { title: newTitle, content: content.value })
})

watch(content, (newContent) => {
    console.log('[MarkdownEditor] content 变化:', newContent?.substring(0, 50), '当前 title:', title.value)
    emit('update:modelValue', { title: title.value, content: newContent })
    // 更新 store 中的编辑器内容
    editorStore.setEditorContent(newContent)
})

watch(() => props.modelValue, (newVal) => {
    console.log('[MarkdownEditor] props.modelValue 变化:', newVal)
    title.value = newVal.title
    content.value = newVal.content
    // 更新 store 中的编辑器内容
    editorStore.setEditorContent(newVal.content)
}, { deep: true })

const handleChange = (value: string) => {
    console.log('[MarkdownEditor] @change 触发:', value?.substring(0, 50))
    content.value = value
    emit('update:modelValue', { title: title.value, content: value })
    // 更新 store 中的编辑器内容
    editorStore.setEditorContent(value)
}

// 监听选区变化
const handleSelectionChange = () => {
    const selection = window.getSelection()
    if (selection && selection.toString()) {
        const selectedText = selection.toString()
        // 获取选区在编辑器内容中的位置
        const range = selection.getRangeAt(0)
        const preSelectionRange = range.cloneRange()
        preSelectionRange.selectNodeContents(document.body)
        preSelectionRange.setEnd(range.startContainer, range.startOffset)
        const start = preSelectionRange.toString().length
        const end = start + selectedText.length
        
        editorStore.setSelection(selectedText, start, end)
        console.log('[MarkdownEditor] 选区变化:', selectedText.substring(0, 50))
    } else {
        editorStore.clearSelection()
    }
}

// 监听鼠标抬起事件（选区通常在鼠标抬起时确定）
const handleMouseUp = () => {
    setTimeout(() => {
        const selection = window.getSelection()
        if (selection && selection.toString()) {
            const selectedText = selection.toString()
            editorStore.setSelectedText(selectedText)
            console.log('[MarkdownEditor] 鼠标抬起选区:', selectedText.substring(0, 50))
        }
    }, 0)
}

onMounted(() => {
    // 初始化编辑器内容到 store
    editorStore.setEditorContent(content.value)
    
    // 监听选区变化
    document.addEventListener('selectionchange', handleSelectionChange)
    document.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
    document.removeEventListener('selectionchange', handleSelectionChange)
    document.removeEventListener('mouseup', handleMouseUp)
    // 清理 store
    editorStore.reset()
})
</script>

<style scoped>
.markdown-editor {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.editor-header {
    padding: 16px 0;
    border-bottom: 1px solid #e7e7e7;
}

.title-input {
    font-size: 18px;
}

.editor-content {
    flex: 1;
    display: flex;
    overflow: hidden;
    min-height: 400px;
}

.editor-pane,
.preview-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #e7e7e7;
    overflow: hidden;
}

.preview-pane {
    border-right: none;
}

.pane-header {
    padding: 12px 16px;
    background: #f9f9f9;
    border-bottom: 1px solid #e7e7e7;
    font-weight: 600;
    color: #666;
}

:deep(.bytemd) {
    flex: 1;
    height: calc(100% - 50px);
    border: none;
}

:deep(.bytemd-toolbar) {
    border-bottom: 1px solid #e7e7e7;
}

:deep(.bytemd-preview) {
    padding: 16px;
}

:deep(.markdown-body) {
    font-size: 15px;
    line-height: 1.8;
}
</style>
