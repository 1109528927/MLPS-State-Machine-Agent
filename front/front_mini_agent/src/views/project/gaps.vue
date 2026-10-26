<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getgap_project_id,
  postGapAction,
  getGapLogs,
  get_gapscount,
  getprojects,
  get_alluser,
} from '@/api/projects'
import CreateGapDialog from './CreateGapDialog.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

function goBackProjects() {
  router.push('/project')
}
const gaps = ref([])
const projectName = ref('')
const members = ref([])
/** null = 全部；否则按状态过滤 */
const statusFilter = ref(null)
const actionLoading = ref(false)

const drawerVisible = ref(false)
const createVisible = ref(false)
const current = ref(null)
const logs = ref([])

const ACTION_LABEL = {
  record: '代录说明',
  submit: '提交复核',
  reject: '退回',
  approve: '通过',
  close: '关闭',
}

/** 固定五种状态顺序；接口没有的键补 0 */
const STATUS_META = [
  { key: '待整改', tone: 'pending' },
  { key: '整改中', tone: 'doing' },
  { key: '待复核', tone: 'review' },
  { key: '已通过', tone: 'pass' },
  { key: '已关闭', tone: 'closed' },
]

function getUserRole() {
  try {
    const info = JSON.parse(localStorage.getItem('userInfo') || '{}')
    return info.role || ''
  } catch {
    return ''
  }
}

const role = ref(getUserRole())

/** 与后端 TRANSITIONS 对齐：当前状态允许哪些 action */
const ACTION_ALLOWED_STATUS = {
  record: ['待整改'],
  submit: ['整改中'],
  reject: ['待复核'],
  approve: ['待复核'],
  close: ['待整改'],
}

const ACTION_ROLES = {
  record: 'inspector',
  submit: 'inspector',
  reject: 'manager',
  approve: 'manager',
  close: 'manager',
}

/** 角色 + 当前状态都允许才显示按钮 */
function canDo(action) {
  const status = current.value?.status
  if (!status) return false
  if (!ACTION_ALLOWED_STATUS[action]?.includes(status)) return false
  return role.value === ACTION_ROLES[action]
}

const hasAnyAction = computed(() =>
  ['record', 'submit', 'reject', 'approve', 'close'].some((a) => canDo(a)),
)

const count_obj = ref({})

const statusSummary = computed(() =>
  STATUS_META.map(({ key, tone }) => ({
    status: key,
    tone,
    num: Number(count_obj.value?.[key] ?? 0),
  })),
)

const totalCount = computed(() =>
  statusSummary.value.reduce((sum, row) => sum + row.num, 0),
)

const filteredGaps = computed(() => {
  if (!statusFilter.value) return gaps.value
  return gaps.value.filter((g) => g.status === statusFilter.value)
})

function setStatusFilter(status) {
  statusFilter.value = status
}

function clearStatusFilter() {
  statusFilter.value = null
}

async function loadProjectName() {
  const pid = Number(route.params.id)
  try {
    const res = await getprojects({ page: 1, page_size: 100 })
    const items = res.data?.data?.items ?? []
    const hit = items.find((p) => Number(p.id) === pid)
    projectName.value = hit?.name || ''
  } catch {
    projectName.value = ''
  }
}

async function loadMembers() {
  const pid = Number(route.params.id)
  try {
    const res = await get_alluser({ project_id: pid })
    members.value = res.data?.data ?? []
  } catch {
    members.value = []
  }
}

const on_getgap_detail = async () => {
  loading.value = true
  try {
    const res = await getgap_project_id({
      project_id: Number(route.params.id),
    })
    gaps.value = res.data?.data ?? []
    const countRes = await get_gapscount({
      project_id: Number(route.params.id),
    })
    count_obj.value = countRes.data?.data ?? {}
  } catch (e) {
    console.error(e)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadLogs(gapId) {
  try {
    const res = await getGapLogs(gapId)
    logs.value = res.data?.data ?? []
  } catch (e) {
    console.error(e)
    logs.value = []
  }
}

async function openDrawer(item) {
  current.value = { ...item }
  drawerVisible.value = true
  await loadLogs(item.id)
}

function onDrawerClose() {
  current.value = null
  logs.value = []
}

async function askComment(title) {
  const { value } = await ElMessageBox.prompt(title, '请填写', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputType: 'textarea',
    inputValidator: (v) => !!String(v || '').trim() || '不能为空',
  })
  return String(value).trim()
}

async function onAction(action) {
  if (!current.value || actionLoading.value) return

  let comment = null
  try {
    if (action === 'record') {
      comment = await askComment('请填写代录整改说明')
    } else if (action === 'reject') {
      comment = await askComment('请填写退回原因')
    }
  } catch {
    return
  }

  actionLoading.value = true
  try {
    const res = await postGapAction(current.value.id, {
      action,
      comment,
    })
    const nextStatus = res.data?.data?.status
    ElMessage.success(`${ACTION_LABEL[action] || action}成功`)
    await on_getgap_detail()
    if (nextStatus) {
      current.value = { ...current.value, status: nextStatus }
    } else {
      const fresh = gaps.value.find((g) => g.id === current.value.id)
      if (fresh) current.value = { ...fresh }
    }
    await loadLogs(current.value.id)
  } catch (e) {
    console.error(e)
    const msg = e.response?.data?.message || e.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
  } finally {
    actionLoading.value = false
  }
}

onMounted(() => {
  loadProjectName()
  loadMembers()
  on_getgap_detail()
})
</script>

<template>
  <div class="page-panel">
    <div class="title-row">
      <div class="page-head title-left">
        <button
          type="button"
          class="page-back"
          title="返回项目列表"
          @click="goBackProjects"
        >
          ←
        </button>
        <div class="page-head-main">
          <h2 class="page-title">差距列表</h2>
          <p class="sub">
            {{ projectName || `项目 #${route.params.id}` }}
            <template v-if="projectName"> · id {{ route.params.id }}</template>
          </p>
        </div>
      </div>
      <el-button type="primary" @click="createVisible = true">录入差距</el-button>
    </div>

    <div class="member-bar">
      <span class="member-bar-label">项目成员</span>
      <template v-if="members.length === 0">
        <span class="member-empty">暂无成员</span>
      </template>
      <template v-else>
        <span
          v-for="m in members"
          :key="m.user_id"
          class="member-tag"
          :title="`工号：${m.employee_no || '—'}`"
        >
          {{ m.username }}
        </span>
      </template>
    </div>

    <div class="status-bar" v-loading="loading">
      <button
        type="button"
        class="status-total status-filter-btn"
        :class="{ active: !statusFilter }"
        title="显示全部"
        @click="clearStatusFilter"
      >
        <span class="status-total-label">合计</span>
        <span class="status-total-num">{{ totalCount }}</span>
      </button>
      <button
        v-for="item in statusSummary"
        :key="item.status"
        type="button"
        class="status-chip status-filter-btn"
        :class="['tone-' + item.tone, { active: statusFilter === item.status }]"
        :title="`筛选：${item.status}`"
        @click="setStatusFilter(item.status)"
      >
        <span class="status-chip-label">{{ item.status }}</span>
        <span class="status-chip-num">{{ item.num }}</span>
      </button>
    </div>

    <div v-loading="loading" class="list-card">
      <p v-if="!loading && gaps.length === 0" class="list-empty">
        暂无差距项
        <button type="button" class="empty-cta" @click="createVisible = true">
          去录入
        </button>
      </p>
      <p v-else-if="!loading && filteredGaps.length === 0" class="list-empty">
        当前状态无数据
        <button type="button" class="empty-cta" @click="clearStatusFilter">
          查看全部
        </button>
      </p>
      <template v-else>
        <div class="list-head cols">
          <div>标题</div>
          <div>状态</div>
          <div>类别</div>
          <div>风险</div>
          <div>创建时间</div>
        </div>
        <div
          v-for="item in filteredGaps"
          :key="item.id"
          class="list-row cols"
          @click="openDrawer(item)"
        >
          <div class="name">{{ item.title }}</div>
          <div class="muted">{{ item.status }}</div>
          <div class="muted">{{ item.category || '—' }}</div>
          <div class="muted">{{ item.risk_level || '—' }}</div>
          <div class="muted">{{ item.create_at }}</div>
        </div>
      </template>
    </div>

    <CreateGapDialog
      v-model="createVisible"
      :project-id="route.params.id"
      @success="on_getgap_detail"
    />

    <el-drawer
      v-model="drawerVisible"
      title="差距详情"
      size="40%"
      destroy-on-close
      @close="onDrawerClose"
    >
      <template v-if="current">
        <div class="drawer-body">
          <div class="field">
            <span class="field-label">标题</span>
            <span class="field-value">{{ current.title }}</span>
          </div>
          <div class="field">
            <span class="field-label">状态</span>
            <span class="field-value">{{ current.status }}</span>
          </div>
          <div class="field">
            <span class="field-label">类别</span>
            <span class="field-value">{{ current.category || '—' }}</span>
          </div>
          <div class="field">
            <span class="field-label">风险</span>
            <span class="field-value">{{ current.risk_level || '—' }}</span>
          </div>
          <div class="field">
            <span class="field-label">原因</span>
            <span class="field-value">{{ current.reason || '—' }}</span>
          </div>
          <div class="field">
            <span class="field-label">要求</span>
            <span class="field-value">{{ current.requirement || '—' }}</span>
          </div>
          <div class="field">
            <span class="field-label">创建时间</span>
            <span class="field-value">{{ current.create_at }}</span>
          </div>
        </div>

        <div class="drawer-actions">
          <el-button
            v-if="canDo('record')"
            type="primary"
            :loading="actionLoading"
            @click="onAction('record')"
          >
            代录说明
          </el-button>
          <el-button
            v-if="canDo('submit')"
            type="success"
            :loading="actionLoading"
            @click="onAction('submit')"
          >
            提交复核
          </el-button>
          <el-button
            v-if="canDo('reject')"
            type="warning"
            :loading="actionLoading"
            @click="onAction('reject')"
          >
            退回
          </el-button>
          <el-button
            v-if="canDo('approve')"
            type="success"
            plain
            :loading="actionLoading"
            @click="onAction('approve')"
          >
            通过
          </el-button>
          <el-button
            v-if="canDo('close')"
            type="danger"
            plain
            :loading="actionLoading"
            @click="onAction('close')"
          >
            关闭
          </el-button>
          <p v-if="!role" class="role-tip">未读取到角色，请重新登录</p>
          <p v-else-if="!hasAnyAction" class="role-tip muted-tip">
            当前状态无需您操作（或请用对应角色账号）
          </p>
        </div>

        <div class="logs">
          <h4>操作历史</h4>
          <p v-if="logs.length === 0">暂无记录</p>
          <ul v-else>
            <li v-for="log in logs" :key="log.id">
              <div>
                {{ ACTION_LABEL[log.action] || log.action }}：
                {{ log.from_status }} → {{ log.to_status }}
              </div>
              <div v-if="log.comment" class="log-comment">说明：{{ log.comment }}</div>
              <div class="log-meta">
                {{ log.actor_name || `操作人 #${log.actor_id}` }} · {{ log.create_at }}
              </div>
            </li>
          </ul>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.title-left {
  flex: 1;
  min-width: 0;
  margin-bottom: 0;
}
.title-row .page-title {
  margin-bottom: 4px;
  border-bottom: none;
  padding-bottom: 0;
}
.sub {
  color: var(--wb-muted);
  margin: 0 0 12px;
  font-size: 13px;
}
.member-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: var(--wb-radius-sm);
  border: 1px solid var(--wb-border);
  background: #f7faf9;
}
.member-bar-label {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--wb-muted);
  margin-right: 4px;
}
.member-empty {
  font-size: 13px;
  color: var(--wb-muted);
}
.member-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--wb-radius-sm);
  border: 1px solid rgba(29, 107, 92, 0.22);
  background: var(--wb-accent-soft);
  color: var(--wb-accent);
  font-size: 13px;
  font-weight: 500;
}
.cols {
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
}
@media (max-width: 720px) {
  .cols {
    grid-template-columns: 1.4fr 0.9fr 0.8fr 0.7fr 1fr;
    font-size: 12px;
    gap: 6px;
  }
  .title-row {
    flex-direction: column;
    align-items: stretch;
  }
}
.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field-label {
  font-size: 12px;
  color: var(--wb-muted);
  font-weight: 500;
}
.field-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--wb-text);
  line-height: 1.5;
  word-break: break-word;
}
.drawer-actions {
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.role-tip {
  width: 100%;
  color: var(--wb-danger);
  font-size: 13px;
}
.muted-tip {
  color: var(--wb-muted);
}
.empty-cta {
  margin-left: 10px;
  border: none;
  background: transparent;
  color: var(--wb-accent);
  font-size: 13px;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}
.logs {
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--wb-border);
}
.logs h4 {
  margin: 0 0 8px;
  font-size: 14px;
}
.logs ul {
  padding-left: 18px;
  margin: 8px 0 0;
}
.logs li {
  margin-bottom: 12px;
}
.log-comment {
  color: var(--wb-text);
  margin-top: 4px;
  opacity: 0.85;
}
.log-meta {
  font-size: 12px;
  color: var(--wb-muted);
  margin-top: 2px;
}
</style>
