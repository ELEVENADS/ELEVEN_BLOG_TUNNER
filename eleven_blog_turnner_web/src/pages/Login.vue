<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <t-icon name="article" size="48px" />
        <h1>ELEVEN Blog Tuner</h1>
        <p>AI 博客生成助手</p>
      </div>

      <t-form ref="formRef" :data="formData" :rules="rules" @submit="handleSubmit">
        <t-form-item label="邮箱" name="email">
          <t-input v-model="formData.email" placeholder="请输入邮箱" size="large">
            <template #prefix-icon>
              <t-icon name="mail" />
            </template>
          </t-input>
        </t-form-item>

        <t-form-item label="密码" name="password">
          <t-input v-model="formData.password" type="password" placeholder="请输入密码" size="large" show-password>
            <template #prefix-icon>
              <t-icon name="lock-on" />
            </template>
          </t-input>
        </t-form-item>

        <t-form-item v-if="isRegister">
          <t-checkbox v-model="agreed">我已阅读并同意相关条款</t-checkbox>
        </t-form-item>

        <t-form-item>
          <t-button type="submit" theme="primary" size="large" block :loading="loading">
            {{ isRegister ? '注册' : '登录' }}
          </t-button>
        </t-form-item>
      </t-form>

      <div class="login-footer">
        <t-link @click="toggleMode">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </t-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const isRegister = ref(false)
const agreed = ref(false)

const formData = reactive({
  email: '',
  password: '',
  username: ''
})

const rules = {
  email: [{ required: true, message: '请输入邮箱', type: 'error' }],
  password: [{ required: true, message: '请输入密码', type: 'error' }]
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
}

const handleSubmit = async () => {
  const result = isRegister.value
    ? await authStore.register({ username: formData.email.split('@')[0], email: formData.email, password: formData.password })
    : await authStore.login({ email: formData.email, password: formData.password })

  if (result.success) {
    MessagePlugin.success(isRegister.value ? '注册成功' : '登录成功')
    router.push('/dashboard')
  } else {
    MessagePlugin.error(result.message)
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin: 16px 0 8px;
  font-size: 24px;
  color: #333;
}

.login-header p {
  color: #666;
  font-size: 14px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
}
</style>
