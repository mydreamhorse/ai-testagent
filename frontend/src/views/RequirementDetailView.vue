<template>
  <div class="requirement-detail" v-loading="loading">
    <div class="page-header">
      <el-button @click="$router.go(-1)">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>{{ requirement?.title }}</h2>
    </div>

    <el-row :gutter="20" v-if="requirement">
      <!-- Requirement Info -->
      <el-col :span="16">
        <el-card title="需求详情">
          <template #header>
            <div class="card-header">
              <span>需求详情</span>
              <el-tag :type="getStatusType(requirement.status)">
                {{ getStatusText(requirement.status) }}
              </el-tag>
            </div>
          </template>
          
          <div class="requirement-info">
            <p><strong>描述：</strong>{{ requirement.description }}</p>
            <p><strong>创建时间：</strong>{{ formatDate(requirement.created_at) }}</p>
            <div class="content-section">
              <strong>详细内容：</strong>
              <div class="content">{{ requirement.content }}</div>
            </div>
          </div>
        </el-card>

        <!-- Parsed Features -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>解析特征 ({{ features.length }})</span>
              <el-button size="small" @click="loadFeatures">刷新</el-button>
            </div>
          </template>
          
          <el-table :data="features" v-if="features.length > 0">
            <el-table-column prop="feature_name" label="特征名称" />
            <el-table-column prop="feature_type" label="类型" width="120" />
            <el-table-column prop="priority" label="优先级" width="100">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small">
                  {{ row.priority }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
          </el-table>
          <el-empty v-else description="暂无解析特征" />
        </el-card>
      </el-col>

      <!-- Actions -->
      <el-col :span="8">
        <el-card title="操作">
          <template #header>
            <span>操作</span>
          </template>
          
          <div class="actions">
            <el-button 
              type="primary" 
              @click="parseRequirement" 
              :loading="parsing"
              :disabled="requirement.status === 'processing'"
              style="width: 100%; margin-bottom: 10px;"
            >
              解析需求
            </el-button>
            
            <el-button 
              type="success" 
              @click="generateTestCases" 
              :loading="generating"
              :disabled="features.length === 0"
              style="width: 100%; margin-bottom: 10px;"
            >
              生成测试用例
            </el-button>
            
            <el-button 
              @click="viewTestCases" 
              style="width: 100%; margin-bottom: 10px;"
            >
              查看测试用例
            </el-button>
          </div>
        </el-card>

        <!-- Statistics -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <span>统计信息</span>
          </template>
          
          <div class="statistics">
            <div class="stat-item">
              <span class="label">解析特征：</span>
              <span class="value">{{ features.length }}</span>
            </div>
            <div class="stat-item">
              <span class="label">测试用例：</span>
              <span class="value">{{ testCasesCount }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/api'

interface Requirement {
  id: number
  title: string
  description: string
  content: string
  status: string
  created_at: string
}

interface Feature {
  id: number
  feature_name: string
  feature_type: string
  priority: string
  description: string
}

const route = useRoute()
const router = useRouter()
const requirement = ref<Requirement | null>(null)
const features = ref<Feature[]>([])
const loading = ref(false)
const parsing = ref(false)
const generating = ref(false)
const testCasesCount = ref(0)

onMounted(() => {
  loadRequirement()
  loadFeatures()
  loadTestCasesCount()
})

const loadRequirement = async () => {
  loading.value = true
  try {
    const response = await api.get(`/api/v1/requirements/${route.params.id}`)
    requirement.value = response
  } catch (error) {
    ElMessage.error('加载需求详情失败')
    router.go(-1)
  } finally {
    loading.value = false
  }
}

const loadFeatures = async () => {
  try {
    const response = await api.get(`/api/v1/requirements/${route.params.id}/features`)
    features.value = response
  } catch (error) {
    console.error('加载特征失败', error)
  }
}

const loadTestCasesCount = async () => {
  try {
    const response = await api.get(`/api/v1/test-cases/?requirement_id=${route.params.id}`)
    testCasesCount.value = response.length
  } catch (error) {
    console.error('加载测试用例数量失败', error)
  }
}

const parseRequirement = async () => {
  parsing.value = true
  try {
    const response = await api.post(`/api/v1/requirements/${route.params.id}/parse`)
    ElMessage.success(response.message || '需求解析成功')
    loadRequirement()
    loadFeatures()
  } catch (error) {
    ElMessage.error('需求解析失败')
  } finally {
    parsing.value = false
  }
}

const generateTestCases = async () => {
  generating.value = true
  try {
    const response = await api.post('/api/v1/generation/test-cases', {
      requirement_id: Number(route.params.id),
      generation_type: 'test_cases'
    })
    ElMessage.success(response.message || '测试用例生成成功')
    loadTestCasesCount()
  } catch (error) {
    ElMessage.error('测试用例生成失败')
  } finally {
    generating.value = false
  }
}

const viewTestCases = () => {
  router.push(`/test-cases?requirement_id=${route.params.id}`)
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

const getPriorityType = (priority: string) => {
  const types: Record<string, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return types[priority] || 'info'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.requirement-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 15px;
}

.page-header h2 {
  margin: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.requirement-info p {
  margin-bottom: 15px;
}

.content-section {
  margin-top: 20px;
}

.content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap;
  margin-top: 10px;
}

.actions .el-button {
  display: block;
}

.statistics {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
}

.stat-item .label {
  color: #666;
}

.stat-item .value {
  font-weight: bold;
  color: #409eff;
}
</style>