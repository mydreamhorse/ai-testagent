<template>
  <div class="test-cases-view">
    <div class="page-header">
      <h2>测试用例</h2>
      <div class="header-actions">
        <el-select v-model="selectedRequirement" placeholder="选择需求" @change="loadTestCases" clearable>
          <el-option 
            v-for="req in requirements" 
            :key="req.id" 
            :label="req.title" 
            :value="req.id"
          />
        </el-select>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建测试用例
        </el-button>
      </div>
    </div>

    <!-- Test Cases List -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试用例列表 ({{ testCases.length }})</span>
          <div class="filters">
            <el-select v-model="selectedType" placeholder="测试类型" @change="loadTestCases" clearable>
              <el-option label="功能测试" value="function" />
              <el-option label="边界测试" value="boundary" />
              <el-option label="异常测试" value="exception" />
              <el-option label="性能测试" value="performance" />
              <el-option label="安全测试" value="security" />
            </el-select>
            <el-button @click="loadTestCases" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="batchEvaluate" :disabled="selectedTestCases.length === 0" :loading="evaluating">
              批量评估
            </el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="testCases" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="test_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTestTypeColor(row.test_type)" size="small">
              {{ getTestTypeText(row.test_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generated_by" label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.generated_by === 'ai' ? 'success' : 'info'" size="small">
              {{ row.generated_by === 'ai' ? 'AI生成' : '手动创建' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="100">
          <template #default="{ row }">
            <span v-if="row.evaluation">{{ row.evaluation.total_score.toFixed(1) }}</span>
            <span v-else class="text-gray">未评估</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewTestCase(row.id)">查看</el-button>
            <el-button size="small" type="primary" @click="evaluateTestCase(row.id)">评估</el-button>
            <el-button size="small" type="danger" @click="deleteTestCase(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建测试用例" width="800px">
      <el-form :model="newTestCase" label-width="120px">
        <el-form-item label="需求" required>
          <el-select v-model="newTestCase.requirement_id" placeholder="选择需求">
            <el-option 
              v-for="req in requirements" 
              :key="req.id" 
              :label="req.title" 
              :value="req.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="newTestCase.title" placeholder="请输入测试用例标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newTestCase.description" type="textarea" :rows="2" placeholder="请输入测试用例描述" />
        </el-form-item>
        <el-form-item label="测试类型" required>
          <el-select v-model="newTestCase.test_type" placeholder="选择测试类型">
            <el-option label="功能测试" value="function" />
            <el-option label="边界测试" value="boundary" />
            <el-option label="异常测试" value="exception" />
            <el-option label="性能测试" value="performance" />
            <el-option label="安全测试" value="security" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" required>
          <el-select v-model="newTestCase.priority" placeholder="选择优先级">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="前置条件">
          <el-input v-model="newTestCase.preconditions" type="textarea" :rows="3" placeholder="请输入前置条件" />
        </el-form-item>
        <el-form-item label="测试步骤" required>
          <el-input v-model="newTestCase.test_steps" type="textarea" :rows="5" placeholder="请输入测试步骤" />
        </el-form-item>
        <el-form-item label="预期结果" required>
          <el-input v-model="newTestCase.expected_result" type="textarea" :rows="3" placeholder="请输入预期结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTestCase" :loading="creating">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import api from '@/api'

interface TestCase {
  id: number
  title: string
  description: string
  test_type: string
  priority: string
  generated_by: string
  created_at: string
  evaluation?: {
    total_score: number
  }
}

interface Requirement {
  id: number
  title: string
}

const route = useRoute()
const router = useRouter()
const testCases = ref<TestCase[]>([])
const requirements = ref<Requirement[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const evaluating = ref(false)
const selectedRequirement = ref<number | undefined>()
const selectedType = ref<string>('')
const selectedTestCases = ref<TestCase[]>([])

const newTestCase = ref({
  requirement_id: undefined as number | undefined,
  title: '',
  description: '',
  test_type: '',
  priority: 'medium',
  preconditions: '',
  test_steps: '',
  expected_result: ''
})

onMounted(() => {
  loadRequirements()
  
  // If there's a requirement_id in query, set it as selected
  if (route.query.requirement_id) {
    selectedRequirement.value = Number(route.query.requirement_id)
  }
  
  loadTestCases()
})

// Watch for route changes to refresh data
watch(
  () => route.query.requirement_id,
  (newRequirementId) => {
    if (newRequirementId) {
      selectedRequirement.value = Number(newRequirementId)
      loadTestCases()
    }
  }
)

// Watch for route changes to refresh data when navigating back to this page
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/test-cases') {
      loadTestCases()
    }
  }
)

const loadRequirements = async () => {
  try {
    const response = await api.get('/api/v1/requirements/')
    requirements.value = response
  } catch (error) {
    ElMessage.error('加载需求列表失败')
  }
}

const loadTestCases = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (selectedRequirement.value) {
      params.append('requirement_id', selectedRequirement.value.toString())
    }
    if (selectedType.value) {
      params.append('test_type', selectedType.value)
    }
    
    // Add sorting parameters - default sort by creation time descending
    params.append('sort_by', 'created_at')
    params.append('sort_order', 'desc')
    
    // Increase limit to get more test cases (including today's generated ones)
    params.append('limit', '500')

    const response = await api.get(`/api/v1/test-cases/?${params}`)
    // 在前端对数据进行排序，确保最新的排在最前面
    testCases.value = response.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } catch (error) {
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const createTestCase = async () => {
  if (!newTestCase.value.requirement_id || !newTestCase.value.title || 
      !newTestCase.value.test_type || !newTestCase.value.test_steps || 
      !newTestCase.value.expected_result) {
    ElMessage.warning('请填写必填字段')
    return
  }

  creating.value = true
  try {
    await api.post('/api/v1/test-cases/', newTestCase.value)
    ElMessage.success('测试用例创建成功')
    showCreateDialog.value = false
    resetNewTestCase()
    loadTestCases()
  } catch (error) {
    ElMessage.error('测试用例创建失败')
  } finally {
    creating.value = false
  }
}

const resetNewTestCase = () => {
  newTestCase.value = {
    requirement_id: undefined,
    title: '',
    description: '',
    test_type: '',
    priority: 'medium',
    preconditions: '',
    test_steps: '',
    expected_result: ''
  }
}

const viewTestCase = (id: number) => {
  router.push(`/test-cases/${id}`)
}

const evaluateTestCase = async (id: number) => {
  try {
    const response = await api.post(`/api/v1/test-cases/${id}/evaluate`)
    ElMessage.success('评估完成')
    loadTestCases()
  } catch (error) {
    ElMessage.error('评估失败')
  }
}

const deleteTestCase = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除此测试用例吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/api/v1/test-cases/${id}`)
    ElMessage.success('删除成功')
    loadTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSelectionChange = (selection: TestCase[]) => {
  selectedTestCases.value = selection
}

const batchEvaluate = async () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请选择要评估的测试用例')
    return
  }

  evaluating.value = true
  try {
    const testCaseIds = selectedTestCases.value.map(tc => tc.id)
    const response = await api.post('/api/v1/test-cases/batch-evaluate', testCaseIds)
    ElMessage.success(`批量评估完成，已评估 ${response.data.evaluated_count} 个测试用例`)
    loadTestCases()
  } catch (error) {
    ElMessage.error('批量评估失败')
  } finally {
    evaluating.value = false
  }
}

const getTestTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    function: 'primary',
    boundary: 'warning',
    exception: 'danger',
    performance: 'info',
    security: 'success'
  }
  return colors[type] || 'info'
}

const getTestTypeText = (type: string) => {
  const texts: Record<string, string> = {
    function: '功能',
    boundary: '边界',
    exception: '异常',
    performance: '性能',
    security: '安全'
  }
  return texts[type] || type
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
.test-cases-view {
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

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.text-gray {
  color: #999;
}
</style>