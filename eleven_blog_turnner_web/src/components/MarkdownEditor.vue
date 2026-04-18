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
                    v-model="content"
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
import { ref, watch } from 'vue'
import { Editor, Viewer } from '@bytemd/vue-next'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'

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

const plugins = [gfm(), highlight()]
const title = ref(props.modelValue.title)
const content = ref(props.modelValue.content)

watch(title, (newTitle) => {
    emit('update:modelValue', { title: newTitle, content: content.value })
})

watch(content, (newContent) => {
    emit('update:modelValue', { title: title.value, content: newContent })
})

watch(() => props.modelValue, (newVal) => {
    title.value = newVal.title
    content.value = newVal.content
}, { deep: true })

const handleChange = (value: string) => {
    emit('change', { title: title.value, content: value })
}
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
