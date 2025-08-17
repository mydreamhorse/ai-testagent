<template>
  <div class="analytics-view">
    <div class="page-header">
      <h2>数据分析 (调试版)</h2>
      <el-button @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- Debug Info -->
    <el-alert title="调试信息" type="info" :closable="false" style="margin-bottom: 20px;">
      <p>加载状态: {{ loading ? '加载中' : '已完成' }}</p>
      <p>概览数据: {{ JSON.stringify(overviewData) }}</p>
      <p>错误信息: {{ debugError || '无' }}</p>
    </el-alert>

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

    <!-- 测试ECharts -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>测试图表 - 质量分数分布</span>
          </template>
          <div class="chart-container">
            <v-chart :option="scoreDistributionOption" :loading="loading" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>测试图表 - 测试类型分布</span>
          </template>
          <div class="chart-container">
            <v-chart :option="testTypeOption" :loading="loading" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 测试自定义组件 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>测试自定义组件</span>
          </template>
          <div style="padding: 20px;">
            <el-button @click="testCoverageHeatmap">测试 CoverageHeatmap</el-button>
            <el-button @click="testDefectAnalysisChart">测试 DefectAnalysisChart</el-button>
            <el-button @click="testTrendAnalysisChart">测试 TrendAnalysisChart</el-button>
            <el-button @click="testStatsDashboard">测试 StatsDashboard</el-button>
          </div>
          
          <!-- 条件渲染自定义组件 -->
          <div v-if="showCoverageHeatmap">
            <h4>CoverageHeatmap 组件:</h4>
            <CoverageHeatmap
              title="测试覆盖率热力图"
              :data="coverageData"
              :loading="loading"
              @cellClick="handleCoverageClick"
              @detailView="handleCoverageDetail"
            />
          </div>
          
          <div v-if="showDefectAnalysisChart">
            <h4>DefectAnalysisChart 组件:</h4>
            <DefectAnalysisChart
              title="缺陷分析图表"
              :data="defectData"
              :loading="loading"
              @defectClick="handleDefectClick"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
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

// 尝试导入自定义组件 - 使用同步导入
let CoverageHeatmap: any = null
let DefectAnalysisChart: any = null
let TrendAnalysisChart: any = null
let StatsDashboard: any = null

// 在组件挂载后动态导入
const loadComponents = async () => {
  try {
    const coverageModule = await import('@/components/charts/CoverageHeatmap.vue')
    CoverageHeatmap = coverageModule.default
    console.log('CoverageHeatmap loaded successfully')
  } catch (error) {
    console.error('Failed to import CoverageHeatmap:', error)
  }

  try {
    const defectModule = await import('@/components/charts/DefectAnalysisChart.vue')
    DefectAnalysisChart = defectModule.default
    console.log('DefectAnalysisChart loaded successfully')
  } catch (error) {
    console.error('Failed to import DefectAnalysisChart:', error)
  }

  try {
    const trendModule = await import('@/components/charts/TrendAnalysisChart.vue')
    TrendAnalysisChart = trendModule.default
    console.log('TrendAnalysisChart loaded successfully')
  } catch (error) {
    console.error('Failed to import TrendAnalysisChart:', error)
  }

  try {
    const statsModule = await import('@/components/charts/StatsDashboard.vue')
    StatsDashboard = statsModule.default
    console.log('StatsDashboard loaded successfully')
  } catch (error) {
    console.error('Failed to import StatsDashboard:', error)
  }
}

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

const loading = ref(false)
const debugError = ref('')
const showCoverageHeatmap = ref(false)
const showDefectAnalysisChart = ref(false)
const showTrendAnalysisChart = ref(false)
const showStatsDashboard = ref(false)

const overviewData = ref<OverviewData>({
  requirements_count: 0,
  test_cases_count: 0,
  features_count: 0,
  average_score: 0
})

const qualityScores = ref<number[]>([85, 78, 92, 76, 88, 81, 95, 73, 89, 84])
const testTypeData = ref([
  { name: '功能测试', value: 60 },
  { name: '边界测试', value: 40 },
  { name: '异常测试', value: 30 },
  { name: '性能测试', value: 20 }
])

// 模拟数据
const coverageData = ref([
  {
    name: '座椅调节',
    category: '核心功能',
    coverage: 85,
    covered_cases: 17,
    total_cases: 20,
    missing_areas: ['边界测试', '异常处理']
  }
])

const defectData = ref([
  {
    id: 1,
    type: 'functional',
    severity: 'high',
    status: 'open',
    detected_at: '2024-01-15T10:00:00Z',
    description: '座椅调节功能在极限位置时响应异常'
  }
])

onMounted(async () => {
  console.log('AnalyticsViewDebug mounted')
  await loadComponents()
  loadAnalyticsData()
})

const loadAnalyticsData = async () => {
  loading.value = true
  debugError.value = ''
  
  try {
    console.log('开始加载数据...')
    
    // 使用默认数据
    overviewData.value = {
      requirements_count: 25,
      test_cases_count: 150,
      features_count: 75,
      average_score: 85.2
    }
    
    console.log('数据加载完成:', overviewData.value)
    
  } catch (error: any) {
    console.error('数据加载失败:', error)
    debugError.value = error.message
    ElMessage.error('加载分析数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadAnalyticsData()
}

// 测试组件函数
const testCoverageHeatmap = () => {
  if (CoverageHeatmap) {
    showCoverageHeatmap.value = !showCoverageHeatmap.value
    ElMessage.success('CoverageHeatmap 组件可用')
  } else {
    ElMessage.error('CoverageHeatmap 组件导入失败')
  }
}

const testDefectAnalysisChart = () => {
  if (DefectAnalysisChart) {
    showDefectAnalysisChart.value = !showDefectAnalysisChart.value
    ElMessage.success('DefectAnalysisChart 组件可用')
  } else {
    ElMessage.error('DefectAnalysisChart 组件导入失败')
  }
}

const testTrendAnalysisChart = () => {
  if (TrendAnalysisChart) {
    showTrendAnalysisChart.value = !showTrendAnalysisChart.value
    ElMessage.success('TrendAnalysisChart 组件可用')
  } else {
    ElMessage.error('TrendAnalysisChart 组件导入失败')
  }
}

const testStatsDashboard = () => {
  if (StatsDashboard) {
    showStatsDashboard.value = !showStatsDashboard.value
    ElMessage.success('StatsDashboard 组件可用')
  } else {
    ElMessage.error('StatsDashboard 组件导入失败')
  }
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

// Event handlers
const handleCoverageClick = (data: any) => {
  ElMessage.info(`点击了覆盖率数据: ${data.name}`)
}

const handleCoverageDetail = (data: any) => {
  ElMessage.info(`查看覆盖率详情: ${data.name}`)
}

const handleDefectClick = (defect: any) => {
  ElMessage.info(`点击了缺陷: ${defect.description}`)
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
</style>