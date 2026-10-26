<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { post_login } from '@/api/login'
import { warmupAgent } from '@/api/chat'

const router = useRouter()
const loading = ref(false)
interface LoginForm {
  username: string
  password: string
}
const form = ref<LoginForm>({
  username: '',
  password: '',
})

async function onLogin() {
  if (!form.value.username.trim() || !form.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    const res = await post_login({
      username: form.value.username,
      password: form.value.password,
    })
    const payload = res.data?.data
    if (payload?.token) {
      localStorage.setItem('token', payload.token)
      localStorage.setItem('userInfo', JSON.stringify(payload.userInfo ?? {}))
      // 后台预热 Agent，不阻塞进首页；失败忽略
      warmupAgent().catch(() => {})
    }
    ElMessage.success(res.data?.message || '登录成功')
    await router.push('/project')
  } catch (e) {
    console.error(e)
    const err = e as { response?: { data?: { message?: string; detail?: string } } }
    const msg = err.response?.data?.message || err.response?.data?.detail || '登录失败'
    ElMessage.error(typeof msg === 'string' ? msg : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-grid" aria-hidden="true" />
    <div class="login-card">
      <div class="login-brand">
        <div class="mark">等</div>
        <div>
          <h1 class="product">等保整改跟踪</h1>
          <p class="hint">机构内部整改进度工作台</p>
        </div>
      </div>
      <h2 class="title">登录</h2>
      <el-form class="form" label-position="top" @submit.prevent="onLogin">
        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="用户名" clearable />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
          />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="submit">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 18% 18%, rgba(29, 107, 92, 0.22), transparent 52%),
    radial-gradient(ellipse at 82% 78%, rgba(21, 32, 43, 0.14), transparent 48%),
    var(--wb-bg);
}

.login-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(21, 32, 43, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(21, 32, 43, 0.04) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
  pointer-events: none;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: var(--wb-card);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-lg);
  box-shadow: var(--wb-shadow-hover);
  padding: 32px 32px 36px;
  animation: login-in 0.45s ease both;
}

@keyframes login-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--wb-border);
}

.mark {
  width: 52px;
  height: 52px;
  border-radius: var(--wb-radius-md);
  background: var(--wb-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(29, 107, 92, 0.3);
  flex-shrink: 0;
}

.product {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.25;
}

.hint {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--wb-muted);
}

.title {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: var(--wb-muted);
}

.submit {
  width: 100%;
  margin-top: 8px;
  height: 40px;
  font-weight: 600;
}
</style>
