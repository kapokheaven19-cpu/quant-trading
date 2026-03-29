<template>
  <div>
    <div class="card">
      <div class="flex-between">
        <h2>托管接口</h2>
        <button class="btn btn-primary" @click="showForm = true">添加接口</button>
      </div>
    </div>

    <div v-if="showForm" class="card">
      <h3>{{ editingApi ? '编辑' : '新建' }}接口</h3>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>路径</label>
          <input v-model="form.path" placeholder="/my-api" required />
        </div>
        <div class="form-group">
          <label>方法</label>
          <select v-model="form.method" required>
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>DELETE</option>
          </select>
        </div>
        <div class="form-group">
          <label>目标URL</label>
          <input v-model="form.target_url" placeholder="https://api.example.com" required />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="form.description"></textarea>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="form.auth_required" /> 需要认证
          </label>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="form.is_public" /> 公开访问
          </label>
        </div>
        <div class="flex">
          <button type="submit" class="btn btn-primary">{{ editingApi ? '更新' : '创建' }}</button>
          <button type="button" class="btn" @click="closeForm">取消</button>
        </div>
      </form>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>方法</th>
            <th>路径</th>
            <th>目标URL</th>
            <th>认证</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="api in apis" :key="api.id">
            <td><span class="badge badge-success">{{ api.method }}</span></td>
            <td>{{ api.path }}</td>
            <td class="text-light">{{ api.target_url }}</td>
            <td>{{ api.auth_required ? '需要' : '可选' }}</td>
            <td>
              <div class="flex">
                <button class="btn btn-sm" @click="editApi(api)">编辑</button>
                <button class="btn btn-sm btn-danger" @click="deleteApi(api.id)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!apis.length" class="text-light" style="text-align: center; padding: 20px;">
        暂无接口
      </p>
    </div>
  </div>
</template>

<script>
import { managedApis } from '../api'
export default {
  name: 'ApiList',
  data() {
    return {
      apis: [],
      showForm: false,
      editingApi: null,
      form: {
        path: '',
        method: 'GET',
        target_url: '',
        description: '',
        auth_required: true,
        is_public: false
      }
    }
  },
  mounted() {
    this.loadApis()
  },
  methods: {
    async loadApis() {
      try {
        const { data } = await managedApis.list()
        this.apis = data
      } catch (e) {
        console.error(e)
      }
    },
    editApi(api) {
      this.editingApi = api
      this.form = { ...api }
      this.showForm = true
    },
    closeForm() {
      this.showForm = false
      this.editingApi = null
      this.form = {
        path: '',
        method: 'GET',
        target_url: '',
        description: '',
        auth_required: true,
        is_public: false
      }
    },
    async handleSubmit() {
      try {
        if (this.editingApi) {
          await managedApis.update(this.editingApi.id, this.form)
        } else {
          await managedApis.create(this.form)
        }
        this.loadApis()
        this.closeForm()
      } catch (e) {
        alert(e.response?.data?.detail || '操作失败')
      }
    },
    async deleteApi(id) {
      if (!confirm('确定删除？')) return
      try {
        await managedApis.delete(id)
        this.loadApis()
      } catch (e) {
        alert('删除失败')
      }
    }
  }
}
</script>
