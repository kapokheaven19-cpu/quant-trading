<template>
  <div>
    <div class="card">
      <div class="flex-between">
        <h2>OAuth 应用</h2>
        <button class="btn btn-primary" @click="showForm = true">创建应用</button>
      </div>
    </div>

    <div v-if="showForm" class="card">
      <h3>新建 OAuth 应用</h3>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>应用名称</label>
          <input v-model="form.name" required />
        </div>
        <div class="form-group">
          <label>回调地址（每行一个）</label>
          <textarea v-model="form.redirect_uris_text" placeholder="https://example.com/callback"></textarea>
        </div>
        <div class="form-group">
          <label>授权类型</label>
          <select v-model="form.grant_types" multiple>
            <option value="authorization_code">授权码模式</option>
            <option value="client_credentials">客户端模式</option>
          </select>
        </div>
        <div class="form-group">
          <label>Scopes</label>
          <input v-model="form.scopes_text" placeholder="read, write" />
        </div>
        <div class="flex">
          <button type="submit" class="btn btn-primary">创建</button>
          <button type="button" class="btn" @click="showForm = false">取消</button>
        </div>
      </form>
    </div>

    <div v-if="newApp" class="card" style="background: #f0fdf4;">
      <h3 style="color: #166534;">新应用已创建</h3>
      <p class="text-light">请妥善保存，密钥只会显示一次</p>
      <div class="code mt-4">
        Client ID: {{ newApp.client_id }}<br>
        Client Secret: {{ newApp.client_secret }}
      </div>
      <button class="btn btn-primary mt-4" @click="newApp = null">我已保存</button>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>应用名称</th>
            <th>Client ID</th>
            <th>回调地址</th>
            <th>Scopes</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="app in apps" :key="app.id">
            <td>{{ app.name }}</td>
            <td class="code">{{ app.client_id }}</td>
            <td>{{ app.redirect_uris?.join(', ') || '-' }}</td>
            <td>{{ app.scopes?.join(', ') || '-' }}</td>
            <td>
              <button class="btn btn-sm btn-danger" @click="deleteApp(app.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!apps.length" class="text-light" style="text-align: center; padding: 20px;">
        暂无应用
      </p>
    </div>
  </div>
</template>

<script>
import { oauthApps } from '../api'
export default {
  name: 'OAuthApps',
  data() {
    return {
      apps: [],
      showForm: false,
      newApp: null,
      form: {
        name: '',
        redirect_uris_text: '',
        grant_types: ['authorization_code'],
        scopes_text: 'read'
      }
    }
  },
  mounted() {
    this.loadApps()
  },
  methods: {
    async loadApps() {
      try {
        const { data } = await oauthApps.list()
        this.apps = data
      } catch (e) {
        console.error(e)
      }
    },
    async handleSubmit() {
      try {
        const data = {
          name: this.form.name,
          redirect_uris: this.form.redirect_uris_text.split('\n').filter(u => u.trim()),
          grant_types: this.form.grant_types,
          scopes: this.form.scopes_text.split(',').map(s => s.trim()).filter(s => s)
        }
        const { data: newApp } = await oauthApps.create(data)
        this.newApp = newApp
        this.showForm = false
        this.loadApps()
      } catch (e) {
        alert(e.response?.data?.detail || '创建失败')
      }
    },
    async deleteApp(id) {
      if (!confirm('确定删除？')) return
      try {
        await oauthApps.delete(id)
        this.loadApps()
      } catch (e) {
        alert('删除失败')
      }
    }
  }
}
</script>
