import request from '@/utils/request'

export const getRecords = (params) => {
  return request.get('/api/chat/records', { params })
}

export const postChat = (user_input) => {
  return request.post('/api/chat', { user_input })
}
