import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 编辑器状态 Store
 * 
 * 用于共享编辑器相关的状态，包括：
 * - 编辑器内容
 * - 选中的文本
 * - 选区位置
 */
export const useEditorStore = defineStore('editor', () => {
  // 编辑器完整内容
  const editorContent = ref('')
  
  // 选中的文本
  const selectedText = ref('')
  
  // 选区开始位置
  const selectionStart = ref<number | null>(null)
  
  // 选区结束位置
  const selectionEnd = ref<number | null>(null)
  
  // 是否有选中文本
  const hasSelection = computed(() => selectedText.value.length > 0)
  
  // 选中文本长度
  const selectionLength = computed(() => selectedText.value.length)

  /**
   * 设置编辑器内容
   */
  const setEditorContent = (content: string) => {
    editorContent.value = content
  }

  /**
   * 设置选中文本
   */
  const setSelectedText = (text: string) => {
    selectedText.value = text
  }

  /**
   * 设置选区位置
   */
  const setSelectionRange = (start: number | null, end: number | null) => {
    selectionStart.value = start
    selectionEnd.value = end
  }

  /**
   * 设置完整的选区信息
   */
  const setSelection = (text: string, start: number | null, end: number | null) => {
    selectedText.value = text
    selectionStart.value = start
    selectionEnd.value = end
  }

  /**
   * 清空选区
   */
  const clearSelection = () => {
    selectedText.value = ''
    selectionStart.value = null
    selectionEnd.value = null
  }

  /**
   * 重置所有状态
   */
  const reset = () => {
    editorContent.value = ''
    selectedText.value = ''
    selectionStart.value = null
    selectionEnd.value = null
  }

  return {
    // State
    editorContent,
    selectedText,
    selectionStart,
    selectionEnd,
    
    // Getters
    hasSelection,
    selectionLength,
    
    // Actions
    setEditorContent,
    setSelectedText,
    setSelectionRange,
    setSelection,
    clearSelection,
    reset
  }
})
