<template>
  <div class="monitoring-dashboard">
    <!-- 系统状态概览 -->
    <div class="system-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <div class="status-icon" :class="systemStatus.overall">
                <el-icon v-if="systemStatus.overall === 'healthy'"><SuccessFilled /></el-icon>
                <el-icon v-else-if="systemStatus.overall === 'warning'"><WarningFilled /></el-icon>
                <el-icon v-else><CircleCloseFilled /></el-icon>
              </div>
              <div class="status-info">
                <h3>{{ getStatusText(systemStatus.overall) }}</h3>
                <p>系统整体状态</p>
                <div class="status-time">
                  最后更新: {{ formatTime(systemStatus.last_update) }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ systemMetrics.cpu_usage }}%</div>
              <div class="metric-label">CPU使用率</div>
              <div class="metric-trend" :class="getTrendClass(systemMetrics.cpu_trend)">
                <el-icon><TrendCharts /></el-icon>
                {{ systemMetrics.cpu_trend > 0 ? '+' : '' }}{{ systemMetrics.cpu_trend }}%
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ systemMetrics.memory_usage }}%</div>
              <div class="metric-label">内存使用率</div>
              <div class="metric-trend" :class="getTrendClass(systemMetrics.memory_trend)">
                <el-icon><TrendCharts /></el-icon>
                {{ systemMetrics.memory_trend > 0 ? '+' : '' }}{{ systemMetrics.memory_trend }}%
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ systemMetrics.active_tests }}</div>
              <div class="metric-label">活跃测试数</div>
              <div class="metric-trend" :class="getTrendClass(systemMetrics.tests_trend)">
                <el-icon><TrendCharts /></el-icon>
                {{ systemMetrics.tests_trend > 0 ? '+' : '' }}{{ systemMetrics.tests_trend }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 实时图表区域 -->
    <div class="realtime-charts">
      <el-row :gutter="20">
        <!-- 系统性能监控 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="chart-header">
                <span>系统性能监控</span>
                <div class="header-controls">
                  <el-switch
                    v-model="autoRefresh"
                    active-text="自动刷新"
                    @change="toggleAutoRefresh"
                  />
                  <el-button size="small" @click="refreshMetrics">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
            <div class="chart-container">
              <v-chart 
                :option="performanceChartOption" 
                :loading="loading"
                ref="performanceChart"
              />
            </div>
          </el-card>
        </el-col>

        <!-- 测试执行监控 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>测试执行监控</span>
            </template>
            <div class="chart-container">
              <v-chart 
                :option="testExecutionChartOption" 
                :loading="loading"
                ref="testExecutionChart"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 错误率监控 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>错误率监控</span>
            </template>
            <div class="chart-container small">
              <v-chart 
                :option="errorRateChartOption" 
                :loading="loading"
              />
            </div>
          </el-card>
        </el-col>

        <!-- 响应时间分布 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>响应时间分布</span>
            </template>
            <div class="chart-container small">
              <v-chart 
                :option="responseTimeChartOption" 
                :loading="loading"
              />
            </div>
          </el-card>
        </el-col>

        <!-- 资源使用趋势 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>资源使用趋势</span>
            </template>
            <div class="chart-container small">
              <v-chart 
                :option="resourceUsageChartOption" 
                :loading="loading"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 告警状态面板 -->
    <div class="alerts-panel">
      <el-card>
        <template #header>
          <div class="alerts-header">
            <span>实时告警</span>
            <div class="alert-summary">
              <el-badge :value="alertCounts.critical" type="danger" class="alert-badge">
                <el-button size="small" type="danger" plain>严重</el-button>
              </el-badge>
              <el-badge :value="alertCounts.warning" type="warning" class="alert-badge">
                <el-button size="small" type="warning" plain>警告</el-button>
              </el-badge>
              <el-badge :value="alertCounts.info" type="info" class="alert-badge">
                <el-button size="small" type="info" plain>信息</el-button>
              </el-badge>
            </div>
          </div>
        </template>

        <div class="alerts-content">
          <el-table 
            :data="recentAlerts" 
            size="small" 
            max-height="300"
            :default-sort="{ prop: 'timestamp', order: 'descending' }"
          >
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag 
                  :type="getSeverityType(row.severity)" 
                  size="small"
                >
                  {{ getSeverityText(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="告警内容" show-overflow-tooltip />
            <el-table-column prop="source" label="来源" width="120" />
            <el-table-column prop="timestamp" label="时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag 
                  :type="row.status === 'resolved' ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ row.status === 'resolved' ? '已解决' : '活跃' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  type="text" 
                  @click="viewAlertDetail(row)"
                >
                  详情
                </el-button>
                <el-button 
                  v-if="row.status === 'active'"
                  size="small" 
                  type="text" 
                  @click="acknowledgeAlert(row)"
                >
                  确认
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- 系统日志面板 -->
    <div class="logs-panel">
      <el-card>
        <template #header>
          <div class="logs-header">
            <span>系统日志</span>
            <div class="log-controls">
              <el-select v-model="logLevel" size="small" style="width: 100px;">
                <el-option label="全部" value="all" />
                <el-option label="错误" value="error" />
                <el-option label="警告" value="warning" />
                <el-option label="信息" value="info" />
                <el-option label="调试" value="debug" />
              </el-select>
              <el-button size="small" @click="clearLogs">
                <el-icon><Delete /></el-icon>
                清空
              </el-button>
              <el-button size="small" @click="downloadLogs">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
            </div>
          </div>
        </template>

        <div class="logs-content">
          <div class="log-viewer" ref="logViewer">
            <div 
              v-for="log in filteredLogs" 
              :key="log.id"
              class="log-entry"
              :class="log.level"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-source">{{ log.source }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled,
  TrendCharts,
  Refresh,
  Delete,
  Download
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  LineChart,
  BarChart,
  GaugeChart
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
  BarChart,
  GaugeChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

interface SystemStatus {
  overall: 'healthy' | 'warning' | 'critical'
  last_update: string
}

interface SystemMetrics {
  cpu_usage: number
  cpu_trend: number
  memory_usage: number
  memory_trend: number
  active_tests: number
  tests_trend: number
}

interface Alert {
  id: number
  severity: 'critical' | 'warning' | 'info'
  title: string
  source: string
  timestamp: string
  status: 'active' | 'resolved'
  description?: string
}

interface LogEntry {
  id: number
  level: 'error' | 'warning' | 'info' | 'debug'
  source: string
  message: string
  timestamp: string
}

const loading = ref(false)
const autoRefresh = ref(true)
const logLevel = ref('all')

// 系统状态数据
const systemStatus = ref<SystemStatus>({
  overall: 'healthy',
  last_update: new Date().toISOString()
})

// 系统指标数据
const systemMetrics = ref<SystemMetrics>({
  cpu_usage: 45,
  cpu_trend: -2.1,
  memory_usage: 68,
  memory_trend: 1.5,
  active_tests: 12,
  tests_trend: 3
})

// 告警数据
const recentAlerts = ref<Alert[]>([
  {
    id: 1,
    severity: 'warning',
    title: 'CPU使用率持续偏高',
    source: '系统监控',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    status: 'active'
  },
  {
    id: 2,
    severity: 'info',
    title: '测试用例执行完成',
    source: '测试引擎',
    timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    status: 'resolved'
  },
  {
    id: 3,
    severity: 'critical',
    title: '数据库连接异常',
    source: '数据库',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    status: 'active'
  }
])

// 系统日志数据
const systemLogs = ref<LogEntry[]>([
  {
    id: 1,
    level: 'info',
    source: 'TestEngine',
    message: '开始执行测试用例 TC_001',
    timestamp: new Date().toISOString()
  },
  {
    id: 2,
    level: 'warning',
    source: 'SystemMonitor',
    message: 'CPU使用率超过阈值: 85%',
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString()
  },
  {
    id: 3,
    level: 'error',
    source: 'Database',
    message: '数据库连接超时',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString()
  }
])

// 实时数据
const performanceData = ref<number[][]>([])
const testExecutionData = ref<number[]>([])
const errorRateData = ref<number[]>([])
const responseTimeData = ref<number[]>([])

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 计算属性
const alertCounts = computed(() => {
  const counts = { critical: 0, warning: 0, info: 0 }
  recentAlerts.value.forEach(alert => {
    if (alert.status === 'active') {
      counts[alert.severity]++
    }
  })
  return counts
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') {
    return systemLogs.value
  }
  return systemLogs.value.filter(log => log.level === logLevel.value)
})

// 图表配置
const performanceChartOption = computed(() => ({
  title: {
    text: '系统性能实时监控'
  },
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['CPU使用率', '内存使用率', '磁盘I/O']
  },
  xAxis: {
    type: 'category',
    data: Array.from({ length: 20 }, (_, i) => {
      const time = new Date(Date.now() - (19 - i) * 30 * 1000)
      return time.toLocaleTimeString()
    })
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
      name: 'CPU使用率',
      type: 'line',
      data: performanceData.value[0] || [],
      smooth: true,
      itemStyle: { color: '#409EFF' }
    },
    {
      name: '内存使用率',
      type: 'line',
      data: performanceData.value[1] || [],
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '磁盘I/O',
      type: 'line',
      data: performanceData.value[2] || [],
      smooth: true,
      itemStyle: { color: '#E6A23C' }
    }
  ]
}))

const testExecutionChartOption = computed(() => ({
  title: {
    text: '测试执行状态'
  },
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: ['通过', '失败', '跳过', '执行中']
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    name: '测试数量',
    type: 'bar',
    data: testExecutionData.value,
    itemStyle: {
      color: (params: any) => {
        const colors = ['#67C23A', '#F56C6C', '#E6A23C', '#409EFF']
        return colors[params.dataIndex]
      }
    }
  }]
}))

const errorRateChartOption = computed(() => ({
  series: [{
    name: '错误率',
    type: 'gauge',
    detail: {
      formatter: '{value}%'
    },
    data: [{ value: errorRateData.value[0] || 0, name: '错误率' }]
  }]
}))

const responseTimeChartOption = computed(() => ({
  title: {
    text: '响应时间分布'
  },
  tooltip: {
    trigger: 'item'
  },
  series: [{
    name: '响应时间',
    type: 'pie',
    radius: '70%',
    data: [
      { value: 35, name: '<100ms', itemStyle: { color: '#67C23A' } },
      { value: 25, name: '100-500ms', itemStyle: { color: '#409EFF' } },
      { value: 20, name: '500ms-1s', itemStyle: { color: '#E6A23C' } },
      { value: 15, name: '1-3s', itemStyle: { color: '#F56C6C' } },
      { value: 5, name: '>3s', itemStyle: { color: '#909399' } }
    ]
  }]
}))

const resourceUsageChartOption = computed(() => ({
  title: {
    text: '资源使用趋势'
  },
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'category',
    data: Array.from({ length: 10 }, (_, i) => `${i + 1}min`)
  },
  yAxis: {
    type: 'value'
  },
  series: [{
    name: '资源使用率',
    type: 'line',
    data: Array.from({ length: 10 }, () => Math.floor(Math.random() * 100)),
    smooth: true,
    areaStyle: { opacity: 0.3 },
    itemStyle: { color: '#409EFF' }
  }]
}))

// 方法
const refreshMetrics = async () => {
  loading.value = true
  try {
    // 模拟数据更新
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新性能数据
    updatePerformanceData()
    updateTestExecutionData()
    updateErrorRateData()
    
    systemStatus.value.last_update = new Date().toISOString()
    ElMessage.success('监控数据已刷新')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

const updatePerformanceData = () => {
  const cpuData = Array.from({ length: 20 }, () => Math.floor(Math.random() * 100))
  const memoryData = Array.from({ length: 20 }, () => Math.floor(Math.random() * 100))
  const diskData = Array.from({ length: 20 }, () => Math.floor(Math.random() * 100))
  
  performanceData.value = [cpuData, memoryData, diskData]
}

const updateTestExecutionData = () => {
  testExecutionData.value = [
    Math.floor(Math.random() * 50) + 20, // 通过
    Math.floor(Math.random() * 10) + 2,  // 失败
    Math.floor(Math.random() * 5) + 1,   // 跳过
    Math.floor(Math.random() * 8) + 2    // 执行中
  ]
}

const updateErrorRateData = () => {
  errorRateData.value = [Math.floor(Math.random() * 10) + 1]
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
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const viewAlertDetail = (alert: Alert) => {
  ElMessageBox.alert(
    alert.description || '暂无详细描述',
    alert.title,
    {
      confirmButtonText: '确定',
      type: alert.severity === 'critical' ? 'error' : 
            alert.severity === 'warning' ? 'warning' : 'info'
    }
  )
}

const acknowledgeAlert = async (alert: Alert) => {
  try {
    alert.status = 'resolved'
    ElMessage.success('告警已确认')
  } catch (error) {
    ElMessage.error('确认告警失败')
  }
}

const clearLogs = () => {
  systemLogs.value = []
  ElMessage.success('日志已清空')
}

const downloadLogs = () => {
  const logContent = systemLogs.value
    .map(log => `${log.timestamp} [${log.level.toUpperCase()}] ${log.source}: ${log.message}`)
    .join('\n')
  
  const blob = new Blob([logContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `system-logs-${new Date().toISOString().split('T')[0]}.txt`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('日志下载完成')
}

// 辅助函数
const getStatusText = (status: string) => {
  const statusTexts: Record<string, string> = {
    'healthy': '健康',
    'warning': '警告',
    'critical': '严重'
  }
  return statusTexts[status] || status
}

const getTrendClass = (trend: number) => {
  if (trend > 0) return 'trend-up'
  if (trend < 0) return 'trend-down'
  return 'trend-stable'
}

const getSeverityType = (severity: string) => {
  const types: Record<string, string> = {
    'critical': 'danger',
    'warning': 'warning',
    'info': 'info'
  }
  return types[severity] || 'info'
}

const getSeverityText = (severity: string) => {
  const texts: Record<string, string> = {
    'critical': '严重',
    'warning': '警告',
    'info': '信息'
  }
  return texts[severity] || severity
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
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
.monitoring-dashboard {
  padding: 20px;
}

.system-overview {
  margin-bottom: 20px;
}

.status-card .status-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.status-icon.healthy {
  background: #67C23A;
}

.status-icon.warning {
  background: #E6A23C;
}

.status-icon.critical {
  background: #F56C6C;
}

.status-info h3 {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.status-info p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.status-time {
  font-size: 12px;
  color: #999;
}

.metric-card .metric-content {
  text-align: center;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  font-weight: bold;
}

.trend-up {
  color: #67C23A;
}

.trend-down {
  color: #F56C6C;
}

.trend-stable {
  color: #909399;
}

.realtime-charts {
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chart-container {
  height: 350px;
}

.chart-container.small {
  height: 250px;
}

.alerts-panel {
  margin-bottom: 20px;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-summary {
  display: flex;
  gap: 10px;
}

.alert-badge {
  margin-right: 10px;
}

.logs-panel {
  margin-bottom: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.log-viewer {
  height: 300px;
  overflow-y: auto;
  background: #f8f9fa;
  border-radius: 4px;
  padding: 10px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.log-entry {
  display: flex;
  gap: 10px;
  padding: 2px 0;
  border-bottom: 1px solid #eee;
}

.log-entry.error {
  color: #F56C6C;
}

.log-entry.warning {
  color: #E6A23C;
}

.log-entry.info {
  color: #409EFF;
}

.log-entry.debug {
  color: #909399;
}

.log-time {
  width: 120px;
  flex-shrink: 0;
}

.log-level {
  width: 60px;
  flex-shrink: 0;
  font-weight: bold;
}

.log-source {
  width: 100px;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
}
</style>