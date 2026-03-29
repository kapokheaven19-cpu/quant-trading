<template>
  <div class="auth-form card">
    <h2>{{ isRegister ? '注册' : '登录' }}</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>用户名</label>
        <input v-model="form.username" required />
      </div>
      <div class="form-group" v-if="isRegister">
        <label>邮箱</label>
        <input v-model="form.email" type="email" required />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="form.password" type="password" required />
      </div>
      <button type="submit" class="btn btn-primary" style="width: 100%;">
        {{ isRegister ? '注册' : '登录' }}
      </button>
    </form>
    <p class="text-light mt-4" style="text-align: center;">
      {{ isRegister ? '已有账号？' : '没有账号？' }}
      <a href="#" @click.prevent="isRegister = !isRegister" style="color: var(--primary);">
        {{ isRegister ? '登录' : '注册' }}
      </a>
    </p>
  </div>
</template>

<script>
import { auth } from '../api'
export default {
  name: 'Login',
  data() {
    return {
      isRegister: false,
      form: {
        username: '',
        email: '',
        password: ''
      }
    }
  },
  methods: {
    async handleSubmit() {
      try {
        if (this.isRegister) {
          await auth.register(this.form)
          this.isRegister = false
          alert('注册成功，请登录')
        } else {
          const { data } = await auth.login(this.form.username, this.form.password)
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          this.$router.push('/')
        }
      } catch (e) {
        alert(e.response?.data?.detail || '操作失败')
      }
    }
  }
}
</script>
