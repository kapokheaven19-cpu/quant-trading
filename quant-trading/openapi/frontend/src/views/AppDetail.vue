<template>
  <div>
    <div class="card">
      <div class="header">
        <el-button text @click="$router.back()">← 返回</el-button>
        <h2>{{ app?.name }}</h2>
      </div>

      <el-descriptions :column="2" border v-if="app">
        <el-descriptions-item label="AppID">
          <code>{{ app.app_id }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="app.is_active ? 'success' : 'danger'">
            {{ app.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ app.description || '无' }}
        </el-descriptions-item>
        <el-descriptions-item label="AppSecret">
          <code>{{ showSecret ? app.app_secret : '••••••••' }}</code>
          <el-button text type="primary" size="small" @click="showSecret = !showSecret">
            {{ showSecret ? '隐藏' : '显示' }}
          </el-button>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ app.created_at }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="card">
      <div class="table-toolbar">
        <h3>API 列表</h3>
        <el-button type="primary" @click="$router.push('/apis/create?app_id=' + appId)">添加 API</el-button>
      </div>

      <el-table :data="apiList" v-loading="apiLoading">
        <el-table-column prop="name" label="API 名称" />
        <el-table-column prop="path" label="路径" width="250">
          <template #default="{ row }">
            <code>{{ row.method }} {{ row.path }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push('/apis/' + row.id)">查看</el-button>
            <el-button text type="danger" @click="handleDeleteApi(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appApi, apiApi } from '../api'

const route = useRoute()
const appId = route.params.id

const app = ref(null)
const apiList = ref([])
const loading = ref(false)
const apiLoading = ref(false)
const showSecret = ref(false)

const loadApp = async () => {
  try {
    loading.value = true
    app.value = await appApi.get(appId)
  } catch (error) {
    ElMessage.error('加载失败: ' + error)
  } finally {
    loading.value = false
  }
}

const loadApis = async () => {
  try {
    apiLoading.value = true
    const res = await apiApi.list(1, 100, '', '', appId)
    apiList.value = res.items
  } catch (error) {
    ElMessage.error('加载 API 列表失败: ' + error)
  } finally {
    apiLoading.value = false
  }
}

const handleDeleteApi = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该 API 吗？', '提示', { type: 'warning' })
    await apiApi.delete(id)
    ElMessage.success('删除成功')
    loadApis()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error)
    }
  }
}

onMounted(() => {
  loadApp()
  loadApis()
})
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.header h2 {
  margin: 0;
}
</style>
