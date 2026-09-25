<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { post_register } from '@/api/login'



const loading = ref(false)
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
    ElMessage.success(res.data?.message || '开通成功')
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
    <h2 class="page-title">开通账号</h2>
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
      <el-button
        type="primary"
        native-type="submit"
        :loading="loading"
        style="width: 100%"
      >
        开通
      </el-button>
    </el-form>
  </div>
</template>

<style scoped>
.form-panel {
  max-width: 480px;
}
</style>
