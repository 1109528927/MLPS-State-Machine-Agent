import request from '@/utils/request'

export const post_register = (data) => {
  return request.post('/api/user/register', data)
}

export const post_login = (data) => {
  return request.post('/api/user/login', data)
}

/** 经理：用户列表（分配成员下拉） */
export const get_user_list = () => {
  return request.get('/api/user/list')
}
