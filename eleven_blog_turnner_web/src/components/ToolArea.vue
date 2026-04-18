<template>
  <t-card title="工具区" :bordered="false" :header-style="{ padding: '12px' }">
    <div class="tool-area-content">
      <t-button theme="primary" @click="extractStyle">
        <template #icon>
          <t-icon name="palette" />
        </template>
        提取风格
      </t-button>
      <t-button theme="default" @click="generateSummary">
        <template #icon>
          <t-icon name="document" />
        </template>
        生成总结
      </t-button>
      <div class="tool-result" v-if="toolResult">
        <h4>结果:</h4>
        <p>{{ toolResult }}</p>
      </div>
    </div>
  </t-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

// 工具区逻辑
const toolResult = ref('')

const extractStyle = () => {
  toolResult.value = '风格提取中...'
  // 模拟风格提取过程
  setTimeout(() => {
    toolResult.value = '已提取风格：专业、简洁、有条理'
    MessagePlugin.success('风格提取成功')
  }, 1000)
}

const generateSummary = () => {
  toolResult.value = '总结生成中...'
  // 模拟总结生成过程
  setTimeout(() => {
    toolResult.value = '文章总结：本文主要介绍了如何使用AI工具生成具有个人风格的博客文章，包括风格提取、内容生成等步骤。'
    MessagePlugin.success('总结生成成功')
  }, 1000)
}
</script>

<style scoped>
.tool-area-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-result {
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
}

.tool-result h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: bold;
}

.tool-result p {
  margin: 0;
  line-height: 1.4;
}
</style>