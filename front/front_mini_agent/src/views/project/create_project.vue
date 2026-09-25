<script setup>
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { post_add_project } from '@/api/projects'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({})

const add_project = async () => {
  const data = {
    name: form.value.name,
    remark: form.value.remark,
  }
  if (!String(data.name ?? '').trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  try {
    const res = await post_add_project(data)
    ElMessage.success(res.data?.message || '创建成功')
    router.push('/project')
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  }
}

const cancel = () => {
  router.push('/project')
}
</script>

<template>
  <div class="page-panel form-panel">
    <h2 class="page-title">新建项目</h2>
    <el-form class="innerbox" label-width="80px" label-position="right">
      <el-form-item label="项目名称">
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" placeholder="请输入备注" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="add_project">创建</el-button>
        <el-button @click="cancel">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-panel {
  max-width: 560px;
}
.innerbox {
  max-width: 480px;
}
</style>
