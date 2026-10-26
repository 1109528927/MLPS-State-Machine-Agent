<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { post_register } from '@/api/login'

const router = useRouter()
const loading = ref(false)

function goBackProjects() {
  router.push('/project')
}
interface RegisterForm {
  username: string
  password: string
  employee_no: string
}
const form = ref<RegisterForm>({
  username: '',
  password: '',
  employee_no: '',
})
const formRef = ref<FormInstance>()

/** 与后端 UserRequest Field 对齐：用户名 3～32、密码 6～64、工号 1～32 */
const rules: FormRules<RegisterForm> = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 32, message: '账号长度为 3～32 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度为 6～64 位', trigger: 'blur' },
  ],
  employee_no: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { min: 1, max: 32, message: '工号长度为 1～32 位', trigger: 'blur' },
  ],
}

function clearForm() {
  form.value = {
    username: '',
    password: '',
    employee_no: '',
  }
  formRef.value?.clearValidate()
}

async function onCreate() {
  const ok = await formRef.value?.validate().catch(() => false)
  if (!ok) return

  loading.value = true
  try {
    const res = await post_register({
      username: form.value.username.trim(),
      password: form.value.password,
      employee_no: form.value.employee_no.trim(),
    })
    const info = res.data?.data?.userInfo
    const tip = info?.id
      ? `开通成功：${info.username}（可在「分配成员」中按账号选择）`
      : res.data?.message || '开通成功'
    ElMessage.success(tip)
    clearForm()
  } catch (e) {
    console.error(e)
    const msg = axios.isAxiosError(e)
      ? (e.response?.data as { message?: string } | undefined)?.message
      : undefined
    ElMessage.error(msg || '开通失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-panel form-panel">
    <div class="page-head">
      <button
        type="button"
        class="page-back"
        title="返回项目列表"
        @click="goBackProjects"
      >
        ←
      </button>
      <div class="page-head-main">
        <h2 class="page-title">开通账号</h2>
      </div>
    </div>
    <el-form
      ref="formRef"
      class="form"
      :model="form"
      :rules="rules"
      label-position="top"
      @submit.prevent="onCreate"
    >
      <el-form-item label="账号" prop="username">
        <el-input v-model="form.username" placeholder="用户名 3～32 位" clearable />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="密码 6～64 位"
          show-password
        />
      </el-form-item>
      <el-form-item label="工号" prop="employee_no">
        <el-input v-model="form.employee_no" placeholder="工号" clearable />
      </el-form-item>
      <div class="form-actions">
        <el-button @click="goBackProjects">取消</el-button>
        <el-button type="primary" native-type="submit" :loading="loading">
          开通
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<style scoped>
.form {
  max-width: 400px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}
.form-actions .el-button {
  min-width: 96px;
}
</style>
