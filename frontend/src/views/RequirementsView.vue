<template>
  <div class="requirements-view">
    <div class="page-header">
      <h2>需求管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建需求
      </el-button>
    </div>

    <!-- Requirements List -->
    <el-card>
      <el-table :data="requirements" v-loading="loading">
        <el-table-column prop="title" label="需求标题" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewRequirement(row.id)">查看</el-button>
            <el-button size="small" type="primary" @click="parseRequirement(row.id)" :disabled="row.status === 'processing'">
              解析
            </el-button>
            <el-button size="small" type="danger" @click="deleteRequirement(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建需求" width="600px">
      <el-form :model="newRequirement" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="newRequirement.title" placeholder="请输入需求标题" />
        </el-form-item>
        <el-form-item label="描述" required>
          <el-input v-model="newRequirement.description" type="textarea" :rows="3" placeholder="请输入需求描述" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="newRequirement.content" type="textarea" :rows="10" placeholder="请输入详细需求内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createRequirement" :loading="creating">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/api'

interface Requirement {
  id: number
  title: string
  description: string
  content: string
  status: string
  created_at: string
}

const router = useRouter()
const requirements = ref<Requirement[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)

const newRequirement = ref({
  title: '',
  description: '',
  content: ''
})

onMounted(() => {
  loadRequirements()
})

const loadRequirements = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/v1/requirements/')
    requirements.value = response
  } catch (error) {
    ElMessage.error('加载需求列表失败')
  } finally {
    loading.value = false
  }
}

const createRequirement = async () => {
  if (!newRequirement.value.title || !newRequirement.value.description || !newRequirement.value.content) {
    ElMessage.warning('请填写完整信息')
    return
  }

  creating.value = true
  try {
    await api.post('/api/v1/requirements/', newRequirement.value)
    ElMessage.success('需求创建成功')
    showCreateDialog.value = false
    newRequirement.value = { title: '', description: '', content: '' }
    loadRequirements()
  } catch (error) {
    ElMessage.error('需求创建失败')
  } finally {
    creating.value = false
  }
}

const viewRequirement = (id: number) => {
  router.push(`/requirements/${id}`)
}

const parseRequirement = async (id: number) => {
  try {
    const response = await api.post(`/api/v1/requirements/${id}/parse`)
    ElMessage.success(response.message || '需求解析成功')
    loadRequirements()
  } catch (error) {
    ElMessage.error('需求解析失败')
  }
}

const deleteRequirement = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除此需求吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/api/v1/requirements/${id}`)
    ElMessage.success('删除成功')
    loadRequirements()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.requirements-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}
</style>