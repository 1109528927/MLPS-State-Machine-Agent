<script setup>
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { post_add_project } from '@/api/projects'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({})
const submitting = ref(false)

const add_project = async () => {
  const data = {
    name: form.value.name,
    remark: form.value.remark,
  }
  if (!String(data.name ?? '').trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  submitting.value = true
  try {
    const res = await post_add_project(data)
    ElMessage.success(res.data?.message || '创建成功')
    router.push('/project')
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const cancel = () => {
  router.push('/project')
}
</script>

<template>
  <div class="page-panel form-panel">
    <div class="page-head">
      <button
        type="button"
        class="page-back"
        title="返回项目列表"
        @click="cancel"
      >
        ←
      </button>
      <div class="page-head-main">
        <h2 class="page-title">新建项目</h2>
      </div>
    </div>
    <el-form class="innerbox" label-width="80px" label-position="right">
      <el-form-item label="项目名称">
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" placeholder="请输入备注" />
      </el-form-item>
      <el-form-item class="form-actions-item">
        <div class="form-actions">
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="add_project">创建</el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.innerbox {
  max-width: 480px;
}
.form-actions-item :deep(.el-form-item__content) {
  justify-content: flex-end;
}
</style>
