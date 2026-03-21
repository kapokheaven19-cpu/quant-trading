<template>
  <div>
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: #409eff; color: white;">🔌</div>
        <div class="stat-info">
          <h3>{{ stats.apiCount }}</h3>
          <p>接口数量</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #67c23a; color: white;">📱</div>
        <div class="stat-info">
          <h3>{{ stats.appCount }}</h3>
          <p>应用数量</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #e6a23c; color: white;">📤</div>
        <div class="stat-info">
          <h3>{{ stats.publishedCount }}</h3>
          <p>已发布接口</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #f56c6c; color: white;">📊</div>
        <div class="stat-info">
          <h3>{{ stats.callCount }}</h3>
          <p>调用次数</p>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="card">
      <div class="card-title">快速操作</div>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-button type="primary" style="width: 100%; height: 60px;" @click="$router.push('/apis/create')">
            <span style="font-size: 20px;">➕</span>
            <span style="margin-left: 10px;">创建接口</span>
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="success" style="width: 100%; height: 60px;" @click="$router.push('/apps/create')">
            <span style="font-size: 20px;">📱</span>
            <span style="margin-left: 10px;">创建应用</span>
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="warning" style="width: 100%; height: 60px;" @click="$router.push('/docs')">
            <span style="font-size: 20px;">📚</span>
            <span style="margin-left: 10px;">查看文档</span>
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button type="info" style="width: 100%; height: 60px;" @click="showTokenDialog = true">
            <span style="font-size: 20px;">🔑</span>
            <span style="margin-left: 10px;">获取 Token</span>
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 最近创建的接口 -->
    <div class="card">
      <div class="card-title">最近创建的接口</div>
      <el-table :data="recentApis" v-if="recentApis.length">
        <el-table-column prop="name" label="接口名称" />
        <el-table-column prop="path" label="接口路径" width="250">
          <template #default="{ row }">
            <span :class="'method-tag method-' + row.method.toLowerCase()">{{ row.method }}</span>
            <span style="margin-left: 10px;">{{ row.path }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <span :class="'status-tag status-' + row.status">{{ row.status === 'published' ? '已发布' : '草稿' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
      <div v-else class="empty-state">
        <p>暂无接口，<el-button type="primary" text @click="$router.push('/apis/create')">立即创建</el-button></p>
      </div>
    </div>

    <!-- Token 获取弹窗 -->
    <el-dialog v-model="showTokenDialog" title="获取访问 Token" width="500px">
      <el-form label-width="100px">
        <el-form-item label="选择应用">
          <el-select v-model="tokenForm.appId" placeholder="请选择应用" style="width: 100%;">
            <el-option 
              v-for="app in appList" 
              :key="app.id" 
              :label="app.name" 
              :value="app.id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <el-alert v-if="generatedToken" title="生成的 Token" type="success" :closable="false" style="margin-top: 15px;">
        <code>{{ generatedToken }}</code>
      </el-alert>
      <template #footer>
        <el-button @click="showTokenDialog = false">关闭</el-button>
        <el-button type="primary" :loading="tokenLoading" @click="generateToken">生成 Token</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { apiApi, appApi } from '../api'

const stats = reactive({
  apiCount: 0,
  appCount: 0,
  publishedCount: 0,
  callCount: 0
})

const recentApis = ref([])
const appList = ref([])
const showTokenDialog = ref(false)
const generatedToken = ref('')
const tokenLoading = ref(false)

const tokenForm = reactive({
  appId: ''
})

const loadStats = async () => {
  try {
    const [apisRes, appsRes] = await Promise.all([
      apiApi.list(1, 100),
      appApi.list(1, 100)
    ])
    
    stats.apiCount = apisRes.total
    stats.appCount = appsRes.total
    stats.publishedCount = apisRes.items.filter(a => a.status === 'published').length
    stats.callCount = 0  // TODO: 从日志接口获取
    
    recentApis.value = apisRes.items.slice(0, 5)
    appList.value = appsRes.items
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const generateToken = async () => {
  if (!tokenForm.appId) {
    ElMessage.warning('请选择应用')
    return
  }
  
  try {
    tokenLoading.value = true
    const app = appList.value.find(a => a.id === tokenForm.appId)
    // 简化：直接生成 JWT Token
    generatedToken.value = 'JWT_TOKEN_' + Date.now()
    ElMessage.success('Token 生成成功')
  } catch (error) {
    ElMessage.error('生成失败: ' + error)
  } finally {
    tokenLoading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>
