<template>
  <div v-loading="loading">
    <div class="card">
      <div class="card-title">
        <span>接口详情</span>
        <span style="float: right;">
          <el-button type="primary" v-if="detail.status === 'published'" @click="showTestDialog = true">测试接口</el-button>
          <el-button type="success" v-if="detail.status === 'draft'" @click="handlePublish">发布</el-button>
          <el-button type="warning" v-else-if="detail.status === 'published'" @click="handleUnpublish">下架</el-button>
          <el-button @click="$router.push('/apis')">返回</el-button>
        </span>
      </div>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="接口名称">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <span :class="'status-tag status-' + detail.status">
            {{ detail.status === 'published' ? '已发布' : '草稿' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="请求方法">
          <span :class="'method-tag method-' + detail.method?.toLowerCase()">{{ detail.method }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="接口路径">
          <code>{{ detail.path }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="后端地址" :span="2">{{ detail.backend_url }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ detail.description || '暂无描述' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 参数配置 -->
    <div class="card" v-if="detail.request_params && detail.request_params.length">
      <div class="card-title">请求参数</div>
      <el-table :data="detail.request_params" stripe>
        <el-table-column prop="name" label="参数名" width="150">
          <template #default="{ row }">
            <span class="param-name">{{ row.name }}</span>
            <span v-if="row.required" style="color: #f56c6c; margin-left: 5px;">*</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <span class="param-type">{{ row.type }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="required" label="必填" width="80">
          <template #default="{ row }">
            {{ row.required ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
      </el-table>
    </div>

    <!-- 授权管理 -->
    <div class="card">
      <div class="card-title">
        <span>授权应用</span>
        <el-button text type="primary" @click="showGrantDialog = true">➕ 添加授权</el-button>
      </div>
      <el-table :data="accessList" v-if="accessList.length">
        <el-table-column prop="app_id" label="应用ID" />
        <el-table-column prop="created_at" label="授权时间" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button text type="danger" @click="handleRevoke(row.app_id)">取消授权</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无授权应用" :image-size="60" />
    </div>

    <!-- 添加授权弹窗 -->
    <el-dialog v-model="showGrantDialog" title="添加授权" width="400px">
      <el-form label-width="80px">
        <el-form-item label="选择应用">
          <el-select v-model="grantForm.appId" placeholder="请选择应用" style="width: 100%;">
            <el-option 
              v-for="app in appList" 
              :key="app.id" 
              :label="app.name" 
              :value="app.id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGrantDialog = false">取消</el-button>
        <el-button type="primary" @click="handleGrant">确定</el-button>
      </template>
    </el-dialog>

    <!-- 测试接口弹窗 -->
    <el-dialog v-model="showTestDialog" title="测试接口" width="700px" @close="testResult = null">
      <div v-if="detail.status !== 'published'" style="text-align: center; padding: 20px;">
        <el-alert type="warning" title="只有已发布的接口才能测试" :closable="false" />
      </div>
      <template v-else>
        <el-form label-width="100px">
          <el-form-item label="请求方法">
            <el-select v-model="testForm.method" style="width: 150px;">
              <el-option label="GET" value="GET" />
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
              <el-option label="DELETE" value="DELETE" />
              <el-option label="PATCH" value="PATCH" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="请求参数" v-if="detail.request_params && detail.request_params.length">
            <el-row :gutter="10" v-for="param in detail.request_params" :key="param.name" style="margin-bottom: 10px;">
              <el-col :span="6">
                <el-tag size="small">{{ param.name }}</el-tag>
                <span v-if="param.required" style="color: #f56c6c;"> *</span>
              </el-col>
              <el-col :span="12">
                <el-input 
                  v-model="testForm.query_params[param.name]" 
                  :placeholder="param.description || param.type"
                  size="small"
                />
              </el-col>
            </el-row>
          </el-form-item>
          
          <el-form-item label="请求体" v-if="['POST', 'PUT', 'PATCH'].includes(testForm.method)">
            <el-input 
              v-model="testForm.body" 
              type="textarea" 
              :rows="5"
              placeholder='{"key": "value"}'
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" :loading="testLoading" @click="testApi">发送请求</el-button>
          </el-form-item>
        </el-form>
        
        <!-- 测试结果 -->
        <div v-if="testResult" class="test-result">
          <el-divider content-position="left">响应结果</el-divider>
          <el-alert 
            :type="testResult.status_code < 400 ? 'success' : 'error'" 
            :title="'状态码: ' + testResult.status_code"
            :closable="false"
            style="margin-bottom: 10px;"
          />
          <div v-if="testResult.debug_url" style="color: #909399; margin-bottom: 10px;">
            请求URL: <code>{{ testResult.debug_url }}</code>
          </div>
          <div v-if="testResult.latency_ms" style="color: #909399; margin-bottom: 10px;">
            耗时: {{ testResult.latency_ms }}ms
          </div>
          <pre v-if="testResult.body">{{ typeof testResult.body === 'object' ? JSON.stringify(testResult.body, null, 2) : testResult.body }}</pre>
          <pre v-if="testResult.error" style="color: #f56c6c;">{{ testResult.error }}</pre>
          <!-- 调试信息 -->
          <el-divider content-position="left">调试信息</el-divider>
          <pre style="background: #f5f5f5; padding: 10px; font-size: 11px;">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiApi, appApi } from '../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref({})
const accessList = ref([])
const appList = ref([])
const showGrantDialog = ref(false)
const showTestDialog = ref(false)
const testLoading = ref(false)
const testResult = ref(null)
const grantForm = reactive({
  appId: ''
})

// 测试相关
const testForm = reactive({
  method: 'GET',
  query_params: {},
  body: ''
})

const testApi = async () => {
  try {
    testLoading.value = true
    testResult.value = null
    
    // 构建 query_params
    const queryParams = {}
    if (detail.value.request_params) {
      detail.value.request_params.forEach(p => {
        if (p.name && testForm.query_params[p.name]) {
          queryParams[p.name] = testForm.query_params[p.name]
        }
      })
    }
    
    const data = {
      method: testForm.method,
      query_params: queryParams,
      body: testForm.body || null
    }
    
    // 直接使用 axios 获取完整响应
    const token = localStorage.getItem('token')
    const response = await fetch(`http://localhost:8001/api/openapis/${route.params.id}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    })
    
    const result = await response.json()
    testResult.value = result
    
  } catch (error) {
    testResult.value = {
      error: error.message || '请求失败',
      status_code: 500
    }
  } finally {
    testLoading.value = false
  }
}

const loadDetail = async () => {
  try {
    loading.value = true
    const [detailRes, accessRes, appsRes] = await Promise.all([
      apiApi.get(route.params.id),
      apiApi.listAccess(route.params.id),
      appApi.list(1, 100)
    ])
    detail.value = detailRes
    accessList.value = accessRes
    appList.value = appsRes.items
  } catch (error) {
    ElMessage.error('加载失败: ' + error)
  } finally {
    loading.value = false
  }
}

const handlePublish = async () => {
  try {
    await apiApi.publish(route.params.id)
    ElMessage.success('发布成功')
    loadDetail()
  } catch (error) {
    ElMessage.error('发布失败: ' + error)
  }
}

const handleUnpublish = async () => {
  try {
    await apiApi.unpublish(route.params.id)
    ElMessage.success('下架成功')
    loadDetail()
  } catch (error) {
    ElMessage.error('下架失败: ' + error)
  }
}

const handleGrant = async () => {
  if (!grantForm.appId) {
    ElMessage.warning('请选择应用')
    return
  }
  try {
    await apiApi.grantAccess(route.params.id, grantForm.appId)
    ElMessage.success('授权成功')
    showGrantDialog.value = false
    grantForm.appId = ''
    loadDetail()
  } catch (error) {
    ElMessage.error('授权失败: ' + error)
  }
}

const handleRevoke = async (appId) => {
  try {
    await ElMessageBox.confirm('确定要取消该应用的授权吗？', '提示', { type: 'warning' })
    await apiApi.revokeAccess(route.params.id, appId)
    ElMessage.success('取消授权成功')
    loadDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消授权失败: ' + error)
    }
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.test-result {
  margin-top: 20px;
}
.test-result pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 300px;
  font-size: 12px;
}
</style>
