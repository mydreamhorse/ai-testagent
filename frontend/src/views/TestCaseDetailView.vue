<template>
  <div class="test-case-detail" v-loading="loading">
    <div class="page-header">
      <el-button @click="$router.go(-1)">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>{{ testCase?.title || '加载中...' }}</h2>
    </div>

    <!-- 错误信息 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      style="margin-bottom: 20px;"
    />

    <el-row :gutter="20" v-if="testCase">
      <!-- 显示错误信息 -->
      <el-col :span="24" v-if="!testCase && !loading">
        <el-alert
          title="加载失败"
          description="无法加载测试用例详情，请检查网络连接或刷新页面重试。"
          type="error"
          show-icon
        />
      </el-col>
      <!-- Test Case Info -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>测试用例详情</span>
              <div class="tags">
                <el-tag :type="getTestTypeColor(testCase.test_type)" size="small">
                  {{ getTestTypeText(testCase.test_type) }}
                </el-tag>
                <el-tag :type="getPriorityType(testCase.priority)" size="small">
                  {{ testCase.priority }}
                </el-tag>
                <el-tag :type="testCase.generated_by === 'ai' ? 'success' : 'info'" size="small">
                  {{ testCase.generated_by === 'ai' ? 'AI生成' : '手动创建' }}
                </el-tag>
              </div>
            </div>
          </template>
          
          <div class="test-case-info">
            <div class="info-section" v-if="testCase.description">
              <h4>描述</h4>
              <p>{{ testCase.description }}</p>
            </div>

            <div class="info-section" v-if="testCase.preconditions">
              <h4>前置条件</h4>
              <div class="content">{{ testCase.preconditions }}</div>
            </div>

            <div class="info-section">
              <h4>测试步骤</h4>
              <div class="content">{{ testCase.test_steps }}</div>
            </div>

            <div class="info-section">
              <h4>预期结果</h4>
              <div class="content">{{ testCase.expected_result }}</div>
            </div>

            <div class="info-section">
              <h4>基本信息</h4>
              <p><strong>创建时间：</strong>{{ formatDate(testCase.created_at) }}</p>
              <p><strong>更新时间：</strong>{{ formatDate(testCase.updated_at) }}</p>
            </div>
          </div>
        </el-card>

        <!-- Evaluation Details -->
        <el-card style="margin-top: 20px;" v-if="evaluation">
          <template #header>
            <div class="card-header">
              <span>质量评估结果</span>
              <el-tag :type="getScoreType(evaluation.total_score)" size="large">
                总分：{{ evaluation.total_score.toFixed(1) }}/100
              </el-tag>
            </div>
          </template>
          
          <div class="evaluation-details">
            <div class="scores-grid">
              <div class="score-item">
                <span class="label">完整性</span>
                <el-progress 
                  :percentage="evaluation.completeness_score" 
                  :color="getScoreColor(evaluation.completeness_score)"
                  :show-text="false"
                />
                <span class="score">{{ evaluation.completeness_score.toFixed(1) }}</span>
              </div>
              <div class="score-item">
                <span class="label">准确性</span>
                <el-progress 
                  :percentage="evaluation.accuracy_score" 
                  :color="getScoreColor(evaluation.accuracy_score)"
                  :show-text="false"
                />
                <span class="score">{{ evaluation.accuracy_score.toFixed(1) }}</span>
              </div>
              <div class="score-item">
                <span class="label">可执行性</span>
                <el-progress 
                  :percentage="evaluation.executability_score" 
                  :color="getScoreColor(evaluation.executability_score)"
                  :show-text="false"
                />
                <span class="score">{{ evaluation.executability_score.toFixed(1) }}</span>
              </div>
              <div class="score-item">
                <span class="label">覆盖度</span>
                <el-progress 
                  :percentage="evaluation.coverage_score" 
                  :color="getScoreColor(evaluation.coverage_score)"
                  :show-text="false"
                />
                <span class="score">{{ evaluation.coverage_score.toFixed(1) }}</span>
              </div>
              <div class="score-item">
                <span class="label">清晰度</span>
                <el-progress 
                  :percentage="evaluation.clarity_score" 
                  :color="getScoreColor(evaluation.clarity_score)"
                  :show-text="false"
                />
                <span class="score">{{ evaluation.clarity_score.toFixed(1) }}</span>
              </div>
            </div>

            <div class="suggestions" v-if="evaluation.suggestions && evaluation.suggestions.length > 0">
              <h4>改进建议</h4>
              <ul>
                <li v-for="suggestion in evaluation.suggestions" :key="suggestion">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Actions -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>操作</span>
          </template>
          
          <div class="actions">
            <el-button 
              type="primary" 
              @click="evaluateTestCase" 
              :loading="evaluating"
              style="width: 100%; margin-bottom: 10px;"
            >
              重新评估
            </el-button>
            
            <el-button 
              @click="editTestCase" 
              style="width: 100%; margin-bottom: 10px;"
            >
              编辑
            </el-button>
            
            <el-button 
              @click="exportTestCase" 
              style="width: 100%; margin-bottom: 10px;"
            >
              导出
            </el-button>
            
            <el-button 
              type="danger" 
              @click="deleteTestCase" 
              style="width: 100%;"
            >
              删除
            </el-button>
          </div>
        </el-card>

        <!-- Quick Stats -->
        <el-card style="margin-top: 20px;" v-if="evaluation">
          <template #header>
            <span>快速统计</span>
          </template>
          
          <div class="quick-stats">
            <div class="stat-item">
              <span class="label">质量等级：</span>
              <el-tag :type="getScoreType(evaluation.total_score)">
                {{ getQualityLevel(evaluation.total_score) }}
              </el-tag>
            </div>
            <div class="stat-item">
              <span class="label">评估时间：</span>
              <span class="value">{{ formatDate(evaluation.evaluated_at) }}</span>
            </div>
            <div class="stat-item">
              <span class="label">评估方式：</span>
              <span class="value">{{ evaluation.evaluator_type === 'ai' ? 'AI评估' : '人工评估' }}</span>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '@/api'

interface TestCase {
  id: number
  title: string
  description: string
  test_type: string
  priority: string
  preconditions: string
  test_steps: string
  expected_result: string
  generated_by: string
  created_at: string
  updated_at: string
}

interface Evaluation {
  total_score: number
  completeness_score: number
  accuracy_score: number
  executability_score: number
  coverage_score: number
  clarity_score: number
  suggestions: string[]
  evaluated_at: string
  evaluator_type: string
}

const route = useRoute()
const router = useRouter()
const testCase = ref<TestCase | null>(null)
const evaluation = ref<Evaluation | null>(null)
const loading = ref(false)
const evaluating = ref(false)
const error = ref<string>('')

onMounted(() => {
  loadTestCase()
  loadEvaluation()
})

const loadTestCase = async () => {
  loading.value = true
  error.value = ''
  try {
    console.log('正在加载测试用例:', route.params.id)
    const response = await api.get(`/api/v1/test-cases/${route.params.id}`)
    console.log('API响应:', response)
    testCase.value = response
  } catch (err: any) {
    console.error('加载测试用例失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载测试用例失败'
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const loadEvaluation = async () => {
  try {
    const response = await api.get(`/api/v1/test-cases/${route.params.id}/evaluation`)
    evaluation.value = response
  } catch (error) {
    console.log('暂无评估数据')
  }
}

const evaluateTestCase = async () => {
  evaluating.value = true
  try {
    const response = await api.post(`/api/v1/test-cases/${route.params.id}/evaluate`)
    ElMessage.success('评估完成')
    evaluation.value = response.evaluation
  } catch (error) {
    ElMessage.error('评估失败')
  } finally {
    evaluating.value = false
  }
}

const editTestCase = () => {
  // TODO: Implement edit functionality
  ElMessage.info('编辑功能开发中')
}

const exportTestCase = () => {
  // TODO: Implement export functionality
  ElMessage.info('导出功能开发中')
}

const deleteTestCase = async () => {
  try {
    await ElMessageBox.confirm('确定删除此测试用例吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/api/v1/test-cases/${route.params.id}`)
    ElMessage.success('删除成功')
    router.go(-1)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
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
    function: '功能测试',
    boundary: '边界测试',
    exception: '异常测试',
    performance: '性能测试',
    security: '安全测试'
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

const getScoreType = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

const getScoreColor = (score: number) => {
  if (score >= 90) return '#67C23A'
  if (score >= 70) return '#E6A23C'
  return '#F56C6C'
}

const getQualityLevel = (score: number) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  if (score >= 60) return '及格'
  return '不及格'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.test-case-detail {
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

.tags {
  display: flex;
  gap: 8px;
}

.test-case-info .info-section {
  margin-bottom: 20px;
}

.test-case-info h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-weight: 600;
}

.test-case-info p {
  margin: 5px 0;
}

.content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
}

.evaluation-details .scores-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score-item .label {
  min-width: 70px;
  font-weight: 500;
}

.score-item .el-progress {
  flex: 1;
}

.score-item .score {
  min-width: 40px;
  text-align: right;
  font-weight: 600;
}

.suggestions h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.suggestions ul {
  margin: 0;
  padding-left: 20px;
}

.suggestions li {
  margin-bottom: 5px;
  line-height: 1.5;
}

.actions .el-button {
  display: block;
}

.quick-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
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
}
</style>