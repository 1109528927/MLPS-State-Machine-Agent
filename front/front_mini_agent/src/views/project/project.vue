<script setup>
import { ElMessage } from 'element-plus'
import { getprojects } from '@/api/projects'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const projects = ref([])
const keyword = ref('')
/** 已生效的搜索词；有值时显示返回箭头 */
const activeKeyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const isFiltered = computed(() => !!activeKeyword.value.trim())

const onprojects = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    const name = activeKeyword.value.trim()
    if (name) {
      params.name = name
    }
    const res = await getprojects(params)
    const payload = res.data?.data
    projects.value = payload?.items ?? []
    total.value = Number(payload?.total ?? 0)
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  activeKeyword.value = keyword.value.trim()
  page.value = 1
  onprojects()
}

/** 返回完整列表（清搜索条件） */
function backToFullList() {
  keyword.value = ''
  activeKeyword.value = ''
  page.value = 1
  onprojects()
}

function onClearInput() {
  // 点输入框清空：若当前处于搜索态，一并回到全量
  if (activeKeyword.value) {
    backToFullList()
  }
}

function onPageChange(p) {
  page.value = p
  onprojects()
}

function onSizeChange(size) {
  pageSize.value = size
  page.value = 1
  onprojects()
}

function goGaps(projectId) {
  router.push(`/project/${projectId}/gaps`)
}

onMounted(onprojects)
</script>

<template>
  <div class="page-panel">
    <div class="page-head">
      <button
        v-if="isFiltered"
        type="button"
        class="page-back"
        title="返回全部项目"
        @click="backToFullList"
      >
        ←
      </button>
      <div class="page-head-main">
        <h2 class="page-title">
          {{ isFiltered ? '搜索结果' : '项目列表' }}
        </h2>
        <p v-if="isFiltered" class="filter-tip">
          关键词「{{ activeKeyword }}」· 点击左上角箭头返回全部
        </p>
      </div>
    </div>

    <div class="page-toolbar">
      <el-input
        v-model="keyword"
        placeholder="按项目名称搜索"
        clearable
        style="max-width: 320px"
        @keyup.enter="onSearch"
        @clear="onClearInput"
      />
      <el-button type="primary" @click="onSearch">搜索</el-button>
      <el-button v-if="isFiltered" @click="backToFullList">返回全部</el-button>
    </div>

    <div v-loading="loading" class="list-card">
      <p v-if="!loading && projects.length === 0" class="list-empty">
        {{ isFiltered ? '没有匹配的项目' : '暂无项目' }}
      </p>
      <template v-else>
        <div class="list-head cols">
          <div>项目名称</div>
          <div>备注</div>
          <div>创建时间</div>
        </div>
        <div
          v-for="item in projects"
          :key="item.id"
          class="list-row cols"
          @click="goGaps(item.id)"
        >
          <div class="name">{{ item.name }}</div>
          <div class="muted">{{ item.remark || '—' }}</div>
          <div class="muted">{{ item.create_at }}</div>
        </div>
      </template>
    </div>

    <div class="pager" v-if="total > 0">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :total="total"
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="[5, 10, 20]"
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
.page-panel .page-title {
  margin-bottom: 0;
  padding-bottom: 8px;
}
.filter-tip {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--wb-muted);
}
.cols {
  grid-template-columns: 2fr 1.5fr 1.5fr;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
@media (max-width: 720px) {
  .cols {
    grid-template-columns: 1.4fr 1fr 1fr;
    font-size: 12px;
    gap: 8px;
  }
  .pager {
    justify-content: center;
  }
}
</style>
