<template>
  <div class="settings-page">
    <t-card title="系统设置" bordered>
      <t-tabs v-model:value="activeTab">
        <t-tab-panel value="llm" label="LLM 设置">
          <t-form :data="llmConfig" label-width="120px">
            <t-form-item label="提供商">
              <t-select v-model="llmConfig.provider" placeholder="请选择 LLM 提供商">
                <t-option value="openai" label="OpenAI" />
                <t-option value="claude" label="Claude" />
                <t-option value="local" label="本地模型" />
              </t-select>
            </t-form-item>
            <t-form-item label="API URL">
              <t-input v-model="llmConfig.apiUrl" placeholder="请输入 API URL" />
            </t-form-item>
            <t-form-item label="API Key">
              <t-input v-model="llmConfig.apiKey" type="password" placeholder="请输入 API Key" show-password />
            </t-form-item>
            <t-form-item label="模型名称">
              <t-input v-model="llmConfig.model" placeholder="请输入模型名称" />
            </t-form-item>
            <t-form-item label="Temperature">
              <t-slider v-model="llmConfig.temperature" :min="0" :max="1" :step="0.1" />
              <span>{{ llmConfig.temperature }}</span>
            </t-form-item>
            <t-form-item label="Max Tokens">
              <t-input-number v-model="llmConfig.maxTokens" :min="100" :max="10000" :step="100" />
            </t-form-item>
            <t-form-item>
              <t-button theme="primary" @click="saveLlmConfig">保存设置</t-button>
            </t-form-item>
          </t-form>
        </t-tab-panel>

        <t-tab-panel value="rag" label="RAG 设置">
          <t-form :data="ragConfig" label-width="120px">
            <t-form-item label="Embedding 模型">
              <t-input v-model="ragConfig.embeddingModel" placeholder="请输入 Embedding 模型" />
            </t-form-item>
            <t-form-item label="分块大小">
              <t-input-number v-model="ragConfig.chunkSize" :min="100" :max="2000" :step="50" />
            </t-form-item>
            <t-form-item label="分块重叠">
              <t-input-number v-model="ragConfig.chunkOverlap" :min="0" :max="500" :step="10" />
            </t-form-item>
            <t-form-item label="Top K">
              <t-input-number v-model="ragConfig.topK" :min="1" :max="20" />
            </t-form-item>
            <t-form-item>
              <t-button theme="primary" @click="saveRagConfig">保存设置</t-button>
            </t-form-item>
          </t-form>
        </t-tab-panel>

        <t-tab-panel value="system" label="系统设置">
          <t-form :data="systemConfig" label-width="120px">
            <t-form-item label="日志级别">
              <t-select v-model="systemConfig.logLevel">
                <t-option value="DEBUG" label="DEBUG" />
                <t-option value="INFO" label="INFO" />
                <t-option value="WARNING" label="WARNING" />
                <t-option value="ERROR" label="ERROR" />
              </t-select>
            </t-form-item>
            <t-form-item>
              <t-button theme="primary" @click="saveSystemConfig">保存设置</t-button>
            </t-form-item>
          </t-form>
        </t-tab-panel>
      </t-tabs>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import apiClient from '@/utils/api'

const activeTab = ref('llm')

const llmConfig = reactive({
  provider: 'openai',
  apiUrl: '',
  apiKey: '',
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 4096
})

const ragConfig = reactive({
  embeddingModel: 'text-embedding-3-small',
  chunkSize: 512,
  chunkOverlap: 50,
  topK: 5
})

const systemConfig = reactive({
  logLevel: 'INFO'
})

const saveLlmConfig = async () => {
  try {
    await apiClient.post('/config/settings', llmConfig)
    MessagePlugin.success('LLM 设置已保存')
  } catch (error) {
    MessagePlugin.error('保存失败')
  }
}

const saveRagConfig = async () => {
  try {
    await apiClient.post('/config/settings', ragConfig)
    MessagePlugin.success('RAG 设置已保存')
  } catch (error) {
    MessagePlugin.error('保存失败')
  }
}

const saveSystemConfig = async () => {
  try {
    await apiClient.post('/config/settings', systemConfig)
    MessagePlugin.success('系统设置已保存')
  } catch (error) {
    MessagePlugin.error('保存失败')
  }
}
</script>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
}
</style>