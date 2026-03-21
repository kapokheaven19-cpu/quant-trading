<template>
  <div>
    <!-- 工具栏 -->
    <div class="card">
      <div class="table-toolbar">
        <div>
          <el-input 
            v-model="keyword" 
            placeholder="搜索接口名称或路径" 
            style="width: 250px; margin-right: 10px;"
            @keyup.enter="loadData"
          />
          <el-select v-model="status" placeholder="接口状态" style="width: 120px; margin-right: 10px;" @change="loadData">
            <el-option label="全部" value="" />
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </div>
        <el-button type="primary" @click="$router.push('/apis/create')">创建接口</el-button>
      </div>

      <!-- 接口列表 -->
      <el-table :data="list" v-loading="loading">
        <el-table-column prop="name" label="接口名称" min-width="150" />
        <el-table-column label="接口路径" min-width="200">
          <template #default="{ row }">
            <span :class="'method-tag method-' + row.method.toLowerCase()">{{ row.method }}</span>
            <span style="margin-left: 10px; font-family: monospace;">{{ row.path }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="backend_url" label="后端地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <span :class="'status-tag status-' + row.status">
              {{ row.status === 'published' ? '已发布' : row.status === 'draft' ? '草稿' : '已废弃' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push('/apis/' + row.id)">查看</el-button>
            <el-button text type="success" v-if="row.status === 'draft'" @click="handlePublish(row.id)">发布</el-button>
            <el-button text type="warning" v-else-if="row.status === 'published'" @click="handleUnpublish(row.id)">下架</el-button>
            <el-button text type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
import { apiApi } from '../api'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const keyword = ref('')
const status = ref('')

const loadData = async () => {
  try {
    loading.value = true
    const res = await apiApi.list(page.value, pageSize.value, status.value, keyword.value)
    list.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error('加载失败: ' + error)
  } finally {
    loading.value = false
  }
}

const handlePublish = async (id) => {
  try {
    await apiApi.publish(id)
    ElMessage.success('发布成功')
    loadData()
  } catch (error) {
    ElMessage.error('发布失败: ' + error)
  }
}

const handleUnpublish = async (id) => {
  try {
    await apiApi.unpublish(id)
    ElMessage.success('下架成功')
    loadData()
  } catch (error) {
    ElMessage.error('下架失败: ' + error)
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该接口吗？', '提示', { type: 'warning' })
    await apiApi.delete(id)
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
