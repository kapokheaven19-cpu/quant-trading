<template>
  <div>
    <div class="card">
      <div class="flex-between">
        <h2>API 密钥</h2>
        <button class="btn btn-primary" @click="createKey">创建密钥</button>
      </div>
    </div>

    <div v-if="newKey" class="card" style="background: #f0fdf4;">
      <h3 style="color: #166534;">新密钥已创建</h3>
      <p class="text-light">请妥善保存，密钥只会显示一次</p>
      <div class="code mt-4">
        App ID: {{ newKey.app_id }}<br>
        App Secret: {{ newKey.app_secret }}
      </div>
      <button class="btn btn-primary mt-4" @click="newKey = null">我已保存</button>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>App ID</th>
            <th>Scopes</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="key in keys" :key="key.id">
            <td>{{ key.name || '-' }}</td>
            <td class="code" style="display: inline-block;">{{ key.app_id }}</td>
            <td>{{ key.scopes?.join(', ') || '-' }}</td>
            <td>
              <span :class="['badge', key.is_active ? 'badge-success' : 'badge-danger']">
                {{ key.is_active ? '启用' : '禁用' }}
              </span>
            </td>
            <td>{{ new Date(key.created_at).toLocaleDateString() }}</td>
            <td>
              <div class="flex">
                <button class="btn btn-sm" @click="toggleKey(key.id)">
                  {{ key.is_active ? '禁用' : '启用' }}
                </button>
                <button class="btn btn-sm btn-danger" @click="deleteKey(key.id)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!keys.length" class="text-light" style="text-align: center; padding: 20px;">
        暂无密钥
      </p>
    </div>
  </div>
</template>

<script>
import { apiKeys } from '../api'
export default {
  name: 'ApiKeyList',
  data() {
    return {
      keys: [],
      newKey: null,
      form: {
        name: '',
        scopes: [],
        expires_at: null
      }
    }
  },
  mounted() {
    this.loadKeys()
  },
  methods: {
    async loadKeys() {
      try {
        const { data } = await apiKeys.list()
        this.keys = data
      } catch (e) {
        console.error(e)
      }
    },
    async createKey() {
      const name = prompt('请输入密钥名称:')
      if (!name) return
      try {
        const { data } = await apiKeys.create({ name, scopes: ['read'] })
        this.newKey = data
        this.loadKeys()
      } catch (e) {
        alert(e.response?.data?.detail || '创建失败')
      }
    },
    async toggleKey(id) {
      try {
        await apiKeys.toggle(id)
        this.loadKeys()
      } catch (e) {
        alert('操作失败')
      }
    },
    async deleteKey(id) {
      if (!confirm('确定删除？')) return
      try {
        await apiKeys.delete(id)
        this.loadKeys()
      } catch (e) {
        alert('删除失败')
      }
    }
  }
}
</script>
