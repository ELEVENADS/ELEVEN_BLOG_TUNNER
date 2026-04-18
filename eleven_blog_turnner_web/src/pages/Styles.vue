<template>
  <div class="styles-page">
    <t-card title="风格管理" bordered>
      <template #actions>
        <t-button theme="primary" @click="showLearnDialog = true">
          <template #icon>
            <t-icon name="add" />
          </template>
          学习新风格
        </t-button>
      </template>

      <t-table :data="styles" :columns="columns" row-key="name" hover :loading="loading">
        <template #features="{ row }">
          <t-tooltip content="词汇多样性">
            <t-progress :percentage="Math.round(row.features.vocabulary_diversity * 100)" />
          </t-tooltip>
        </template>
        <template #operations="{ row }">
          <t-space>
            <t-link @click="viewStyle(row.name)">查看</t-link>
            <t-link theme="danger" @click="deleteStyle(row.name)">删除</t-link>
          </t-space>
        </template>
      </t-table>
    </t-card>

    <t-dialog v-model:visible="showLearnDialog" header="学习新风格" :footer="false" width="600px">
      <t-form :data="learnForm" @submit="handleLearn">
        <t-form-item label="风格名称" name="style_name">
          <t-input v-model="learnForm.style_name" placeholder="请输入风格名称" />
        </t-form-item>
        <t-form-item label="示例文本" name="text">
          <t-textarea
            v-model="learnForm.text"
            placeholder="请粘贴您的写作样本，段落越多学习效果越好"
            :autosize="{ minRows: 5, maxRows: 10 }"
          />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button type="submit" theme="primary" :loading="learning">开始学习</t-button>
            <t-button @click="showLearnDialog = false">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { styleApi, type Style } from '@/api/style'

const loading = ref(false)
const styles = ref<Style[]>([])
const showLearnDialog = ref(false)
const learning = ref(false)

const learnForm = reactive({
  style_name: '',
  text: ''
})

const columns = [
  { colKey: 'name', title: '风格名称', width: '150' },
  { colKey: 'features', title: '词汇多样性', width: '200' },
  { colKey: 'metadata', title: '来源', width: '150' },
  { colKey: 'operations', title: '操作', width: '150' }
]

onMounted(() => {
  fetchStyles()
})

const fetchStyles = async () => {
  loading.value = true
  try {
    const response = await styleApi.getStyleList()
    if (response.data?.styles) {
      const styleDetails = await Promise.all(
        response.data.styles.map((name: string) => styleApi.getStyleDetail(name))
      )
      styles.value = styleDetails.map(res => res.data).filter(Boolean)
    }
  } catch (error) {
    console.error('Failed to fetch styles:', error)
  } finally {
    loading.value = false
  }
}

const handleLearn = async () => {
  if (!learnForm.style_name || !learnForm.text) {
    MessagePlugin.warning('请填写完整信息')
    return
  }

  learning.value = true
  try {
    await styleApi.learnStyle(learnForm)
    MessagePlugin.success('风格学习成功')
    showLearnDialog.value = false
    learnForm.style_name = ''
    learnForm.text = ''
    fetchStyles()
  } catch (error: any) {
    MessagePlugin.error(error.response?.data?.message || '学习失败')
  } finally {
    learning.value = false
  }
}

const viewStyle = async (name: string) => {
  try {
    const response = await styleApi.getStyleDetail(name)
    if (response.data) {
      MessagePlugin.success(`风格详情: ${JSON.stringify(response.data.features)}`)
    }
  } catch (error) {
    MessagePlugin.error('获取风格详情失败')
  }
}

const deleteStyle = async (name: string) => {
  try {
    await styleApi.deleteStyle(name)
    MessagePlugin.success('删除成功')
    fetchStyles()
  } catch (error) {
    MessagePlugin.error('删除失败')
  }
}
</script>

<style scoped>
.styles-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>