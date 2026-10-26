<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getprojects,
  post_add_member,
  get_alluser,
  delete_member,
} from '@/api/projects'
import { get_user_list } from '@/api/login'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const projects = ref([])
const allUsers = ref([])
const projectId = ref(null)
const userId = ref(null)
const members = ref([])

const memberIdSet = computed(
  () => new Set(members.value.map((m) => Number(m.user_id))),
)

/** 未加入当前项目的用户，供下拉选择 */
const candidateUsers = computed(() =>
  allUsers.value.filter((u) => !memberIdSet.value.has(Number(u.id))),
)

async function loadProjects() {
  loading.value = true
  try {
    const res = await getprojects({ page: 1, page_size: 100 })
    projects.value = res.data?.data?.items ?? []
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '加载项目失败')
  } finally {
    loading.value = false
  }
}

async function loadAllUsers() {
  try {
    const res = await get_user_list()
    allUsers.value = res.data?.data ?? []
  } catch (e) {
    console.error(e)
    allUsers.value = []
    ElMessage.error(e.response?.data?.message || '加载用户失败')
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
    ElMessage.warning('请选择要分配的用户')
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
  userId.value = null
  loadMembers(id)
})

onMounted(async () => {
  await Promise.all([loadProjects(), loadAllUsers()])
})
</script>

<template>
  <div class="page-panel form-panel" v-loading="loading">
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
        <h2 class="page-title">分配成员</h2>
      </div>
    </div>

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
          <template v-if="!projectId">
            <p class="list-empty member-hint">请先选择项目</p>
          </template>
          <template v-else-if="members.length === 0">
            <p class="list-empty member-hint">暂无成员</p>
          </template>
          <template v-else>
            <div
              v-for="m in members"
              :key="m.user_id"
              class="list-row member-row"
            >
              <span class="name">{{ m.username }}</span>
              <span class="muted">工号：{{ m.employee_no }}</span>
              <button
                type="button"
                class="remove-btn"
                title="移出项目"
                @click.stop="onRemove(m)"
              >
                ×
              </button>
            </div>
          </template>
        </div>
      </el-form-item>

      <el-form-item label="添加用户">
        <el-select
          v-model="userId"
          placeholder="请选择用户（可搜索账号/工号）"
          filterable
          clearable
          :disabled="!projectId"
          style="width: 100%"
        >
          <el-option
            v-for="u in candidateUsers"
            :key="u.id"
            :label="`${u.username}（工号 ${u.employee_no || '—'}）`"
            :value="u.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item class="form-actions-item">
        <div class="form-actions">
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            确定
          </el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.innerbox {
  width: 100%;
  max-width: 520px;
}
.member-list {
  min-height: 32px;
  width: 100%;
}
.member-hint {
  padding: 12px 0;
  text-align: left;
}
.member-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr auto;
  cursor: default;
  margin-bottom: 4px;
  border: 1px solid var(--wb-border);
}
.member-row:hover {
  border-color: rgba(29, 107, 92, 0.25);
}
.remove-btn {
  border: none;
  background: transparent;
  color: var(--wb-danger);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}
.member-row:hover .remove-btn {
  opacity: 1;
}
.form-actions-item :deep(.el-form-item__content) {
  justify-content: flex-end;
}
</style>
