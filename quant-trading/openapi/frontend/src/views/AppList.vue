<template>
  <div>
    <div class="card">
      <div class="table-toolbar">
        <el-input 
          v-model="keyword" 
          placeholder="搜索应用名称" 
          style="width: 250px;"
          @keyup.enter="loadData"
        />
        <el-button type="primary" @click="$router.push('/apps/create')">创建应用</el-button>
      </div>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="name" label="应用名称" />
        <el-table-column prop="app_id" label="AppID" width="340">
          <template #default="{ row }">
            <code>{{ row.app_id }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push('/apps/' + row.id)">查看</el-button>
            <el-button text type="warning" @click="handleResetSecret(row.id)">重置密钥</el-button>
            <el-button text type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end;"
        @change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appApi } from '../api'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const keyword = ref('')

const loadData = async () => {
  try {
    loading.value = true
    const res = await appApi.list(page.value, pageSize.value)
    list.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error('加载失败: ' + error)
  } finally {
    loading.value = false
  }
}

const handleResetSecret = async (id) => {
  try {
    await ElMessageBox.confirm('确定要重置应用密钥吗？重置后旧密钥将失效。', '提示', { type: 'warning' })
    const res = await appApi.resetSecret(id)
    ElMessageBox.alert(`新的 AppSecret: ${res.app_secret}`, '密钥已重置', {
      confirmButtonText: '我知道了',
      type: 'success'
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败: ' + error)
    }
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该应用吗？', '提示', { type: 'warning' })
    await appApi.delete(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>
