<template>
  <div>
    <div class="card">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="form-section-title">基本信息</div>
          <el-form-item label="接口名称" prop="name">
            <el-input v-model="form.name" placeholder="如：获取用户信息" />
          </el-form-item>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="请求方法" prop="method">
                <el-select v-model="form.method" style="width: 100%;">
                  <el-option label="GET" value="GET" />
                  <el-option label="POST" value="POST" />
                  <el-option label="PUT" value="PUT" />
                  <el-option label="DELETE" value="DELETE" />
                  <el-option label="PATCH" value="PATCH" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="接口路径" prop="path">
                <el-input v-model="form.path" placeholder="/api/users" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="接口描述" prop="description">
            <el-input v-model="form.description" type="textarea" :rows="3" placeholder="接口功能描述" />
          </el-form-item>
        </div>

        <!-- 后端配置 -->
        <div class="form-section">
          <div class="form-section-title">后端配置</div>
          <el-form-item label="后端服务地址" prop="backend_url">
            <el-input v-model="form.backend_url" placeholder="如：https://api.example.com" />
            <div style="color: #999; font-size: 12px; margin-top: 5px;">实际的后端服务 URL，平台会将请求转发到此地址</div>
          </el-form-item>
        </div>

        <!-- 请求参数 -->
        <div class="form-section">
          <div class="form-section-title">
            请求参数 
            <el-button text type="primary" @click="addParam">➕ 添加参数</el-button>
          </div>
          <el-table :data="form.request_params" v-if="form.request_params && form.request_params.length">
            <el-table-column label="参数名" width="150">
              <template #default="{ row, $index }">
                <el-input v-model="row.name" placeholder="参数名" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-select v-model="row.type" size="small">
                  <el-option label="string" value="string" />
                  <el-option label="integer" value="integer" />
                  <el-option label="number" value="number" />
                  <el-option label="boolean" value="boolean" />
                  <el-option label="array" value="array" />
                  <el-option label="object" value="object" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="必填" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.required" />
              </template>
            </el-table-column>
            <el-table-column label="描述">
              <template #default="{ row }">
                <el-input v-model="row.description" placeholder="参数描述" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button text type="danger" @click="removeParam($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无请求参数" :image-size="60" />
        </div>

        <!-- 响应示例 -->
        <div class="form-section">
          <div class="form-section-title">响应示例</div>
          <el-form-item label="响应示例">
            <el-input v-model="responseExample" type="textarea" :rows="5" placeholder='{"code": 200, "data": {...}}' />
          </el-form-item>
        </div>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">创建</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiApi } from '../api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const responseExample = ref('')

const form = reactive({
  name: '',
  method: 'GET',
  path: '',
  description: '',
  backend_url: '',
  request_params: []
})

const rules = {
  name: [{ required: true, message: '请输入接口名称', trigger: 'blur' }],
  method: [{ required: true, message: '请选择请求方法', trigger: 'change' }],
  path: [
    { required: true, message: '请输入接口路径', trigger: 'blur' },
    { pattern: /^\/[\w\-/]*$/, message: '路径必须以 / 开头', trigger: 'blur' }
  ],
  backend_url: [{ required: true, message: '请输入后端服务地址', trigger: 'blur' }]
}

const addParam = () => {
  if (!form.request_params) form.request_params = []
  form.request_params.push({
    name: '',
    type: 'string',
    required: false,
    description: ''
  })
}

const removeParam = (index) => {
  form.request_params.splice(index, 1)
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    
    const data = {
      ...form,
      response_body: responseExample.value ? { example: responseExample.value } : null
    }
    
    await apiApi.create(data)
    ElMessage.success('创建成功')
    router.push('/apis')
  } catch (error) {
    ElMessage.error('创建失败: ' + error)
  } finally {
    loading.value = false
  }
}
</script>
