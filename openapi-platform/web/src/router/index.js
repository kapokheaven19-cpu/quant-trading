import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import ApiList from '../views/ApiList.vue'
import ApiKeyList from '../views/ApiKeyList.vue'
import OAuthApps from '../views/OAuthApps.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/apis', component: ApiList },
  { path: '/api-keys', component: ApiKeyList },
  { path: '/oauth-apps', component: OAuthApps }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
