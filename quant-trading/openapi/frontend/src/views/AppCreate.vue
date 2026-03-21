<template>
  <div>
    <div class="card">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="应用名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入应用名称" />
        </el-form-item>
        <el-form-item label="应用描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入应用描述" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">创建</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 创建成功提示 -->
    <el-dialog v-model="showSecretDialog" title="应用创建成功" width="500px" :close-on-click-modal="false" :show-close="false">
      <el-alert title="请妥善保存以下信息" type="warning" :closable="false" style="margin-bottom: 20px;">
        AppSecret 只会在创建时显示一次，请立即保存！
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="AppID">
          <el-input v-model="createdApp.app_id" readonly />
        </el-form-item>
        <el-form-item label="AppSecret">
          <el-input v-model="createdApp.app_secret" readonly />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="handleCopied">我已保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { appApi } from '../api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const showSecretDialog = ref(false)
const createdApp = reactive({
  app_id: '',
  app_secret: ''
})

const form = reactive({
  name: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入应用名称', trigger: 'blur' }]
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    
    const res = await appApi.create(form)
    
    // 显示 AppSecret
    createdApp.app_id = res.app_id
    createdApp.app_secret = res.app_secret
    showSecretDialog.value = true
  } catch (error) {
    ElMessage.error('创建失败: ' + error)
  } finally {
    loading.value = false
  }
}

const handleCopied = () => {
  showSecretDialog.value = false
  router.push('/apps')
}
</script>
