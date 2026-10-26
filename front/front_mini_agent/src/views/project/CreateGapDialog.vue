<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { post_create_gap } from '@/api/projects'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  projectId: { type: [Number, String], required: true },
})

const emit = defineEmits(['update:modelValue', 'success'])

/** 等保测评常见安全类（GB/T 22239 十大类） */
const CATEGORY_OPTIONS = [
  '安全物理环境',
  '安全通信网络',
  '安全区域边界',
  '安全计算环境',
  '安全管理中心',
  '安全管理制度',
  '安全管理机构',
  '安全管理人员',
  '安全建设管理',
  '安全运维管理',
]

const RISK_OPTIONS = ['高', '中', '低']

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
    class="gap-dialog"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form label-width="88px" label-position="right" class="gap-form">
      <el-form-item label="标题" required>
        <el-input v-model="form.title" placeholder="差距项标题" maxlength="200" show-word-limit />
      </el-form-item>
      <el-form-item label="类别">
        <el-select
          v-model="form.category"
          placeholder="请选择安全类（可选）"
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="c in CATEGORY_OPTIONS"
            :key="c"
            :label="c"
            :value="c"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="风险等级">
        <el-select
          v-model="form.risk_level"
          placeholder="请选择（可选）"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="r in RISK_OPTIONS"
            :key="r"
            :label="r"
            :value="r"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="原因">
        <el-input v-model="form.reason" type="textarea" :rows="2" placeholder="可选" />
      </el-form-item>
      <el-form-item label="整改要求">
        <el-input v-model="form.requirement" type="textarea" :rows="2" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="form-actions">
        <el-button @click="close">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.gap-form :deep(.el-form-item) {
  margin-bottom: 18px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
