<template>
  <div class="real-time-metrics">
    <el-card>
      <template #header>
        <div class="metrics-header">
          <span>实时指标监控</span>
          <div class="header-controls">
            <el-switch
              v-model="autoRefresh"
              active-text="自动刷新"
              @change="toggleAutoRefresh"
            />
            <el-select v-model="refreshInterval" size="small" style="width: 100px;">
              <el-option label="5秒" :value="5000" />
              <el-option label="10秒" :value="10000" />
              <el-option label="30秒" :value="30000" />
              <el-option label="1分钟" :value="60000" />
            </el-select>
            <el-button size="small" @click="refreshMetrics">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <!-- 关键指标卡片 -->
      <div class="key-metrics">
        <el-row :gutter="16">
          <el-col :span="6" v-for="metric in keyMetrics" :key="metric.key">
            <div class="metric-card" :class="getMetricStatus(metric.value, metric.thresholds)">
              <div class="metric-icon">
                <el-icon>
                  <component :is="metric.icon" />
                </el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">
                  {{ formatMetricValue(metric.value, metric.unit) }}
                </div>
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-change" :class="getChangeClass(metric.change)">
                  <el-icon v-if="metric.change > 0"><ArrowUp /></el-icon>
                  <el-icon v-else-if="metric.change < 0"><ArrowDown /></el-icon>
                  <el-icon v-else><Minus /></el-icon>
                  <span>{{ Math.abs(metric.change) }}{{ metric.unit === 'percent' ? '%' : '' }}</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 实时图表 -->
      <div class="realtime-charts">
        <el-row :gutter="16">
          <!-- 系统负载图表 -->
          <el-col :span="12">
            <div class="chart-container">
              <h4>系统负载</h4>
              <v-chart 
                :option="systemLoadOption" 
                :loading="loading"
                ref="systemLoadChart"
              />
            </div>
          </el-col>

          <!-- 网络流量图表 -->
          <el-col :span="12">
            <div class="chart-container">
              <h4>网络流量</h4>
              <v-chart 
                :option="networkTrafficOption" 
                :loading="loading"
                ref="networkTrafficChart"
              />
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 20px;">
          <!-- 数据库连接池 -->
          <el-col :span="8">
            <div class="chart-container small">
              <h4>数据库连接池</h4>
              <v-chart 
                :option="dbConnectionOption" 
                :loading="loading"
              />
            </div>
          </el-col>

          <!-- 缓存命中率 -->
          <el-col :span="8">
            <div class="chart-container small">
              <h4>缓存命中率</h4>
              <v-chart 
                :option="cacheHitRateOption" 
                :loading="loading"
              />
            </div>
          </el-col>

          <!-- API响应时间 -->
          <el-col :span="8">
            <div class="chart-container small">
              <h4>API响应时间</h4>
              <v-chart 
                :option="apiResponseTimeOption" 
                :loading="loading"
              />
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 性能指标表格 -->
      <div class="metrics-table">
        <h4>详细指标</h4>
        <el-table :data="detailedMetrics" size="small" max-height="300">
          <el-table-column prop="name" label="指标名称" width="200" />
          <el-table-column prop="current_value" label="当前值" width="120">
            <template #default="{ row }">
              {{ formatMetricValue(row.current_value, row.unit) }}
            </template>
          </el-table-column>
          <el-table-column prop="avg_value" label="平均值" width="120">
            <template #default="{ row }">
              {{ formatMetricValue(row.avg_value, row.unit) }}
            </template>
          </el-table-column>
          <el-table-column prop="max_value" label="最大值" width="120">
            <template #default="{ row }">
              {{ formatMetricValue(row.max_value, row.unit) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="getStatusType(row.status)" 
                size="small"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_updated" label="更新时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.last_updated) }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
        </el-table>
      </div>

      <!-- 告警阈值设置 -->
      <div class="threshold-settings" v-if="showThresholdSettings">
        <h4>告警阈值设置</h4>
        <el-form :model="thresholdForm" size="small" label-width="120px">
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="CPU使用率">
                <el-input-number 
                  v-model="thresholdForm.cpu_warning" 
                  :min="0" 
                  :max="100" 
                  :precision="1"
                />
                <span style="margin: 0 10px;">%</span>
                <el-input-number 
                  v-model="thresholdForm.cpu_critical" 
                  :min="0" 
                  :max="100" 
                  :precision="1"
                />
                <span style="margin-left: 5px;">%</span>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="内存使用率">
                <el-input-number 
                  v-model="thresholdForm.memory_warning" 
                  :min="0" 
                  :max="100" 
                  :precision="1"
                />
                <span style="margin: 0 10px;">%</span>
                <el-input-number 
                  v-model="thresholdForm.memory_critical" 
                  :min="0" 
                  :max="100" 
                  :precision="1"
                />
                <span style="margin-left: 5px;">%</span>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="响应时间">
                <el-input-number 
                  v-model="thresholdForm.response_warning" 
                  :min="0" 
                  :precision="0"
                />
                <span style="margin: 0 10px;">ms</span>
                <el-input-number 
                  v-model="thresholdForm.response_critical" 
                  :min="0" 
                  :precision="0"
                />
                <span style="margin-left: 5px;">ms</span>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <el-button type="primary" size="small" @click="saveThresholds">
              保存设置
            </el-button>
            <el-button size="small" @click="resetThresholds">
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  ArrowUp,
  ArrowDown,
  Minus,
  Monitor,
  Connection,
  Timer,
  DataBoard
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  LineChart,
  GaugeChart,
  BarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  LineChart,
  GaugeChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

interface KeyMetric {
  key: string
  label: string
  value: number
  unit: 'percent' | 'ms' | 'count' | 'bytes'
  change: number
  icon: any
  thresholds: {
    warning: number
    critical: number
  }
}

interface DetailedMetric {
  name: string
  current_value: number
  avg_value: number
  max_value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  last_updated: string
  description: string
}

interface ThresholdForm {
  cpu_warning: number
  cpu_critical: number
  memory_warning: number
  memory_critical: number
  response_warning: number
  response_critical: number
}

const props = defineProps<{
  showThresholdSettings?: boolean
}>()

const emit = defineEmits<{
  thresholdUpdate: [thresholds: ThresholdForm]
}>()

const loading = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref(10000) // 10秒
const showThresholdSettings = ref(props.showThresholdSettings || false)

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 关键指标数据
const keyMetrics = ref<KeyMetric[]>([
  {
    key: 'cpu',
    label: 'CPU使用率',
    value: 45.2,
    unit: 'percent',
    change: -2.1,
    icon: Monitor,
    thresholds: { warning: 70, critical: 90 }
  },
  {
    key: 'memory',
    label: '内存使用率',
    value: 68.5,
    unit: 'percent',
    change: 1.3,
    icon: DataBoard,
    thresholds: { warning: 80, critical: 95 }
  },
  {
    key: 'response_time',
    label: '平均响应时间',
    value: 245,
    unit: 'ms',
    change: -15,
    icon: Timer,
    thresholds: { warning: 500, critical: 1000 }
  },
  {
    key: 'connections',
    label: '活跃连接数',
    value: 127,
    unit: 'count',
    change: 8,
    icon: Connection,
    thresholds: { warning: 200, critical: 300 }
  }
])

// 详细指标数据
const detailedMetrics = ref<DetailedMetric[]>([
  {
    name: 'CPU使用率',
    current_value: 45.2,
    avg_value: 42.8,
    max_value: 78.5,
    unit: 'percent',
    status: 'normal',
    last_updated: new Date().toISOString(),
    description: '系统CPU使用率'
  },
  {
    name: '内存使用率',
    current_value: 68.5,
    avg_value: 65.2,
    max_value: 85.3,
    unit: 'percent',
    status: 'normal',
    last_updated: new Date().toISOString(),
    description: '系统内存使用率'
  },
  {
    name: '磁盘I/O',
    current_value: 23.1,
    avg_value: 28.5,
    max_value: 67.2,
    unit: 'percent',
    status: 'normal',
    last_updated: new Date().toISOString(),
    description: '磁盘读写使用率'
  },
  {
    name: '网络带宽',
    current_value: 156.7,
    avg_value: 142.3,
    max_value: 234.8,
    unit: 'mbps',
    status: 'normal',
    last_updated: new Date().toISOString(),
    description: '网络带宽使用情况'
  }
])

// 阈值设置表单
const thresholdForm = ref<ThresholdForm>({
  cpu_warning: 70,
  cpu_critical: 90,
  memory_warning: 80,
  memory_critical: 95,
  response_warning: 500,
  response_critical: 1000
})

// 实时数据
const systemLoadData = ref<number[][]>([[], [], []])
const networkTrafficData = ref<number[][]>([[], []])
const timeLabels = ref<string[]>([])

// 图表配置
const systemLoadOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['CPU', '内存', '磁盘I/O']
  },
  xAxis: {
    type: 'category',
    data: timeLabels.value
  },
  yAxis: {
    type: 'value',
    max: 100,
    axisLabel: {
      formatter: '{value}%'
    }
  },
  series: [
    {
      name: 'CPU',
      type: 'line',
      data: systemLoadData.value[0],
      smooth: true,
      itemStyle: { color: '#409EFF' }
    },
    {
      name: '内存',
      type: 'line',
      data: systemLoadData.value[1],
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '磁盘I/O',
      type: 'line',
      data: systemLoadData.value[2],
      smooth: true,
      itemStyle: { color: '#E6A23C' }
    }
  ]
}))

const networkTrafficOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['入站流量', '出站流量']
  },
  xAxis: {
    type: 'category',
    data: timeLabels.value
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: '{value} MB/s'
    }
  },
  series: [
    {
      name: '入站流量',
      type: 'line',
      data: networkTrafficData.value[0],
      smooth: true,
      itemStyle: { color: '#409EFF' },
      areaStyle: { opacity: 0.3 }
    },
    {
      name: '出站流量',
      type: 'line',
      data: networkTrafficData.value[1],
      smooth: true,
      itemStyle: { color: '#67C23A' },
      areaStyle: { opacity: 0.3 }
    }
  ]
}))

const dbConnectionOption = computed(() => ({
  series: [{
    name: '连接池使用率',
    type: 'gauge',
    detail: {
      formatter: '{value}%'
    },
    data: [{ value: 65, name: '连接池' }],
    axisLine: {
      lineStyle: {
        width: 20,
        color: [
          [0.7, '#67C23A'],
          [0.9, '#E6A23C'],
          [1, '#F56C6C']
        ]
      }
    }
  }]
}))

const cacheHitRateOption = computed(() => ({
  series: [{
    name: '缓存命中率',
    type: 'gauge',
    detail: {
      formatter: '{value}%'
    },
    data: [{ value: 92, name: '命中率' }],
    axisLine: {
      lineStyle: {
        width: 20,
        color: [
          [0.8, '#F56C6C'],
          [0.95, '#E6A23C'],
          [1, '#67C23A']
        ]
      }
    }
  }]
}))

const apiResponseTimeOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['<100ms', '100-300ms', '300-500ms', '500ms-1s', '>1s']
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    name: '请求数量',
    type: 'bar',
    data: [45, 32, 18, 8, 2],
    itemStyle: {
      color: (params: any) => {
        const colors = ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C', '#909399']
        return colors[params.dataIndex]
      }
    }
  }]
}))

// 方法
const refreshMetrics = async () => {
  loading.value = true
  try {
    // 模拟数据更新
    await new Promise(resolve => setTimeout(resolve, 500))
    
    updateMetricsData()
    updateChartData()
    
    ElMessage.success('指标数据已刷新')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const updateMetricsData = () => {
  keyMetrics.value.forEach(metric => {
    // 模拟数据变化
    const change = (Math.random() - 0.5) * 10
    metric.value = Math.max(0, Math.min(100, metric.value + change))
    metric.change = change
  })

  detailedMetrics.value.forEach(metric => {
    const change = (Math.random() - 0.5) * 5
    metric.current_value = Math.max(0, metric.current_value + change)
    metric.last_updated = new Date().toISOString()
    
    // 更新状态
    if (metric.name === 'CPU使用率' || metric.name === '内存使用率') {
      if (metric.current_value > 90) {
        metric.status = 'critical'
      } else if (metric.current_value > 70) {
        metric.status = 'warning'
      } else {
        metric.status = 'normal'
      }
    }
  })
}

const updateChartData = () => {
  const now = new Date()
  const timeLabel = now.toLocaleTimeString()
  
  // 更新时间标签
  timeLabels.value.push(timeLabel)
  if (timeLabels.value.length > 20) {
    timeLabels.value.shift()
  }
  
  // 更新系统负载数据
  systemLoadData.value[0].push(Math.floor(Math.random() * 100))
  systemLoadData.value[1].push(Math.floor(Math.random() * 100))
  systemLoadData.value[2].push(Math.floor(Math.random() * 100))
  
  systemLoadData.value.forEach(series => {
    if (series.length > 20) {
      series.shift()
    }
  })
  
  // 更新网络流量数据
  networkTrafficData.value[0].push(Math.floor(Math.random() * 50))
  networkTrafficData.value[1].push(Math.floor(Math.random() * 30))
  
  networkTrafficData.value.forEach(series => {
    if (series.length > 20) {
      series.shift()
    }
  })
}

const toggleAutoRefresh = (enabled: boolean) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    refreshMetrics()
  }, refreshInterval.value)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const saveThresholds = () => {
  // 更新关键指标的阈值
  keyMetrics.value.forEach(metric => {
    switch (metric.key) {
      case 'cpu':
        metric.thresholds.warning = thresholdForm.value.cpu_warning
        metric.thresholds.critical = thresholdForm.value.cpu_critical
        break
      case 'memory':
        metric.thresholds.warning = thresholdForm.value.memory_warning
        metric.thresholds.critical = thresholdForm.value.memory_critical
        break
      case 'response_time':
        metric.thresholds.warning = thresholdForm.value.response_warning
        metric.thresholds.critical = thresholdForm.value.response_critical
        break
    }
  })
  
  emit('thresholdUpdate', thresholdForm.value)
  ElMessage.success('阈值设置已保存')
}

const resetThresholds = () => {
  thresholdForm.value = {
    cpu_warning: 70,
    cpu_critical: 90,
    memory_warning: 80,
    memory_critical: 95,
    response_warning: 500,
    response_critical: 1000
  }
  ElMessage.info('阈值已重置为默认值')
}

// 辅助函数
const formatMetricValue = (value: number, unit: string) => {
  switch (unit) {
    case 'percent':
      return `${value.toFixed(1)}%`
    case 'ms':
      return `${Math.round(value)}ms`
    case 'count':
      return Math.round(value).toString()
    case 'bytes':
      return `${(value / 1024 / 1024).toFixed(1)}MB`
    case 'mbps':
      return `${value.toFixed(1)} MB/s`
    default:
      return value.toString()
  }
}

const getMetricStatus = (value: number, thresholds: { warning: number; critical: number }) => {
  if (value >= thresholds.critical) return 'critical'
  if (value >= thresholds.warning) return 'warning'
  return 'normal'
}

const getChangeClass = (change: number) => {
  if (change > 0) return 'change-up'
  if (change < 0) return 'change-down'
  return 'change-stable'
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'normal': 'success',
    'warning': 'warning',
    'critical': 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'normal': '正常',
    'warning': '警告',
    'critical': '严重'
  }
  return texts[status] || status
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  // 初始化数据
  for (let i = 0; i < 10; i++) {
    updateChartData()
  }
  
  refreshMetrics()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.real-time-metrics {
  width: 100%;
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.key-metrics {
  margin-bottom: 30px;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  background: #f8f9fa;
  gap: 15px;
  transition: all 0.3s ease;
}

.metric-card.normal {
  border-left: 4px solid #67C23A;
}

.metric-card.warning {
  border-left: 4px solid #E6A23C;
  background: #fdf6ec;
}

.metric-card.critical {
  border-left: 4px solid #F56C6C;
  background: #fef0f0;
}

.metric-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: bold;
}

.change-up {
  color: #67C23A;
}

.change-down {
  color: #F56C6C;
}

.change-stable {
  color: #909399;
}

.realtime-charts {
  margin-bottom: 30px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-container h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.chart-container:not(.small) {
  height: 350px;
}

.chart-container.small {
  height: 250px;
}

.metrics-table {
  margin-bottom: 30px;
}

.metrics-table h4 {
  margin-bottom: 15px;
  color: #333;
}

.threshold-settings {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.threshold-settings h4 {
  margin-bottom: 15px;
  color: #333;
}
</style>