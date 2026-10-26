<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getRecords, chatStreamApi, warmupAgent } from '@/api/chat'

const input = ref('')
const messages = ref([])
const loading = ref(false)
const statusText = ref('')
const listRef = ref(null)

const quickPrompts = [
  '我有哪些项目？',
  '给我一个工作台总览',
  '我是谁？权限范围是什么？',
  '项目里待整改还有几条？',
]

const roleHint = computed(() => {
  try {
    const info = JSON.parse(localStorage.getItem('userInfo') || '{}')
    if (info.role === 'manager') return '当前：项目经理（可查全部项目）'
    if (info.role === 'inspector') return '当前：核查人员（仅可见被分配项目）'
    return '已登录'
  } catch {
    return ''
  }
})

async function scrollToBottom() {
  await nextTick()
  const el = listRef.value
  if (el) el.scrollTop = el.scrollHeight
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

/** 无 token 流时：按队列慢慢画 done.answer */
async function typeOut(msgIndex, text) {
  const step = 2
  for (let i = 0; i < text.length; i += step) {
    if (!messages.value[msgIndex]) return
    messages.value[msgIndex].text = text.slice(0, i + step)
    await scrollToBottom()
    await sleep(18)
  }
  if (messages.value[msgIndex]) {
    messages.value[msgIndex].text = text
  }
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

function useQuick(q) {
  if (loading.value) return
  input.value = q
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', text })
  messages.value.push({ role: 'assistant', text: '' })
  const assistantIndex = messages.value.length - 1
  await scrollToBottom()
  loading.value = true
  statusText.value = '连接中…'
  let gotToken = false

  try {
    await chatStreamApi(text, async (ev) => {
      if (ev.type === 'status') {
        statusText.value = ev.content || ''
        return
      }
      if (ev.type === 'token' && ev.content) {
        gotToken = true
        statusText.value = ''
        messages.value[assistantIndex].text += ev.content
        await scrollToBottom()
        return
      }
      if (ev.type === 'error') {
        statusText.value = ''
        ElMessage.error(ev.content || '流式失败')
        return
      }
      if (ev.type === 'done') {
        statusText.value = ''
        const answer =
          ev.answer || messages.value[assistantIndex].text || '（无回复）'
        if (gotToken) {
          messages.value[assistantIndex].text = answer
          await scrollToBottom()
        } else {
          await typeOut(assistantIndex, answer)
        }
      }
    })
  } catch (e) {
    console.error(e)
    statusText.value = ''
    const tip = e.message || '发送失败'
    ElMessage.error(tip)
    if (!messages.value[assistantIndex].text) {
      messages.value[assistantIndex].text = `（失败：${tip}）`
    }
    if (tip.includes('登录已失效')) {
      location.href = '/login'
    }
  } finally {
    loading.value = false
    statusText.value = ''
  }
}

onMounted(() => {
  warmupAgent().catch(() => {})
  loadHistory()
})
</script>

<template>
  <div class="page-panel chat-panel">
    <div class="title-row">
      <h2 class="page-title">智能助手</h2>
      <span v-if="roleHint" class="role-hint">{{ roleHint }}</span>
    </div>

    <div class="quick" v-if="!loading || messages.length > 0">
      <button
        v-for="q in quickPrompts"
        :key="q"
        type="button"
        class="quick-btn"
        :disabled="loading"
        @click="useQuick(q)"
      >
        {{ q }}
      </button>
    </div>

    <div class="msg-list" v-loading="loading && messages.length === 0" ref="listRef">
      <p class="empty" v-if="!loading && messages.length === 0">
        试试下方快捷问法，或直接问「某项目待整改几条」
      </p>
      <ul class="info">
        <li v-for="(item, index) in messages" :key="index" :class="item.role">
          <div class="bubble">
            <b>{{ item.role === 'user' ? '我' : '助手' }}</b>
            <span>{{ item.text }}</span>
            <span
              v-if="item.role === 'assistant' && loading && index === messages.length - 1"
              class="cursor"
              >|</span
            >
          </div>
        </li>
      </ul>
      <p v-if="statusText" class="status">{{ statusText }}</p>
    </div>
    <div class="bottom">
      <el-input
        v-model="input"
        placeholder="说点什么，例如：给我工作台总览"
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
  height: calc(100vh - 56px - 48px);
  max-height: calc(100vh - 56px - 48px);
  overflow: hidden;
}
.title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}
.chat-panel .page-title {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: none;
}
.role-hint {
  font-size: 12px;
  color: var(--wb-accent);
  background: var(--wb-accent-soft);
  border-radius: 999px;
  padding: 2px 10px;
  white-space: nowrap;
}
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  flex-shrink: 0;
}
.quick-btn {
  border: 1px solid var(--wb-border);
  background: var(--wb-card);
  color: var(--wb-text);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}
.quick-btn:hover:not(:disabled) {
  border-color: var(--wb-accent);
  background: var(--wb-accent-soft);
  color: var(--wb-accent);
}
.quick-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.msg-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  background: var(--wb-chat-bg);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-md);
  padding: 16px;
}
.empty {
  display: flex;
  margin: 0;
  height: 100%;
  min-height: 160px;
  justify-content: center;
  align-items: center;
  color: var(--wb-muted);
  font-size: 14px;
}
.info {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info li {
  display: flex;
  width: 100%;
}
.info li.user {
  justify-content: flex-end;
}
.info li.assistant {
  justify-content: flex-start;
}
.bubble {
  max-width: min(78%, 520px);
  line-height: 1.55;
  white-space: pre-wrap;
  padding: 10px 14px;
  border-radius: var(--wb-radius-md);
  border: 1px solid var(--wb-border);
  background: var(--wb-card);
  box-shadow: var(--wb-shadow);
}
.info li.user .bubble {
  background: var(--wb-accent-soft);
  border-color: rgba(29, 107, 92, 0.22);
  border-bottom-right-radius: 4px;
}
.info li.assistant .bubble {
  border-bottom-left-radius: 4px;
}
.bubble b {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--wb-muted);
}
.cursor {
  display: inline-block;
  margin-left: 1px;
  animation: blink 1s step-end infinite;
  color: var(--wb-accent);
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
.status {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--wb-muted);
}
.bottom {
  flex-shrink: 0;
  margin-top: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
  padding-top: 4px;
}
.bottom .el-button {
  flex-shrink: 0;
  min-width: 80px;
}
</style>
