<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getgap_project_id, postGapAction, getGapLogs, get_gapscount } from '@/api/projects'
import CreateGapDialog from './CreateGapDialog.vue'

const route = useRoute()
const loading = ref(false)
const gaps = ref([])
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

onMounted(on_getgap_detail)
</script>

<template>
  <div class="page-panel">
    <div class="title-row">
      <div>
        <h2 class="page-title">差距列表</h2>
        <p class="sub">项目 ID：{{ route.params.id }}</p>
      </div>
      <el-button type="primary" @click="createVisible = true">录入差距</el-button>
    </div>

    <div class="status-bar" v-loading="loading">
      <div class="status-total">
        <span class="status-total-label">合计</span>
        <span class="status-total-num">{{ totalCount }}</span>
      </div>
      <div
        v-for="item in statusSummary"
        :key="item.status"
        class="status-chip"
        :class="'tone-' + item.tone"
      >
        <span class="status-chip-label">{{ item.status }}</span>
        <span class="status-chip-num">{{ item.num }}</span>
      </div>
    </div>

    <div v-loading="loading" class="list">
      <p v-if="!loading && gaps.length === 0">暂无差距项</p>

      <div class="head item">
        <div>标题</div>
        <div>状态</div>
        <div>类别</div>
        <div>风险</div>
        <div>创建时间</div>
      </div>

      <div
        v-for="item in gaps"
        :key="item.id"
        class="card"
        @click="openDrawer(item)"
      >
        <div class="item">
          <div>{{ item.title }}</div>
          <div>{{ item.status }}</div>
          <div>{{ item.category }}</div>
          <div>{{ item.risk_level }}</div>
          <div>{{ item.create_at }}</div>
        </div>
      </div>
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
          <p><span>标题：</span>{{ current.title }}</p>
          <p><span>状态：</span>{{ current.status }}</p>
          <p><span>类别：</span>{{ current.category }}</p>
          <p><span>风险：</span>{{ current.risk_level }}</p>
          <p><span>原因：</span>{{ current.reason }}</p>
          <p><span>要求：</span>{{ current.requirement }}</p>
          <p><span>创建时间：</span>{{ current.create_at }}</p>
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
              <div class="log-meta">操作人 #{{ log.actor_id }} · {{ log.create_at }}</div>
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
.title-row .page-title {
  margin-bottom: 4px;
}
.sub {
  color: var(--wb-muted);
  margin: 0 0 16px;
  font-size: 13px;
}

.status-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: stretch;
  margin-bottom: 14px;
}

.status-total {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 48px;
  padding: 5px 8px;
  border-radius: 6px;
  background: var(--wb-sidebar);
  color: #fff;
}

.status-total-label {
  font-size: 10px;
  opacity: 0.75;
}

.status-total-num {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.15;
  margin-top: 1px;
}

.status-chip {
  flex: 1;
  min-width: 64px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
  padding: 5px 8px;
  border-radius: 6px;
  border: 1px solid var(--wb-border);
  background: #f7faf9;
}

.status-chip-label {
  font-size: 10px;
  color: var(--wb-muted);
}

.status-chip-num {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.15;
  color: var(--wb-text);
}

.tone-pending {
  border-color: #e2c49a;
  background: #fbf6ee;
}
.tone-pending .status-chip-num {
  color: #a07030;
}
.tone-doing {
  border-color: #9bbad4;
  background: #eef4f9;
}
.tone-doing .status-chip-num {
  color: #3a6d94;
}
.tone-review {
  border-color: #c4b48a;
  background: #f8f4e8;
}
.tone-review .status-chip-num {
  color: #8a7340;
}
.tone-pass {
  border-color: #9bc4b6;
  background: var(--wb-accent-soft);
}
.tone-pass .status-chip-num {
  color: var(--wb-accent);
}
.tone-closed {
  border-color: #c9ced6;
  background: #f2f4f7;
}
.tone-closed .status-chip-num {
  color: #5c6673;
}

.card {
  cursor: pointer;
  padding: 12px;
  border-radius: 8px;
  transition: background 0.15s ease;
}
.card:hover {
  background: var(--wb-accent-soft);
}
.item {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
  gap: 12px;
  align-items: center;
}
.head {
  font-weight: 600;
  font-size: 13px;
  color: var(--wb-muted);
  padding: 8px 12px;
  border-bottom: 1px solid var(--wb-border);
  margin-bottom: 4px;
}
.drawer-body p {
  margin: 10px 0;
  line-height: 1.5;
  word-break: break-word;
}
.drawer-body span {
  font-weight: bold;
  color: #333;
}
.drawer-actions {
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.role-tip {
  width: 100%;
  color: #c45656;
  font-size: 13px;
}
.logs {
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--wb-border);
}
.logs ul {
  padding-left: 18px;
  margin: 8px 0 0;
}
.logs li {
  margin-bottom: 12px;
}
.log-comment {
  color: #555;
  margin-top: 4px;
}
.log-meta {
  font-size: 12px;
  color: var(--wb-muted);
  margin-top: 2px;
}

@media (max-width: 720px) {
  .status-chip {
    min-width: calc(33.33% - 6px);
  }
}
</style>
