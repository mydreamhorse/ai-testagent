<template>
  <div class="generation-view">
    <div class="page-header">
      <h2>AI生成</h2>
    </div>

    <el-row :gutter="20">
      <!-- Generation Panel -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>智能生成</span>
          </template>
          
          <el-form :model="generationForm" label-width="120px">
            <el-form-item label="选择需求" required>
              <el-select 
                v-model="generationForm.requirement_id" 
                placeholder="请选择需求"
                @change="onRequirementChange"
                style="width: 100%"
              >
                <el-option 
                  v-for="req in requirements" 
                  :key="req.id" 
                  :label="req.title" 
                  :value="req.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="生成类型" required>
              <el-radio-group v-model="generationForm.generation_type">
                <el-radio label="test_cases">测试用例生成</el-radio>
                <el-radio label="evaluation">质量评估</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="生成选项" v-if="generationForm.generation_type === 'test_cases'">
              <el-checkbox-group v-model="generationOptions.test_types">
                <el-checkbox label="function">功能测试</el-checkbox>
                <el-checkbox label="boundary">边界测试</el-checkbox>
                <el-checkbox label="exception">异常测试</el-checkbox>
                <el-checkbox label="performance">性能测试</el-checkbox>
                <el-checkbox label="security">安全测试</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <el-button 
                type="primary" 
                @click="startGeneration" 
                :loading="generating"
                :disabled="!generationForm.requirement_id || !generationForm.generation_type"
              >
                开始生成
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Generation History -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>生成历史</span>
              <el-button size="small" @click="loadHistory">刷新</el-button>
            </div>
          </template>
          
          <el-table :data="history" v-loading="historyLoading">
            <el-table-column prop="requirement_title" label="需求" min-width="200" />
            <el-table-column prop="generation_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.generation_type === 'test_cases' ? 'primary' : 'success'" size="small">
                  {{ row.generation_type === 'test_cases' ? '测试用例' : '质量评估' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="processing_time" label="耗时" width="100">
              <template #default="{ row }">
                {{ row.processing_time ? `${row.processing_time.toFixed(1)}s` : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" @click="viewResult(row)" v-if="row.status === 'completed'">
                  查看结果
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- Info Panel -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>选中需求信息</span>
          </template>
          
          <div v-if="selectedRequirement">
            <div class="requirement-info">
              <h4>{{ selectedRequirement.title }}</h4>
              <p class="description">{{ selectedRequirement.description }}</p>
              <div class="stats">
                <div class="stat-item">
                  <span class="label">状态：</span>
                  <el-tag :type="getStatusType(selectedRequirement.status)" size="small">
                    {{ getStatusText(selectedRequirement.status) }}
                  </el-tag>
                </div>
                <div class="stat-item">
                  <span class="label">解析特征：</span>
                  <span class="value">{{ requirementStats.features_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">测试用例：</span>
                  <span class="value">{{ requirementStats.test_cases_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">创建时间：</span>
                  <span class="value">{{ formatDate(selectedRequirement.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="请选择需求" />
        </el-card>

        <!-- Tips -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <span>使用提示</span>
          </template>
          
          <div class="tips">
            <div class="tip-item">
              <el-icon><InfoFilled /></el-icon>
              <span>请先确保需求已完成解析，才能生成测试用例</span>
            </div>
            <div class="tip-item">
              <el-icon><InfoFilled /></el-icon>
              <span>质量评估需要先有测试用例才能进行</span>
            </div>
            <div class="tip-item">
              <el-icon><InfoFilled /></el-icon>
              <span>AI生成过程可能需要几秒到几分钟时间</span>
            </div>
            <div class="tip-item">
              <el-icon><InfoFilled /></el-icon>
              <span>可以在生成历史中查看详细结果</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Result Dialog -->
    <el-dialog v-model="showResultDialog" title="生成结果" width="800px">
      <div v-if="generationResult">
        <h4>{{ generationResult.generation_type === 'test_cases' ? '测试用例生成结果' : '质量评估结果' }}</h4>
        
        <div v-if="generationResult.generation_type === 'test_cases'">
          <p>成功生成 <strong>{{ generationResult.output_data?.test_cases_count || 0 }}</strong> 个测试用例</p>
          <div v-if="generationResult.output_data?.test_cases">
            <h5>生成的测试用例：</h5>
            <ul>
              <li v-for="tc in generationResult.output_data.test_cases" :key="tc.title">
                {{ tc.title }} ({{ tc.test_type }}, {{ tc.priority }})
              </li>
            </ul>
          </div>
        </div>
        
        <div v-else-if="generationResult.generation_type === 'quality_evaluation'">
          <p>成功评估 <strong>{{ generationResult.output_data?.evaluated_count || 0 }}</strong> 个测试用例</p>
          <p>平均分数：<strong>{{ generationResult.output_data?.average_score?.toFixed(1) || 0 }}/100</strong></p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showResultDialog = false">关闭</el-button>
        <el-button type="primary" @click="viewDetailedResult" v-if="generationResult">
          查看详细结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import api from '@/api'

interface Requirement {
  id: number
  title: string
  description: string
  status: string
  created_at: string
}

interface GenerationHistory {
  id: number
  requirement_id: number
  requirement_title: string
  generation_type: string
  status: string
  processing_time: number
  created_at: string
  output_data?: any
}

const router = useRouter()
const requirements = ref<Requirement[]>([])
const selectedRequirement = ref<Requirement | null>(null)
const history = ref<GenerationHistory[]>([])
const generating = ref(false)
const historyLoading = ref(false)
const showResultDialog = ref(false)
const generationResult = ref<GenerationHistory | null>(null)

const generationForm = ref({
  requirement_id: undefined as number | undefined,
  generation_type: 'test_cases'
})

const generationOptions = ref({
  test_types: ['function', 'exception']
})

const requirementStats = ref({
  features_count: 0,
  test_cases_count: 0
})

onMounted(() => {
  loadRequirements()
  loadHistory()
})

watch(() => generationForm.value.requirement_id, (newId) => {
  if (newId) {
    onRequirementChange(newId)
  }
})

const loadRequirements = async () => {
  try {
    const response = await api.get('/api/v1/requirements/')
    requirements.value = response
  } catch (error) {
    ElMessage.error('加载需求列表失败')
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await api.get('/api/v1/generation/history')
    // Add requirement titles to history
    history.value = response.map((item: any) => ({
      ...item,
      requirement_title: requirements.value.find(r => r.id === item.requirement_id)?.title || '未知需求'
    }))
  } catch (error) {
    ElMessage.error('加载生成历史失败')
  } finally {
    historyLoading.value = false
  }
}

const onRequirementChange = async (requirementId: number) => {
  selectedRequirement.value = requirements.value.find(r => r.id === requirementId) || null
  
  if (selectedRequirement.value) {
    // Load requirement stats
    try {
      const [featuresRes, testCasesRes] = await Promise.all([
        api.get(`/api/v1/requirements/${requirementId}/features`),
        api.get(`/api/v1/test-cases/?requirement_id=${requirementId}`)
      ])
      
      requirementStats.value = {
        features_count: featuresRes.length,
        test_cases_count: testCasesRes.length
      }
    } catch (error) {
      console.error('加载需求统计失败', error)
    }
  }
}

const startGeneration = async () => {
  if (!generationForm.value.requirement_id || !generationForm.value.generation_type) {
    ElMessage.warning('请选择需求和生成类型')
    return
  }

  // Check prerequisites
  if (generationForm.value.generation_type === 'test_cases' && selectedRequirement.value?.status !== 'completed') {
    ElMessage.warning('请先解析需求后再生成测试用例')
    return
  }

  if (generationForm.value.generation_type === 'evaluation' && requirementStats.value.test_cases_count === 0) {
    ElMessage.warning('请先生成测试用例后再进行质量评估')
    return
  }

  generating.value = true
  try {
    const endpoint = generationForm.value.generation_type === 'test_cases' 
      ? '/api/v1/generation/test-cases' 
      : '/api/v1/generation/evaluation'
    
    const requestData = {
      requirement_id: generationForm.value.requirement_id,
      generation_type: generationForm.value.generation_type,
      options: generationForm.value.generation_type === 'test_cases' 
        ? { test_types: generationOptions.value.test_types }
        : undefined
    }

    const response = await api.post(endpoint, requestData)
    ElMessage.success(response.message || '生成成功')
    
    // Refresh data
    loadHistory()
    onRequirementChange(generationForm.value.requirement_id)
    
    // If test cases were generated, offer to navigate to test cases view
    if (generationForm.value.generation_type === 'test_cases') {
      ElMessageBox.confirm(
        '测试用例生成成功！是否立即查看生成的测试用例？',
        '生成完成',
        {
          confirmButtonText: '查看测试用例',
          cancelButtonText: '稍后查看',
          type: 'success'
        }
      ).then(() => {
        // Navigate to test cases view with the current requirement filter
        router.push({
          name: 'TestCases',
          query: { requirement_id: generationForm.value.requirement_id }
        })
      }).catch(() => {
        // User chose to stay on current page
      })
    }
    
  } catch (error) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

const resetForm = () => {
  generationForm.value = {
    requirement_id: undefined,
    generation_type: 'test_cases'
  }
  generationOptions.value = {
    test_types: ['function', 'exception']
  }
  selectedRequirement.value = null
  requirementStats.value = {
    features_count: 0,
    test_cases_count: 0
  }
}

const viewResult = (result: GenerationHistory) => {
  generationResult.value = result
  showResultDialog.value = true
}

const viewDetailedResult = () => {
  if (generationResult.value?.generation_type === 'test_cases') {
    router.push(`/test-cases?requirement_id=${generationResult.value.requirement_id}`)
  } else {
    router.push(`/requirements/${generationResult.value?.requirement_id}`)
  }
  showResultDialog.value = false
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
.generation-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.requirement-info h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.requirement-info .description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.5;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item .label {
  color: #666;
}

.stat-item .value {
  font-weight: bold;
  color: #409eff;
}

.tips {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.tip-item .el-icon {
  color: #409eff;
  margin-top: 2px;
}
</style>