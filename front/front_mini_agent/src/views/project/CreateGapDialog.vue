<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { post_create_gap } from '@/api/projects'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  projectId: { type: [Number, String], required: true },
})

const emit = defineEmits(['update:modelValue', 'success'])

const submitting = ref(false)
const form = ref({
  title: '',
  category: '',
  risk_level: '',
  reason: '',
  requirement: '',
})

function resetForm() {
  form.value = {
    title: '',
    category: '',
    risk_level: '',
    reason: '',
    requirement: '',
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) resetForm()
  },
)

function close() {
  emit('update:modelValue', false)
}

async function onSubmit() {
  if (!String(form.value.title ?? '').trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  submitting.value = true
  try {
    const res = await post_create_gap({
      project_id: Number(props.projectId),
      title: form.value.title.trim(),
      category: form.value.category || null,
      risk_level: form.value.risk_level || null,
      reason: form.value.reason || null,
      requirement: form.value.requirement || null,
    })
    ElMessage.success(res.data?.message || '录入成功')
    emit('success')
    close()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || e.response?.data?.detail || '录入失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="录入差距"
    width="520px"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form label-width="88px" label-position="right">
      <el-form-item label="标题" required>
        <el-input v-model="form.title" placeholder="差距项标题" />
      </el-form-item>
      <el-form-item label="类别">
        <el-input v-model="form.category" placeholder="可选" />
      </el-form-item>
      <el-form-item label="风险等级">
        <el-input v-model="form.risk_level" placeholder="可选，如高/中/低" />
      </el-form-item>
      <el-form-item label="原因">
        <el-input v-model="form.reason" type="textarea" :rows="2" placeholder="可选" />
      </el-form-item>
      <el-form-item label="整改要求">
        <el-input v-model="form.requirement" type="textarea" :rows="2" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>
