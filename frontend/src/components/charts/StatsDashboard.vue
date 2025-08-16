<template>
  <div class="stats-dashboard">
    <!-- 概览卡片 -->
    <div class="overview-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="icon reports">
                <el-icon><Document /></el-icon>
              </div>
              <div class="info">
                <h3>{{ overviewStats.total_reports }}</h3>
                <p>生成报告数</p>
                <div class="trend" :class="overviewStats.reports_trend > 0 ? 'up' : 'down'">
                  <el-icon v-if="overviewStats.reports_trend > 0"><ArrowUp /></el-icon>
                  <el-icon v-else><ArrowDown /></el-icon>
                  <span>{{ Math.abs(overviewStats.reports_trend) }}%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="icon defects">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="info">
                <h3>{{ overviewStats.total_defects }}</h3>
                <p>发现缺陷数</p>
                <div class="trend" :class="overviewStats.defects_trend > 0 ? 'down' : 'up'">
                  <el-icon v-if="overviewStats.defects_trend > 0"><ArrowUp /></el-icon>
                  <el-icon v-else><ArrowDown /></el-icon>
                  <span>{{ Math.abs(overviewStats.defects_trend) }}%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="icon coverage">
                <el-icon><PieChart /></el-icon>
              </div>
              <div class="info">
                <h3>{{ overviewStats.avg_coverage }}%</h3>
                <p>平均覆盖率</p>
                <div class="trend" :class="overviewStats.coverage_trend > 0 ? 'up' : 'down'">
                  <el-icon v-if="overviewStats.coverage_trend > 0"><ArrowUp /></el-icon>
                  <el-icon v-else><ArrowDown /></el-icon>
                  <span>{{ Math.abs(overviewStats.coverage_trend) }}%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="icon quality">
                <el-icon><Star /></el-icon>
              </div>
              <div class="info">
                <h3>{{ overviewStats.quality_score }}</h3>
                <p>质量评分</p>
                <div class="trend" :class="overviewStats.quality_trend > 0 ? 'up' : 'down'">
                  <el-icon v-if="overviewStats.quality_trend > 0"><ArrowUp /></el-icon>
                  <el-icon v-else><ArrowDown /></el-icon>
                  <span>{{ Math.abs(overviewStats.quality_trend) }}%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 快速操作 -->
    <div class="quick-actions">
      <el-card>
        <template #header>
          <span>快速操作</span>
        </template>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-button type="primary" @click="generateReport" :loading="generating">
              <el-icon><DocumentAdd /></el-icon>
              生成新报告
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button type="success" @click="analyzeCoverage">
              <el-icon><DataAnalysis /></el-icon>
              分析覆盖率
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button type="warning" @click="checkDefects">
              <el-icon><Search /></el-icon>
              检查缺陷
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button type="info" @click="exportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 图表展示区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 测试执行统计 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>测试执行统计</span>
            </template>
            <div class="chart-container">
              <v-chart :option="executionStatsOption" :loading="loading" />
            </div>
          </el-card>
        </el-col>

        <!-- 质量指标雷达图 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>质量指标雷达图</span>
            </template>
            <div class="chart-container">
              <v-chart :option="qualityRadarOption" :loading="loading" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 缺陷严重程度分布 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>缺陷严重程度</span>
            </template>
            <div class="chart-container small">
              <v-chart :option="defectSeverityOption" :loading="loading" />
            </div>
          </el-card>
        </el-col>

        <!-- 覆盖率分布 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>覆盖率分布</span>
            </template>
            <div class="chart-container small">
              <v-chart :option="coverageDistributionOption" :loading="loading" />
            </div>
          </el-card>
        </el-col>

        <!-- 月度趋势 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>月度趋势</span>
            </template>
            <div class="chart-container small">
              <v-chart :option="monthlyTrendOption" :loading="loading" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activities">
      <el-card>
        <template #header>
          <div class="activities-header">
            <span>最近活动</span>
            <el-button size="small" text @click="refreshActivities">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="activity in recentActivities"
            :key="activity.id"
            :timestamp="activity.timestamp"
            :type="getActivityType(activity.type)"
          >
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-description">{{ activity.description }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  WarningFilled,
  PieChart,
  Star,
  ArrowUp,
  ArrowDown,
  DocumentAdd,
  DataAnalysis,
  Search,
  Download,
  Refresh
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  BarChart,
  LineChart,
  PieChart as EChartsPieChart,
  RadarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  EChartsPieChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  RadarComponent
])

interface OverviewStats {
  total_reports: number
  reports_trend: number
  total_defects: number
  defects_trend: number
  avg_coverage: number
  coverage_trend: number
  quality_score: number
  quality_trend: number
}

interface Activity {
  id: number
  type: 'report' | 'defect' | 'coverage' | 'alert'
  title: string
  description: string
  timestamp: string
}

const props = defineProps<{
  data?: any
}>()

const emit = defineEmits<{
  generateReport: []
  analyzeCoverage: []
  checkDefects: []
  exportData: []
}>()

const loading = ref(false)
const generating = ref(false)

// 概览统计数据
const overviewStats = ref<OverviewStats>({
  total_reports: 156,
  reports_trend: 12.5,
  total_defects: 23,
  defects_trend: -8.3,
  avg_coverage: 87.2,
  coverage_trend: 5.1,
  quality_score: 8.6,
  quality_trend: 3.2
})

// 最近活动数据
const recentActivities = ref<Activity[]>([
  {
    id: 1,
    type: 'report',
    title: '生成了测试执行报告',
    description: '包含125个测试用例的执行结果',
    timestamp: '2024-01-15 14:30'
  },
  {
    id: 2,
    type: 'defect',
    title: '发现高优先级缺陷',
    description: '在座椅调节功能中发现严重缺陷',
    timestamp: '2024-01-15 11:20'
  },
  {
    id: 3,
    type: 'coverage',
    title: '覆盖率分析完成',
    description: '整体覆盖率提升至87.2%',
    timestamp: '2024-01-15 09:15'
  },
  {
    id: 4,
    type: 'alert',
    title: '系统告警',
    description: '测试执行时间超出预期阈值',
    timestamp: '2024-01-14 16:45'
  }
])

// 测试执行统计图表配置
const executionStatsOption = computed(() => ({
  title: {
    text: '测试执行统计',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['通过', '失败', '跳过'],
    top: 30
  },
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '通过',
      type: 'bar',
      stack: 'total',
      data: [45, 52, 48, 61, 55, 42, 38],
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '失败',
      type: 'bar',
      stack: 'total',
      data: [5, 8, 6, 4, 7, 9, 6],
      itemStyle: { color: '#F56C6C' }
    },
    {
      name: '跳过',
      type: 'bar',
      stack: 'total',
      data: [2, 1, 3, 2, 1, 2, 4],
      itemStyle: { color: '#E6A23C' }
    }
  ]
}))

// 质量指标雷达图配置
const qualityRadarOption = computed(() => ({
  title: {
    text: '质量指标雷达图',
    left: 'center'
  },
  radar: {
    indicator: [
      { name: '功能完整性', max: 100 },
      { name: '性能表现', max: 100 },
      { name: '安全性', max: 100 },
      { name: '可靠性', max: 100 },
      { name: '易用性', max: 100 },
      { name: '兼容性', max: 100 }
    ]
  },
  series: [{
    name: '质量指标',
    type: 'radar',
    data: [
      {
        value: [85, 78, 92, 88, 82, 75],
        name: '当前指标',
        itemStyle: { color: '#409EFF' }
      },
      {
        value: [80, 75, 85, 82, 78, 70],
        name: '目标指标',
        itemStyle: { color: '#67C23A' }
      }
    ]
  }]
}))

// 缺陷严重程度分布配置
const defectSeverityOption = computed(() => ({
  tooltip: {
    trigger: 'item'
  },
  series: [{
    name: '缺陷严重程度',
    type: 'pie',
    radius: '70%',
    data: [
      { value: 2, name: '严重', itemStyle: { color: '#F56C6C' } },
      { value: 5, name: '高', itemStyle: { color: '#E6A23C' } },
      { value: 8, name: '中', itemStyle: { color: '#409EFF' } },
      { value: 8, name: '低', itemStyle: { color: '#67C23A' } }
    ],
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }]
}))

// 覆盖率分布配置
const coverageDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    name: '模块数量',
    type: 'bar',
    data: [2, 5, 8, 15, 25],
    itemStyle: {
      color: new (window as any).echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#409EFF' },
        { offset: 1, color: '#67C23A' }
      ])
    }
  }]
}))

// 月度趋势配置
const monthlyTrendOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月']
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    name: '质量分数',
    type: 'line',
    data: [7.8, 8.1, 8.3, 8.0, 8.5, 8.6],
    smooth: true,
    itemStyle: { color: '#67C23A' },
    areaStyle: { opacity: 0.3 }
  }]
}))

// 操作方法
const generateReport = () => {
  generating.value = true
  setTimeout(() => {
    generating.value = false
    ElMessage.success('报告生成成功')
    emit('generateReport')
  }, 2000)
}

const analyzeCoverage = () => {
  ElMessage.info('开始分析覆盖率...')
  emit('analyzeCoverage')
}

const checkDefects = () => {
  ElMessage.info('开始检查缺陷...')
  emit('checkDefects')
}

const exportData = () => {
  ElMessage.info('开始导出数据...')
  emit('exportData')
}

const refreshActivities = () => {
  ElMessage.success('活动数据已刷新')
}

// 获取活动类型
const getActivityType = (type: string) => {
  const typeMap: Record<string, string> = {
    'report': 'primary',
    'defect': 'danger',
    'coverage': 'success',
    'alert': 'warning'
  }
  return typeMap[type] || 'info'
}

onMounted(() => {
  // 初始化数据加载
})
</script>

<style scoped>
.stats-dashboard {
  padding: 20px;
}

.overview-section {
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

.overview-card .icon.reports {
  background: #409EFF;
}

.overview-card .icon.defects {
  background: #F56C6C;
}

.overview-card .icon.coverage {
  background: #67C23A;
}

.overview-card .icon.quality {
  background: #E6A23C;
}

.overview-card .info {
  flex: 1;
}

.overview-card .info h3 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.overview-card .info p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: bold;
}

.trend.up {
  color: #67C23A;
}

.trend.down {
  color: #F56C6C;
}

.quick-actions {
  margin-bottom: 20px;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-container {
  height: 350px;
}

.chart-container.small {
  height: 250px;
}

.recent-activities {
  margin-bottom: 20px;
}

.activities-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-content {
  margin-bottom: 10px;
}

.activity-title {
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.activity-description {
  color: #666;
  font-size: 14px;
}
</style>