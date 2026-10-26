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
          <router-link class="nav-item" to="/project/devideuser">分配成员</router-link>
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
  width: 232px;
  flex-shrink: 0;
  background: var(--wb-sidebar);
  color: #e8eef4;
  display: flex;
  flex-direction: column;
  padding: 18px 12px;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 10px 10px 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 14px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: var(--wb-radius-md);
  background: var(--wb-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(29, 107, 92, 0.35);
  flex-shrink: 0;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 0.02em;
}

.brand-sub {
  font-size: 12px;
  color: rgba(232, 238, 244, 0.5);
  margin-top: 3px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-group {
  margin: 18px 10px 8px;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(232, 238, 244, 0.38);
  font-weight: 600;
}

.nav-item {
  display: block;
  padding: 10px 12px;
  border-radius: var(--wb-radius-sm);
  color: rgba(232, 238, 244, 0.82);
  font-size: 14px;
  transition:
    background 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

.nav-item:hover {
  background: var(--wb-sidebar-hover);
  color: #fff;
}

.nav-item.router-link-active {
  background: var(--wb-sidebar-active);
  color: #fff;
  box-shadow: inset 3px 0 0 var(--wb-accent);
  font-weight: 600;
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
  box-shadow: 0 1px 0 rgba(21, 32, 43, 0.03);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--wb-space-lg);
}

.topbar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--wb-text);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  line-height: 1.25;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
}

.user-role {
  font-size: 12px;
  color: var(--wb-accent);
  background: var(--wb-accent-soft);
  border: 1px solid rgba(29, 107, 92, 0.2);
  border-radius: 999px;
  padding: 2px 10px;
  font-weight: 500;
}

.logout-btn {
  border: 1px solid rgba(29, 107, 92, 0.35);
  background: transparent;
  color: var(--wb-accent);
  border-radius: var(--wb-radius-sm);
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    border-color 0.15s ease;
}

.logout-btn:hover {
  background: var(--wb-accent);
  border-color: var(--wb-accent);
  color: #fff;
}

.content {
  flex: 1;
  overflow: auto;
  padding: var(--wb-space-lg) var(--wb-space-lg) 36px;
}
</style>
