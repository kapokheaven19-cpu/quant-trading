<template>
  <div>
    <div class="card">
      <div class="header">
        <h2>API 文档</h2>
        <el-input 
          v-model="keyword" 
          placeholder="搜索 API" 
          style="width: 250px;"
          @keyup.enter="loadData"
        />
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="我的 API" name="my">
          <el-table :data="myApis" v-loading="loading">
            <el-table-column prop="name" label="接口名称" />
            <el-table-column label="路径" width="250">
              <template #default="{ row }">
                <span :class="'method-tag method-' + row.method.toLowerCase()">{{ row.method }}</span>
                <code style="margin-left: 8px;">{{ row.path }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'published' ? 'success' : 'info'">
                  {{ row.status === 'published' ? '已发布' : '草稿' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button text type="primary" @click="showDoc(row)">查看文档</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="市场 API" name="market">
          <el-empty description="API 市场功能开发中" />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- API 文档对话框 -->
    <el-dialog v-model="docVisible" :title="currentApi?.name" width="700px">
      <div v-if="currentApi" class="api-doc">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="接口名称">{{ currentApi.name }}</el-descriptions-item>
          <el-descriptions-item label="请求方法">
            <span :class="'method-tag method-' + currentApi.method.toLowerCase()">{{ currentApi.method }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="接口路径"><code>{{ currentApi.path }}</code></el-descriptions-item>
          <el-descriptions-item label="后端地址">{{ currentApi.backend_url }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ currentApi.description || '无' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentApi.request_params && currentApi.request_params.length" class="doc-section">
          <h4>请求参数</h4>
          <el-table :data="currentApi.request_params" size="small">
            <el-table-column prop="name" label="参数名" width="120" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                {{ row.required ? '是' : '否' }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>

        <div v-if="currentApi.response_body" class="doc-section">
          <h4>响应示例</h4>
          <pre>{{ JSON.stringify(currentApi.response_body, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { apiApi } from '../api'

const keyword = ref('')
const activeTab = ref('my')
const myApis = ref([])
const loading = ref(false)
const docVisible = ref(false)
const currentApi = ref(null)

const loadData = async () => {
  try {
    loading.value = true
    const res = await apiApi.list(1, 100, '', keyword.value)
    myApis.value = res.items
  } catch (error) {
    ElMessage.error('加载失败: ' + error)
  } finally {
    loading.value = false
  }
}

const showDoc = (api) => {
  currentApi.value = api
  docVisible.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header h2 {
  margin: 0;
}
.doc-section {
  margin-top: 20px;
}
.doc-section h4 {
  margin-bottom: 10px;
}
.doc-section pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
