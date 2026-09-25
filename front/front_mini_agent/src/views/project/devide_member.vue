<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getprojects,
  post_add_member,
  get_alluser,
  delete_member,
} from '@/api/projects'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const projects = ref([])
const projectId = ref(null)
const userId = ref(null)
const members = ref([])

async function loadProjects() {
  loading.value = true
  try {
    const res = await getprojects({ name: '' })
    projects.value = res.data?.data ?? []
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '加载项目失败')
  } finally {
    loading.value = false
  }
}

async function loadMembers(id) {
  if (id == null || id === '') {
    members.value = []
    return
  }
  try {
    const res = await get_alluser({ project_id: Number(id) })
    members.value = res.data?.data ?? []
  } catch (e) {
    members.value = []
    ElMessage.error(e.response?.data?.message || '加载成员失败')
  }
}

async function onSubmit() {
  if (projectId.value == null) {
    ElMessage.warning('请选择项目')
    return
  }
  if (userId.value == null || userId.value === '') {
    ElMessage.warning('请输入要分配的用户 ID')
    return
  }

  submitting.value = true
  try {
    const res = await post_add_member({
      user_id: Number(userId.value),
      project_id: Number(projectId.value),
    })
    const payload = res.data?.data
    const nameText = payload?.username || `用户${payload?.user_id}`
    const projectText = payload?.project_name || `项目${payload?.project_id}`
    ElMessage.success(res.data?.message || `已将 ${nameText} 加入 ${projectText}`)
    userId.value = null
    await loadMembers(projectId.value)
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '分配失败')
  } finally {
    submitting.value = false
  }
}

async function onRemove(m) {
  if (projectId.value == null) {
    ElMessage.warning('请先选择项目')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定将「${m.username}」移出当前项目？移出后该用户将看不到此项目。`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }

  try {
    const res = await delete_member({
      user_id: Number(m.user_id),
      project_id: Number(projectId.value),
    })
    ElMessage.success(res.data?.message || '移除成功')
    await loadMembers(projectId.value)
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '移除失败')
  }
}

function cancel() {
  router.push('/project')
}

watch(projectId, (id) => {
  loadMembers(id)
})

onMounted(loadProjects)
</script>

<template>
  <div class="page-panel form-panel" v-loading="loading">
    <h2 class="page-title">分配成员</h2>

    <el-form class="innerbox" label-width="120px" label-position="right">
      <el-form-item label="项目">
        <el-select
          v-model="projectId"
          placeholder="请选择项目"
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="item in projects"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="已有成员">
        <div class="member-list">
          <template v-if="!projectId">请先选择项目</template>
          <template v-else-if="members.length === 0">暂无成员</template>
          <template v-else>
            <div v-for="m in members" :key="m.user_id" class="member-row">
              <span>{{ m.username }}（工号：{{ m.employee_no }}）</span>
              <button
                type="button"
                class="remove-btn"
                title="移出项目"
                @click="onRemove(m)"
              >
                ×
              </button>
            </div>
          </template>
        </div>
      </el-form-item>

      <el-form-item label="用户 ID">
        <el-input
          v-model="userId"
          type="number"
          placeholder="请输入要分配的用户 ID"
          clearable
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">
          确定
        </el-button>
        <el-button @click="cancel">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-panel {
  max-width: 640px;
}
.innerbox {
  width: 100%;
  max-width: 520px;
}
.member-list {
  min-height: 32px;
  color: var(--wb-muted);
  line-height: 1.5;
  width: 100%;
}
.member-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 6px;
  color: var(--wb-text);
}
.member-row:hover {
  background: var(--wb-accent-soft);
}
.remove-btn {
  display: none;
  border: none;
  background: transparent;
  color: #c45656;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
}
.member-row:hover .remove-btn {
  display: inline-block;
}
</style>
