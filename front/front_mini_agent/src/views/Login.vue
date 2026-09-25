<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { post_login } from '@/api/login'

const router = useRouter()
const loading = ref(false)
interface LoginForm{
  username:string
  password:string
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
    }
    ElMessage.success(res.data?.message || '登录成功')
    await router.push('/project')
  } catch (e) {
  console.error(e)
  const err = e as { response?: { data?: { message?: string } } }
  ElMessage.error(err.response?.data?.message || '登录失败')
} finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
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
        <el-button type="primary" native-type="submit" :loading="loading" class="submit" >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(29, 107, 92, 0.18), transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(21, 32, 43, 0.12), transparent 45%),
    var(--wb-bg);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--wb-card);
  border: 1px solid var(--wb-border);
  border-radius: 12px;
  box-shadow: var(--wb-shadow);
  padding: 28px 28px 32px;
}

.login-brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 24px;
}

.mark {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--wb-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
}

.product {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.hint {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--wb-muted);
}

.title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.submit {
  width: 100%;
  margin-top: 8px;
}
</style>
