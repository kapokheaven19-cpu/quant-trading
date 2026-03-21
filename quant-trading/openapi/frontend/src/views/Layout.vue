<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">OpenAPI 平台</div>
      <div class="sidebar-menu">
        <router-link to="/dashboard" class="menu-item" :class="{ active: route.path === '/dashboard' }">
          <span class="menu-icon">📊</span>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/apis" class="menu-item" :class="{ active: route.path.startsWith('/apis') }">
          <span class="menu-icon">🔌</span>
          <span>接口管理</span>
        </router-link>
        <router-link to="/apps" class="menu-item" :class="{ active: route.path.startsWith('/apps') }">
          <span class="menu-icon">📱</span>
          <span>应用管理</span>
        </router-link>
        <router-link to="/docs" class="menu-item" :class="{ active: route.path === '/docs' }">
          <span class="menu-icon">📚</span>
          <span>接口文档</span>
        </router-link>
      </div>
    </div>
    
    <!-- 主体内容 -->
    <div class="main-content">
      <div class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <div class="header-user">
          <span>{{ username }}</span>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </div>
      <div class="content-wrapper">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/apis': '接口管理',
    '/apis/create': '创建接口',
    '/apps': '应用管理',
    '/apps/create': '创建应用',
    '/docs': '接口文档'
  }
  return titles[route.path] || 'OpenAPI 平台'
})

const username = computed(() => {
  return localStorage.getItem('username') || '用户'
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>
