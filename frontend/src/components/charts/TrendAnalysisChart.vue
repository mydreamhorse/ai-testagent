<template>
  <div class="trend-analysis-chart">
    <el-card>
      <template #header>
        <div class="trend-header">
          <span>{{ title }}</span>
          <div class="header-controls">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              @change="handleDateRangeChange"
            />
            <el-select v-model="trendType" size="small" style="width: 120px;">
              <el-option label="测试执行" value="execution" />
              <el-option label="缺陷发现" value="defects" />
              <el-option label="覆盖率变化" value="coverage" />
              <el-option label="质量指标" value="quality" />
            </el-select>
            <el-button size="small" @click="exportTrendData">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>
      </template>

      <div class="trend-container">
        <v-chart 
          :option="trendOption" 
          :loading="loading"
          @click="handleDataPointClick"
        />
      </div>

      <!-- 趋势分析摘要 -->
      <div class="trend-summary">
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="summary-card">
              <div class="summary-header">
                <el-icon class="trend-up"><TrendCharts /></el-icon>
                <span>趋势分析</span>
              </div>
              <div class="summary-content">
                <div class="trend-indicator" :class="trendIndicator.type">
                  <el-icon v-if="trendIndicator.type === 'up'"><ArrowUp /></el-icon>
                  <el-icon v-else-if="trendIndicator.type === 'down'"><ArrowDown /></el-icon>
                  <el-icon v-else><Minus /></el-icon>
                  <span>{{ trendIndicator.text }}</span>
                </div>
                <div class="trend-description">{{ trendIndicator.description }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-card">
              <div class="summary-header">
                <el-icon class="prediction"><Star /></el-icon>
                <span>预测分析</span>
              </div>
              <div class="summary-content">
                <div class="prediction-value">{{ prediction.value }}</div>
                <div class="prediction-description">{{ prediction.description }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-card">
              <div class="summary-header">
                <el-icon class="recommendation"><InfoFilled /></el-icon>
                <span>改进建议</span>
              </div>
              <div class="summary-content">
                <div class="recommendation-list">
                  <div 
                    v-for="(rec, index) in recommendations" 
                    :key="index"
                    class="recommendation-item"
                  >
                    {{ rec }}
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 详细数据表格 -->
      <div class="trend-details" v-if="showDetails">
        <el-table :data="trendDetails" size="small" max-height="300">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="value" label="数值" width="100" />
          <el-table-column prop="change" label="变化" width="100">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change)">
                {{ row.change > 0 ? '+' : '' }}{{ row.change }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_rate" label="变化率" width="100">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_rate)">
                {{ row.change_rate > 0 ? '+' : '' }}{{ row.change_rate }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" show-overflow-tooltip />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Download, 
  TrendCharts, 
  ArrowUp, 
  ArrowDown, 
  Minus,
  Star,
  InfoFilled
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  LineChart,
  BarChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkLineComponent
])

interface TrendDataPoint {
  date: string
  value: number
  change?: number
  change_rate?: number
  notes?: string
}

interface TrendIndicator {
  type: 'up' | 'down' | 'stable'
  text: string
  description: string
}

interface Prediction {
  value: string
  description: string
}

const props = defineProps<{
  title?: string
  data: TrendDataPoint[]
  loading?: boolean
}>()

const emit = defineEmits<{
  dataPointClick: [point: TrendDataPoint]
  dateRangeChange: [range: [Date, Date]]
  exportData: [type: string, range: [Date, Date]]
}>()

const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30天前
  new Date()
])
const trendType = ref<'execution' | 'defects' | 'coverage' | 'quality'>('execution')
const showDetails = ref(false)

// 处理后的趋势数据
const processedData = computed(() => {
  return props.data
    .filter(point => {
      const pointDate = new Date(point.date)
      return pointDate >= dateRange.value[0] && pointDate <= dateRange.value[1]
    })
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
})

// 趋势分析指标
const trendIndicator = computed<TrendIndicator>(() => {
  if (processedData.value.length < 2) {
    return {
      type: 'stable',
      text: '数据不足',
      description: '需要更多数据点进行趋势分析'
    }
  }

  const firstValue = processedData.value[0].value
  const lastValue = processedData.value[processedData.value.length - 1].value
  const changeRate = ((lastValue - firstValue) / firstValue) * 100

  if (changeRate > 5) {
    return {
      type: 'up',
      text: `上升 ${changeRate.toFixed(1)}%`,
      description: '指标呈现上升趋势，表现良好'
    }
  } else if (changeRate < -5) {
    return {
      type: 'down',
      text: `下降 ${Math.abs(changeRate).toFixed(1)}%`,
      description: '指标呈现下降趋势，需要关注'
    }
  } else {
    return {
      type: 'stable',
      text: '保持稳定',
      description: '指标变化较小，保持稳定状态'
    }
  }
})

// 预测分析
const prediction = computed<Prediction>(() => {
  if (processedData.value.length < 3) {
    return {
      value: '无法预测',
      description: '数据点不足，无法进行预测分析'
    }
  }

  // 简单的线性预测
  const recentData = processedData.value.slice(-7) // 最近7个数据点
  const avgChange = recentData.reduce((sum, point, index) => {
    if (index === 0) return sum
    return sum + (point.value - recentData[index - 1].value)
  }, 0) / (recentData.length - 1)

  const lastValue = processedData.value[processedData.value.length - 1].value
  const predictedValue = lastValue + avgChange * 7 // 预测7天后的值

  return {
    value: predictedValue.toFixed(1),
    description: `基于近期趋势，预计7天后数值为 ${predictedValue.toFixed(1)}`
  }
})

// 改进建议
const recommendations = computed<string[]>(() => {
  const recs: string[] = []
  
  if (trendIndicator.value.type === 'down') {
    recs.push('建议加强质量控制措施')
    recs.push('分析下降原因并制定改进计划')
  } else if (trendIndicator.value.type === 'up') {
    recs.push('保持当前良好趋势')
    recs.push('总结成功经验并推广应用')
  } else {
    recs.push('监控关键指标变化')
    recs.push('适时调整策略以促进改进')
  }

  return recs
})

// 趋势详情数据
const trendDetails = computed(() => {
  return processedData.value.map((point, index) => {
    const prevPoint = index > 0 ? processedData.value[index - 1] : null
    const change = prevPoint ? point.value - prevPoint.value : 0
    const change_rate = prevPoint ? ((point.value - prevPoint.value) / prevPoint.value) * 100 : 0

    return {
      ...point,
      change: Number(change.toFixed(2)),
      change_rate: Number(change_rate.toFixed(2))
    }
  })
})

// 趋势图表配置
const trendOption = computed(() => {
  const dates = processedData.value.map(point => point.date)
  const values = processedData.value.map(point => point.value)

  // 计算移动平均线
  const movingAverage = calculateMovingAverage(values, 7)

  return {
    title: {
      text: getTrendTypeText(trendType.value) + '趋势分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          result += `${param.seriesName}: ${param.value}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['实际值', '移动平均', '趋势线'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100,
        height: 30
      }
    ],
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: getTrendTypeUnit(trendType.value)
    },
    series: [
      {
        name: '实际值',
        type: 'line',
        data: values,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          opacity: 0.3
        },
        smooth: true
      },
      {
        name: '移动平均',
        type: 'line',
        data: movingAverage,
        itemStyle: {
          color: '#67C23A'
        },
        lineStyle: {
          type: 'dashed'
        },
        smooth: true
      },
      {
        name: '趋势线',
        type: 'line',
        data: calculateTrendLine(values),
        itemStyle: {
          color: '#E6A23C'
        },
        lineStyle: {
          type: 'dotted'
        }
      }
    ]
  }
})

// 计算移动平均
const calculateMovingAverage = (data: number[], window: number) => {
  const result: (number | null)[] = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < window - 1) {
      result.push(null)
    } else {
      const sum = data.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / window)
    }
  }
  
  return result
}

// 计算趋势线
const calculateTrendLine = (data: number[]) => {
  if (data.length < 2) return data

  const n = data.length
  const sumX = (n * (n - 1)) / 2
  const sumY = data.reduce((a, b) => a + b, 0)
  const sumXY = data.reduce((sum, y, x) => sum + x * y, 0)
  const sumXX = data.reduce((sum, _, x) => sum + x * x, 0)

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
  const intercept = (sumY - slope * sumX) / n

  return data.map((_, index) => slope * index + intercept)
}

// 处理数据点击
const handleDataPointClick = (params: any) => {
  const point = processedData.value[params.dataIndex]
  if (point) {
    emit('dataPointClick', point)
  }
}

// 处理日期范围变化
const handleDateRangeChange = (range: [Date, Date]) => {
  emit('dateRangeChange', range)
}

// 导出趋势数据
const exportTrendData = () => {
  emit('exportData', trendType.value, dateRange.value)
  ElMessage.success('数据导出中...')
}

// 获取变化样式类
const getChangeClass = (value: number) => {
  if (value > 0) return 'change-positive'
  if (value < 0) return 'change-negative'
  return 'change-neutral'
}

// 获取趋势类型文本
const getTrendTypeText = (type: string) => {
  const typeTexts: Record<string, string> = {
    'execution': '测试执行',
    'defects': '缺陷发现',
    'coverage': '覆盖率变化',
    'quality': '质量指标'
  }
  return typeTexts[type] || type
}

// 获取趋势类型单位
const getTrendTypeUnit = (type: string) => {
  const typeUnits: Record<string, string> = {
    'execution': '执行次数',
    'defects': '缺陷数量',
    'coverage': '覆盖率(%)',
    'quality': '质量分数'
  }
  return typeUnits[type] || ''
}

onMounted(() => {
  showDetails.value = true
})
</script>

<style scoped>
.trend-analysis-chart {
  width: 100%;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.trend-container {
  height: 500px;
  margin-bottom: 20px;
}

.trend-summary {
  margin-bottom: 20px;
}

.summary-card {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  height: 100%;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  font-weight: bold;
  color: #333;
}

.summary-header .el-icon {
  font-size: 18px;
}

.trend-up {
  color: #409EFF;
}

.prediction {
  color: #67C23A;
}

.recommendation {
  color: #E6A23C;
}

.summary-content {
  color: #666;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
}

.trend-indicator.up {
  color: #67C23A;
}

.trend-indicator.down {
  color: #F56C6C;
}

.trend-indicator.stable {
  color: #909399;
}

.trend-description {
  font-size: 14px;
  line-height: 1.4;
}

.prediction-value {
  font-size: 20px;
  font-weight: bold;
  color: #67C23A;
  margin-bottom: 8px;
}

.prediction-description {
  font-size: 14px;
  line-height: 1.4;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recommendation-item {
  font-size: 14px;
  line-height: 1.4;
  padding-left: 15px;
  position: relative;
}

.recommendation-item::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #E6A23C;
}

.trend-details {
  margin-bottom: 20px;
}

.change-positive {
  color: #67C23A;
  font-weight: bold;
}

.change-negative {
  color: #F56C6C;
  font-weight: bold;
}

.change-neutral {
  color: #909399;
}
</style>