import request from '@/utils/request'

/** 登录后触发后端 Agent 预热（后台跑，不阻塞页面） */
export const warmupAgent = () => {
  return request.post('/api/chat/warmup')
}

export const getRecords = (params) => {
  return request.get('/api/chat/records', { params })
}

export const postChat = (user_input) => {
  return request.post('/api/chat', { user_input })
}

/**
 * 流式对话 POST /api/chat/stream（SSE）
 * onEvent({ type: 'token'|'status'|'done'|'error', content?, answer? })
 */
export async function chatStreamApi(user_input, onEvent) {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ user_input }),
  })
  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    throw new Error('登录已失效，请重新登录')
  }
  if (!res.ok || !res.body) throw new Error('流式接口请求失败')

  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    const payload = await res.json().catch(() => null)
    throw new Error(payload?.message || payload?.detail || '流式接口返回异常')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() || ''
    for (const frame of frames) {
      const line = frame.split('\n').find((l) => l.trim().startsWith('data:'))
      if (!line) continue
      const raw = line.trim().slice(5).trim()
      if (!raw) continue
      onEvent(JSON.parse(raw))
    }
  }
}
