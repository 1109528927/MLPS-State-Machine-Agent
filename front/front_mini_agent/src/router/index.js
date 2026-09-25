import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue') },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),  // 父级
    redirect: '/project',
    children: [
      { path: 'project', name: 'project', component: () =>import('@/views/project/project.vue') },
      { path: 'project/:id/gaps', name: 'gap', component: () => import('@/views/project/gaps.vue') },
      { path: 'chat', name: 'chat', component: () =>import('@/views/Chat.vue')},
      { path: 'users/create', name: 'userCreate', component: () => import('@/views/user/CreateUser.vue') },
      { path: 'project/create', name: 'projectcreate', component: () => import('@/views/project/create_project.vue')},
      { path: 'project/devideuser', name: 'projectdeviedeuser', component: () => import('@/views/project/devide_member.vue')}
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path === '/login') {
    // 已登录还去登录页 → 可直接进工作台
    if (token) return next('/project')
    return next()
  }
  if (!token) {
    // 没登录去业务页 → 踢回登录
    return next('/login')
  }
  next() // 放行
})

export default router
