<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const userInfo = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('userInfo') || '{}')
  } catch {
    return {}
  }
})

const isManager = computed(() => userInfo.value.role === 'manager')

const displayName = computed(
  () => userInfo.value.username || userInfo.value.employee_no || '用户',
)

const roleLabel = computed(() => {
  if (userInfo.value.role === 'manager') return '项目经理'
  if (userInfo.value.role === 'inspector') return '核查人员'
  return userInfo.value.role || '未设置角色'
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  router.push('/login')
}
</script>

<template>
  <div class="workbench">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">等</div>
        <div class="brand-text">
          <div class="brand-name">等保整改跟踪</div>
          <div class="brand-sub">内部工作台</div>
        </div>
      </div>

      <nav class="nav">
        <router-link class="nav-item" to="/project">我的项目</router-link>
        <router-link class="nav-item" to="/chat">智能助手</router-link>
        <template v-if="isManager">
          <div class="nav-group">管理</div>
          <router-link class="nav-item" to="/users/create">开通账号</router-link>
          <router-link class="nav-item" to="/project/create">新建项目</router-link>
          <router-link class="nav-item" to="/project/devideuser">分配核查</router-link>
        </template>
      </nav>
    </aside>

    <div class="main-wrap">
      <header class="topbar">
        <div class="topbar-title">整改跟踪工作台</div>
        <div class="topbar-right">
          <div class="user-meta">
            <span class="user-name">{{ displayName }}</span>
            <span class="user-role">{{ roleLabel }}</span>
          </div>
          <button type="button" class="logout-btn" @click="logout">退出</button>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.workbench {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--wb-bg);
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--wb-sidebar);
  color: #e8eef4;
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
}

.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 10px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 12px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--wb-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
}

.brand-sub {
  font-size: 12px;
  color: rgba(232, 238, 244, 0.55);
  margin-top: 2px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-group {
  margin: 14px 10px 6px;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(232, 238, 244, 0.4);
}

.nav-item {
  display: block;
  padding: 10px 12px;
  border-radius: 8px;
  color: rgba(232, 238, 244, 0.82);
  font-size: 14px;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--wb-sidebar-hover);
  color: #fff;
}

.nav-item.router-link-active {
  background: var(--wb-sidebar-active);
  color: #fff;
  box-shadow: inset 3px 0 0 var(--wb-accent);
}

.main-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 56px;
  flex-shrink: 0;
  background: var(--wb-header);
  border-bottom: 1px solid var(--wb-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--wb-text);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.25;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
}

.user-role {
  font-size: 12px;
  color: var(--wb-muted);
}

.logout-btn {
  border: 1px solid var(--wb-border);
  background: #fff;
  color: var(--wb-text);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}

.logout-btn:hover {
  border-color: var(--wb-accent);
  color: var(--wb-accent);
}

.content {
  flex: 1;
  overflow: auto;
  padding: 20px 24px 32px;
}
</style>
