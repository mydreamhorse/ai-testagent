<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- Statistics Cards -->
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24" :color="'white'">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Recent Activities -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
              <el-button type="text" @click="viewAllActivities">查看全部</el-button>
            </div>
          </template>
          <div class="activity-list">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon">
                <el-icon :color="activity.color">
                  <component :is="activity.icon" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-time">{{ formatTime(activity.time) }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- Quality Trends -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>质量趋势</span>
              <el-button type="text" @click="viewDetailedAnalytics">详细分析</el-button>
            </div>
          </template>
          <div class="chart-container">
            <v-chart
              :option="qualityChartOption"
              style="height: 300px"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Test Case Distribution -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>测试用例分布</span>
          </template>
          <div class="chart-container">
            <v-chart
              :option="distributionChartOption"
              style="height: 250px"
            />
          </div>
        </el-card>
      </el-col>
      
      <!-- Quick Actions -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button
              v-for="action in quickActions"
              :key="action.title"
              :type="action.type"
              class="action-btn"
              @click="handleQuickAction(action.action)"
            >
              <el-icon><component :is="action.icon" /></el-icon>
              {{ action.title }}
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <!-- Recent Requirements -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新需求</span>
              <el-button type="text" @click="viewAllRequirements">查看全部</el-button>
            </div>
          </template>
          <div class="requirement-list">
            <div
              v-for="req in recentRequirements"
              :key="req.id"
              class="requirement-item"
              @click="viewRequirement(req.id)"
            >
              <div class="requirement-title">{{ req.title }}</div>
              <div class="requirement-meta">
                <el-tag :type="getStatusType(req.status)" size="small">
                  {{ getStatusText(req.status) }}
                </el-tag>
                <span class="requirement-date">{{ formatDate(req.created_at) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const router = useRouter()

// Mock data
const stats = ref([
  {
    title: '总需求数',
    value: '24',
    icon: 'Document',
    color: '#409eff'
  },
  {
    title: '测试用例',
    value: '186',
    icon: 'List',
    color: '#67c23a'
  },
  {
    title: '平均质量分',
    value: '87.5',
    icon: 'Trophy',
    color: '#e6a23c'
  },
  {
    title: '生成效率',
    value: '92%',
    icon: 'TrendCharts',
    color: '#f56c6c'
  }
])

const recentActivities = ref([
  {
    id: 1,
    title: '新增需求"座椅电动调节功能"',
    time: new Date(Date.now() - 1000 * 60 * 30),
    icon: 'Plus',
    color: '#409eff'
  },
  {
    id: 2,
    title: '完成测试用例生成',
    time: new Date(Date.now() - 1000 * 60 * 60),
    icon: 'Check',
    color: '#67c23a'
  },
  {
    id: 3,
    title: '质量评估完成',
    time: new Date(Date.now() - 1000 * 60 * 60 * 2),
    icon: 'Star',
    color: '#e6a23c'
  }
])

const recentRequirements = ref([
  {
    id: 1,
    title: '座椅电动调节功能',
    status: 'completed',
    created_at: '2023-12-01T10:30:00Z'
  },
  {
    id: 2,
    title: '座椅记忆功能',
    status: 'processing',
    created_at: '2023-12-01T09:15:00Z'
  },
  {
    id: 3,
    title: '座椅加热功能',
    status: 'pending',
    created_at: '2023-11-30T16:45:00Z'
  }
])

const quickActions = ref([
  {
    title: '新增需求',
    action: 'add-requirement',
    icon: 'Plus',
    type: 'primary'
  },
  {
    title: '生成测试用例',
    action: 'generate-tests',
    icon: 'MagicStick',
    type: 'success'
  },
  {
    title: '质量评估',
    action: 'evaluate-quality',
    icon: 'Star',
    type: 'warning'
  }
])

const qualityChartOption = ref({
  title: {
    text: '质量分数趋势',
    left: 'center',
    textStyle: {
      fontSize: 14
    }
  },
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['12-01', '12-02', '12-03', '12-04', '12-05', '12-06', '12-07']
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 100
  },
  series: [
    {
      data: [82, 85, 88, 86, 89, 87, 90],
      type: 'line',
      smooth: true,
      itemStyle: {
        color: '#409eff'
      }
    }
  ]
})

const distributionChartOption = ref({
  title: {
    text: '测试类型分布',
    left: 'center',
    textStyle: {
      fontSize: 14
    }
  },
  tooltip: {
    trigger: 'item'
  },
  series: [
    {
      type: 'pie',
      radius: '60%',
      data: [
        { value: 45, name: '功能测试' },
        { value: 28, name: '边界测试' },
        { value: 18, name: '异常测试' },
        { value: 12, name: '性能测试' },
        { value: 8, name: '安全测试' }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
})

const formatTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    return time.toLocaleDateString()
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
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
  return texts[status] || '未知'
}

const handleQuickAction = (action: string) => {
  switch (action) {
    case 'add-requirement':
      router.push('/requirements')
      break
    case 'generate-tests':
      router.push('/generation')
      break
    case 'evaluate-quality':
      router.push('/test-cases')
      break
  }
}

const viewAllActivities = () => {
  // Navigate to activities page
}

const viewDetailedAnalytics = () => {
  router.push('/analytics')
}

const viewAllRequirements = () => {
  router.push('/requirements')
}

const viewRequirement = (id: number) => {
  router.push(`/requirements/${id}`)
}

onMounted(() => {
  // Load dashboard data
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.stat-title {
  font-size: 14px;
  color: #666;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #999;
}

.chart-container {
  height: 300px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  height: 40px;
  justify-content: flex-start;
}

.requirement-list {
  max-height: 250px;
  overflow-y: auto;
}

.requirement-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.requirement-item:hover {
  background-color: #f9f9f9;
}

.requirement-item:last-child {
  border-bottom: none;
}

.requirement-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.requirement-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.requirement-date {
  font-size: 12px;
  color: #999;
}
</style>