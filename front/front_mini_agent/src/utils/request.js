import axios from 'axios'

const instance=axios.create({
    baseURL:'',
    timeout: 10000,
})

// 添加请求拦截器
instance.interceptors.request.use(
  function (config) {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      // 若后端读自定义头，则改成：
      // config.headers.token = token
    }
    return config
  },
  function (error) {
    // 对请求错误做些什么
    return Promise.reject(error)
  },
)

// 添加响应拦截器
instance.interceptors.response.use(
  function (response) {
    // 2xx 范围内的状态码都会触发该函数。
    // 对响应数据做点什么
    return response
  },
  function (error) {
    // 迷你助手暂无登录；以后有 token 可在此处理 401 跳转
    if (error.response?.status === 401) { 
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      location.href = '/login'
     }
    return Promise.reject(error)
  },
)

export default instance
