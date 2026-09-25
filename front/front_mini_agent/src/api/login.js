import request from '@/utils/request'

export const post_register = (data) => {
  return request.post('/api/user/register', data)
}

export const post_login = (data) => {
  return request.post('/api/user/login', data)
}
