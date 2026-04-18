<template>
  <t-card title="文件树" :bordered="false" :header-style="{ padding: '12px' }">
    <div class="file-tree-content">
      <t-tree
        :data="fileTreeData"
        :expanded="expandedNodes"
        @expand="handleTreeExpand"
        @select="handleTreeSelect"
      />
    </div>
  </t-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 文件树数据
const fileTreeData = ref([
  {
    label: '笔记',
    value: 'notes',
    children: [
      { label: '个人笔记1', value: 'note1' },
      { label: '个人笔记2', value: 'note2' },
      { label: '个人笔记3', value: 'note3' }
    ]
  },
  {
    label: '文章',
    value: 'articles',
    children: [
      { label: '已发布文章', value: 'published' },
      { label: '草稿', value: 'drafts' },
      { label: '待审核', value: 'reviewing' }
    ]
  },
  {
    label: '风格',
    value: 'styles',
    children: [
      { label: '专业风格', value: 'professional' },
      { label: '轻松风格', value: 'casual' },
      { label: '学术风格', value: 'academic' }
    ]
  }
])

const expandedNodes = ref(['notes', 'articles', 'styles'])

const handleTreeExpand = (expanded: string[], node: any) => {
  expandedNodes.value = expanded
}

const handleTreeSelect = (selected: string[], node: any) => {
  console.log('Selected node:', node)
  // 可以根据选择的节点进行相应的操作
}
</script>

<style scoped>
.file-tree-content {
  margin-top: 8px;
}
</style>