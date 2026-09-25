import request from '@/utils/request'

export const getprojects = (params) => {
  return request.get('/api/project/list', { params })
}

export const getgap_project_id = (params) => {
  return request.get('/api/project/list/gap', { params })
}

export const postGapAction = (gapId, data) => {
  return request.post(`/api/project/gap/${gapId}/action`, data)
}

export const getGapLogs = (gapId) => {
  return request.get(`/api/project/gap/${gapId}/logs`)
}

export const post_add_project = (data) => {
  return request.post(`/api/project/create`,data)
}

export const post_add_member = (data) =>{
  return request.post('/api/project/member', data)
}

export const get_alluser = (params) => {
  return request.get('/api/project/alluser', { params })
}

export const delete_member = (data) => {
  return request.delete('/api/project/member', { data })
}

export const get_gapscount = (params) => {
  return request.get('/api/project/gap_status_count', { params })
}

export const post_create_gap = (data) => {
  return request.post('/api/project/gap/create', data)
}

