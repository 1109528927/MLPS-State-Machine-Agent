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
    if (error.response?.status === 401) {
      const url = String(error.config?.url || '')
      // 登录接口本身的 401（账号密码错误）交给 Login.vue 弹提示，不要整页跳转
      const isLoginRequest = url.includes('/api/user/login')
      const onLoginPage = location.pathname === '/login' || location.pathname.endsWith('/login')
      if (!isLoginRequest) {
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        if (!onLoginPage) {
          location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

export default instance
