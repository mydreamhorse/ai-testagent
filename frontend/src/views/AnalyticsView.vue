<template>
  <div class="analytics-view">
    <div class="page-header">
      <h2>数据分析</h2>
      <el-button @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- Overview Cards -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="icon requirements">
              <el-icon><Document /></el-icon>
            </div>
            <div class="info">
              <h3>{{ overviewData.requirements_count }}</h3>
              <p>需求总数</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="icon test-cases">
              <el-icon><List /></el-icon>
            </div>
            <div class="info">
              <h3>{{ overviewData.test_cases_count }}</h3>
              <p>测试用例总数</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="icon features">
              <el-icon><Star /></el-icon>
            </div>
            <div class="info">
              <h3>{{ overviewData.features_count }}</h3>
              <p>解析特征总数</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="icon score">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="info">
              <h3>{{ overviewData.average_score.toFixed(1) }}</h3>
              <p>平均质量得分</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- Quality Score Distribution -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>质量分数分布</span>
          </template>
          <div class="chart-container">
            <v-chart :option="scoreDistributionOption" :loading="loading" />
          </div>
        </el-card>
      </el-col>

      <!-- Test Type Distribution -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>测试类型分布</span>
          </template>
          <div class="chart-container">
            <v-chart :option="testTypeOption" :loading="loading" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- Quality Dimensions Radar -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>质量维度雷达图</span>
          </template>
          <div class="chart-container">
            <v-chart :option="qualityRadarOption" :loading="loading" />
          </div>
        </el-card>
      </el-col>

      <!-- Generation Trend -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>生成趋势</span>
          </template>
          <div class="chart-container">
            <v-chart :option="generationTrendOption" :loading="loading" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Detailed Statistics -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>详细统计</span>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="stat-section">
            <h4>需求状态统计</h4>
            <el-table :data="requirementStats" size="small">
              <el-table-column prop="status" label="状态">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" />
              <el-table-column prop="percentage" label="占比">
                <template #default="{ row }">
                  {{ row.percentage.toFixed(1) }}%
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
        
        <el-col :span="12">
          <div class="stat-section">
            <h4>测试优先级统计</h4>
            <el-table :data="priorityStats" size="small">
              <el-table-column prop="priority" label="优先级">
                <template #default="{ row }">
                  <el-tag :type="getPriorityType(row.priority)" size="small">
                    {{ row.priority }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" />
              <el-table-column prop="percentage" label="占比">
                <template #default="{ row }">
                  {{ row.percentage.toFixed(1) }}%
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Document, List, Star, TrendCharts } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  BarChart,
  PieChart,
  LineChart,
  RadarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
} from 'echarts/components'
import api from '@/api'

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  LineChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
])

interface OverviewData {
  requirements_count: number
  test_cases_count: number
  features_count: number
  average_score: number
}

interface StatItem {
  status?: string
  priority?: string
  count: number
  percentage: number
}

const loading = ref(false)
const overviewData = ref<OverviewData>({
  requirements_count: 0,
  test_cases_count: 0,
  features_count: 0,
  average_score: 0
})

const requirementStats = ref<StatItem[]>([])
const priorityStats = ref<StatItem[]>([])
const qualityScores = ref<number[]>([])
const testTypeData = ref<{name: string, value: number}[]>([])
const qualityDimensions = ref({
  completeness: 0,
  accuracy: 0,
  executability: 0,
  coverage: 0,
  clarity: 0
})
const generationTrend = ref<{date: string, count: number}[]>([])

onMounted(() => {
  loadAnalyticsData()
})

const loadAnalyticsData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadOverviewData(),
      loadRequirementStats(),
      loadTestCaseStats(),
      loadQualityData(),
      loadGenerationTrend()
    ])
  } catch (error) {
    ElMessage.error('加载分析数据失败')
  } finally {
    loading.value = false
  }
}

const loadOverviewData = async () => {
  try {
    const [reqRes, tcRes, featRes] = await Promise.all([
      api.get('/api/v1/requirements/'),
      api.get('/api/v1/test-cases/'),
      api.get('/api/v1/requirements/')
    ])

    overviewData.value.requirements_count = reqRes.length
    overviewData.value.test_cases_count = tcRes.length
    
    // Count features from all requirements
    let featuresCount = 0
    for (const req of reqRes) {
      try {
        const featRes = await api.get(`/api/v1/requirements/${req.id}/features`)
        featuresCount += featRes.length
      } catch (error) {
        console.log(`Failed to load features for requirement ${req.id}`)
      }
    }
    overviewData.value.features_count = featuresCount

    // Calculate average score from test cases with evaluations
    const testCasesWithScores = tcRes.filter((tc: any) => tc.evaluation)
    if (testCasesWithScores.length > 0) {
      const totalScore = testCasesWithScores.reduce((sum: number, tc: any) => sum + tc.evaluation.total_score, 0)
      overviewData.value.average_score = totalScore / testCasesWithScores.length
    }
  } catch (error) {
    console.error('Failed to load overview data', error)
  }
}

const loadRequirementStats = async () => {
  try {
    const response = await api.get('/api/v1/requirements/')
    const requirements = response
    
    const statusCounts: Record<string, number> = {}
    requirements.forEach((req: any) => {
      statusCounts[req.status] = (statusCounts[req.status] || 0) + 1
    })

    requirementStats.value = Object.entries(statusCounts).map(([status, count]) => ({
      status,
      count,
      percentage: (count / requirements.length) * 100
    }))
  } catch (error) {
    console.error('Failed to load requirement stats', error)
  }
}

const loadTestCaseStats = async () => {
  try {
    const response = await api.get('/api/v1/test-cases/')
    const testCases = response
    
    // Priority stats
    const priorityCounts: Record<string, number> = {}
    testCases.forEach((tc: any) => {
      priorityCounts[tc.priority] = (priorityCounts[tc.priority] || 0) + 1
    })

    priorityStats.value = Object.entries(priorityCounts).map(([priority, count]) => ({
      priority,
      count,
      percentage: (count / testCases.length) * 100
    }))

    // Test type stats
    const typeCounts: Record<string, number> = {}
    testCases.forEach((tc: any) => {
      typeCounts[tc.test_type] = (typeCounts[tc.test_type] || 0) + 1
    })

    testTypeData.value = Object.entries(typeCounts).map(([name, value]) => ({
      name: getTestTypeText(name),
      value
    }))
  } catch (error) {
    console.error('Failed to load test case stats', error)
  }
}

const loadQualityData = async () => {
  try {
    const response = await api.get('/api/v1/test-cases/')
    const testCases = response.filter((tc: any) => tc.evaluation)
    
    if (testCases.length > 0) {
      qualityScores.value = testCases.map((tc: any) => tc.evaluation.total_score)
      
      // Average quality dimensions
      const dimensions = {
        completeness: 0,
        accuracy: 0,
        executability: 0,
        coverage: 0,
        clarity: 0
      }

      testCases.forEach((tc: any) => {
        dimensions.completeness += tc.evaluation.completeness_score
        dimensions.accuracy += tc.evaluation.accuracy_score
        dimensions.executability += tc.evaluation.executability_score
        dimensions.coverage += tc.evaluation.coverage_score
        dimensions.clarity += tc.evaluation.clarity_score
      })

      Object.keys(dimensions).forEach(key => {
        qualityDimensions.value[key as keyof typeof dimensions] = 
          dimensions[key as keyof typeof dimensions] / testCases.length
      })
    }
  } catch (error) {
    console.error('Failed to load quality data', error)
  }
}

const loadGenerationTrend = async () => {
  try {
    const response = await api.get('/api/v1/generation/history')
    const history = response
    
    // Group by date
    const dateGroups: Record<string, number> = {}
    history.forEach((item: any) => {
      const date = new Date(item.created_at).toLocaleDateString('zh-CN')
      dateGroups[date] = (dateGroups[date] || 0) + 1
    })

    generationTrend.value = Object.entries(dateGroups)
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .slice(-7) // Last 7 days
  } catch (error) {
    console.error('Failed to load generation trend', error)
  }
}

const refreshData = () => {
  loadAnalyticsData()
}

// Chart options
const scoreDistributionOption = computed(() => ({
  title: {
    text: '质量分数分布',
    left: 'center'
  },
  tooltip: {
    trigger: 'item'
  },
  xAxis: {
    type: 'category',
    data: ['0-60', '60-70', '70-80', '80-90', '90-100']
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    data: [
      qualityScores.value.filter(s => s < 60).length,
      qualityScores.value.filter(s => s >= 60 && s < 70).length,
      qualityScores.value.filter(s => s >= 70 && s < 80).length,
      qualityScores.value.filter(s => s >= 80 && s < 90).length,
      qualityScores.value.filter(s => s >= 90).length
    ],
    type: 'bar',
    itemStyle: {
      color: '#409EFF'
    }
  }]
}))

const testTypeOption = computed(() => ({
  title: {
    text: '测试类型分布',
    left: 'center'
  },
  tooltip: {
    trigger: 'item'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [{
    name: '测试类型',
    type: 'pie',
    radius: '50%',
    data: testTypeData.value,
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }]
}))

const qualityRadarOption = computed(() => ({
  title: {
    text: '质量维度雷达图',
    left: 'center'
  },
  legend: {
    data: ['平均质量']
  },
  radar: {
    indicator: [
      { name: '完整性', max: 100 },
      { name: '准确性', max: 100 },
      { name: '可执行性', max: 100 },
      { name: '覆盖度', max: 100 },
      { name: '清晰度', max: 100 }
    ]
  },
  series: [{
    name: '质量维度',
    type: 'radar',
    data: [{
      value: [
        qualityDimensions.value.completeness,
        qualityDimensions.value.accuracy,
        qualityDimensions.value.executability,
        qualityDimensions.value.coverage,
        qualityDimensions.value.clarity
      ],
      name: '平均质量'
    }]
  }]
}))

const generationTrendOption = computed(() => ({
  title: {
    text: '生成趋势',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: generationTrend.value.map(item => item.date)
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    data: generationTrend.value.map(item => item.count),
    type: 'line',
    smooth: true,
    itemStyle: {
      color: '#67C23A'
    }
  }]
}))

// Helper functions
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
</script>

<style scoped>
.analytics-view {
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

.overview-cards {
  margin-bottom: 20px;
}

.overview-card .card-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.overview-card .icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.overview-card .icon.requirements {
  background: #409EFF;
}

.overview-card .icon.test-cases {
  background: #67C23A;
}

.overview-card .icon.features {
  background: #E6A23C;
}

.overview-card .icon.score {
  background: #F56C6C;
}

.overview-card .info h3 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.overview-card .info p {
  margin: 5px 0 0 0;
  color: #666;
  font-size: 14px;
}

.chart-container {
  height: 400px;
}

.stat-section h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-weight: 600;
}
</style>