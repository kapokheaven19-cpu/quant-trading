import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import Dashboard from '../views/Dashboard.vue'
import ApiList from '../views/ApiList.vue'
import ApiCreate from '../views/ApiCreate.vue'
import ApiDetail from '../views/ApiDetail.vue'
import AppList from '../views/AppList.vue'
import AppCreate from '../views/AppCreate.vue'
import AppDetail from '../views/AppDetail.vue'
import ApiDocs from '../views/ApiDocs.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: Dashboard },
      { path: 'apis', name: 'ApiList', component: ApiList },
      { path: 'apis/create', name: 'ApiCreate', component: ApiCreate },
      { path: 'apis/:id', name: 'ApiDetail', component: ApiDetail },
      { path: 'apps', name: 'AppList', component: AppList },
      { path: 'apps/create', name: 'AppCreate', component: AppCreate },
      { path: 'apps/:id', name: 'AppDetail', component: AppDetail },
      { path: 'docs', name: 'ApiDocs', component: ApiDocs }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
