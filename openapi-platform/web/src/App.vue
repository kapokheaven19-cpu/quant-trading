<template>
  <div v-if="isLoggedIn">
    <header class="header">
      <h1>OpenAPI Platform</h1>
      <nav class="nav">
        <router-link to="/">首页</router-link>
        <router-link to="/apis">接口管理</router-link>
        <router-link to="/api-keys">API密钥</router-link>
        <router-link to="/oauth-apps">OAuth应用</router-link>
        <a @click="logout">退出</a>
      </nav>
    </header>
    <main class="container">
      <router-view></router-view>
    </main>
  </div>
  <div v-else>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    isLoggedIn() {
      return !!localStorage.getItem('access_token')
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      this.$router.push('/login')
    }
  }
}
</script>
