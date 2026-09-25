<script setup>
import { ElMessage } from 'element-plus'
import { getprojects } from '@/api/projects'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const projects = ref([])
const keyword = ref('')

const onprojects = async () => {
  loading.value = true
  try {
    const params = { name: '' }
    if (keyword.value.trim()) {
      params.name = keyword.value.trim()
    }
    const res = await getprojects(params)
    projects.value = res.data?.data ?? []
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function goGaps(projectId) {
  router.push(`/project/${projectId}/gaps`)
}

onMounted(onprojects)
</script>

<template>
  <div class="page-panel">
    <h2 class="page-title">项目列表</h2>
    <div class="page-toolbar">
      <el-input
        v-model="keyword"
        placeholder="按项目名称搜索"
        clearable
        style="max-width: 320px"
        @keyup.enter="onprojects"
      />
      <el-button type="primary" @click="onprojects">搜索</el-button>
    </div>

    <div v-loading="loading" class="list">
      <p v-if="!loading && projects.length === 0" class="empty">暂无项目</p>
      <div v-else class="head item">
        <div>项目名称</div>
        <div>备注</div>
        <div>创建时间</div>
      </div>
      <div
        v-for="item in projects"
        :key="item.id"
        class="card"
        @click="goGaps(item.id)"
      >
        <div class="item">
          <div class="name">{{ item.name }}</div>
          <div class="muted">{{ item.remark || '—' }}</div>
          <div class="muted">{{ item.create_at }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list {
  min-height: 120px;
}
.empty {
  color: var(--wb-muted);
  text-align: center;
  padding: 32px 0;
}
.item {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr;
  gap: 12px;
  align-items: center;
}
.head {
  font-weight: 600;
  font-size: 13px;
  color: var(--wb-muted);
  padding: 8px 12px;
  border-bottom: 1px solid var(--wb-border);
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
.name {
  font-weight: 600;
}
.muted {
  color: var(--wb-muted);
  font-size: 13px;
}
</style>
