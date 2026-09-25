<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { getRecords, postChat } from '@/api/chat'

const input = ref('')
const messages = ref([])
const loading = ref(false)
const listRef = ref(null)

async function scrollToBottom() {
  await nextTick()
  const el = listRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function loadHistory() {
  loading.value = true
  try {
    const res = await getRecords({ skip: 0, limit: 20 })
    const rows = res.data?.data ?? []
    const list = []
    for (const r of [...rows].reverse()) {
      if (r.user_input) list.push({ role: 'user', text: r.user_input })
      if (r.agent_output) list.push({ role: 'assistant', text: r.agent_output })
    }
    messages.value = list
    await scrollToBottom()
  } catch (e) {
    console.error(e)
    ElMessage.error('历史加载失败')
  } finally {
    loading.value = false
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', text })
  await scrollToBottom()
  loading.value = true
  try {
    const res = await postChat(text)
    const reply =
      res.data?.data?.agent_output ?? res.data?.data?.reply ?? '（无回复）'
    messages.value.push({ role: 'assistant', text: reply })
    await scrollToBottom()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '发送失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<template>
  <div class="page-panel chat-panel">
    <h2 class="page-title">智能助手</h2>
    <div class="list" v-loading="loading" ref="listRef">
      <p class="empty" v-if="!loading && messages.length === 0">暂无消息</p>
      <ul class="info">
        <li v-for="(item, index) in messages" :key="index" :class="item.role">
          <b>{{ item.role === 'user' ? '我' : '助手' }}</b>
          <span>{{ item.text }}</span>
        </li>
      </ul>
    </div>
    <div class="bottom">
      <el-input
        v-model="input"
        placeholder="说点什么"
        :disabled="loading"
        @keyup.enter="send"
      />
      <el-button type="primary" :loading="loading" @click="send">发送</el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  max-width: 800px;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 120px);
}
.list {
  flex: 1;
  overflow-y: auto;
  background: #f4f7fa;
  border: 1px solid var(--wb-border);
  border-radius: 8px;
  padding: 12px 16px;
  min-height: 320px;
}
.empty {
  display: flex;
  margin: 0;
  height: 100%;
  min-height: 200px;
  justify-content: center;
  align-items: center;
  color: var(--wb-muted);
}
.info {
  list-style: none;
  margin: 0;
  padding: 0;
}
.info li {
  margin-bottom: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fff;
}
.info li.user {
  background: var(--wb-accent-soft);
}
.info b {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--wb-muted);
}
.bottom {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
</style>
