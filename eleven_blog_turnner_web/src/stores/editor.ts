import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 插入模式类型
 */
export type InsertMode = 'append' | 'replace' | 'insert_after_selection'

/**
 * 编辑器状态 Store
 *
 * 用于共享编辑器相关的状态，包括：
 * - 编辑器内容
 * - 选中的文本
 * - 选区位置
 * - 待插入的内容
 * - 插入模式
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

  // 待插入的内容（用于 ToolArea 向编辑器传递内容）
  const pendingInsertContent = ref('')

  // 是否需要插入内容的标志
  const shouldInsertContent = ref(false)

  // 插入模式
  const insertMode = ref<InsertMode>('append')

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
   * 请求插入内容（在末尾追加）
   */
  const requestInsertContent = (content: string) => {
    pendingInsertContent.value = content
    insertMode.value = 'append'
    shouldInsertContent.value = true
  }

  /**
   * 请求替换选中的内容
   */
  const requestReplaceContent = (content: string) => {
    pendingInsertContent.value = content
    insertMode.value = 'replace'
    shouldInsertContent.value = true
  }

  /**
   * 请求在选区后插入内容
   */
  const requestInsertAfterSelection = (content: string) => {
    pendingInsertContent.value = content
    insertMode.value = 'insert_after_selection'
    shouldInsertContent.value = true
  }

  /**
   * 确认内容已插入
   */
  const confirmContentInserted = () => {
    pendingInsertContent.value = ''
    shouldInsertContent.value = false
    insertMode.value = 'append'
  }

  /**
   * 重置所有状态
   */
  const reset = () => {
    editorContent.value = ''
    selectedText.value = ''
    selectionStart.value = null
    selectionEnd.value = null
    pendingInsertContent.value = ''
    shouldInsertContent.value = false
  }

  return {
    // State
    editorContent,
    selectedText,
    selectionStart,
    selectionEnd,
    pendingInsertContent,
    shouldInsertContent,
    insertMode,

    // Getters
    hasSelection,
    selectionLength,

    // Actions
    setEditorContent,
    setSelectedText,
    setSelectionRange,
    setSelection,
    clearSelection,
    requestInsertContent,
    requestReplaceContent,
    requestInsertAfterSelection,
    confirmContentInserted,
    reset
  }
})
