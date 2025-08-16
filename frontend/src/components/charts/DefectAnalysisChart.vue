<template>
  <div class="defect-analysis-chart">
    <el-card>
      <template #header>
        <div class="chart-header">
          <span>{{ title }}</span>
          <el-button-group size="small">
            <el-button 
              :type="chartType === 'distribution' ? 'primary' : ''" 
              @click="chartType = 'distribution'"
            >
              分布图
            </el-button>
            <el-button 
              :type="chartType === 'trend' ? 'primary' : ''" 
              @click="chartType = 'trend'"
            >
              趋势图
            </el-button>
            <el-button 
              :type="chartType === 'severity' ? 'primary' : ''" 
              @click="chartType = 'severity'"
            >
              严重程度
            </el-button>
          </el-button-group>
        </div>
      </template>
      
      <div class="chart-container">
        <v-chart 
          :option="currentChartOption" 
          :loading="loading"
          @click="handleChartClick"
        />
      </div>
      
      <!-- 统计信息 -->
      <div class="stats-summary" v-if="defectStats">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ defectStats.total }}</div>
              <div class="stat-label">总缺陷数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value critical">{{ defectStats.critical }}</div>
              <div class="stat-label">严重缺陷</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ defectStats.resolved }}</div>
              <div class="stat-label">已解决</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ defectStats.resolution_rate }}%</div>
              <div class="stat-label">解决率</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  BarChart,
  LineChart,
  PieChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

interface DefectData {
  id: number
  type: string
  severity: string
  status: string
  detected_at: string
  resolved_at?: string
  description: string
}

interface DefectStats {
  total: number
  critical: number
  resolved: number
  resolution_rate: number
}

const props = defineProps<{
  title?: string
  data: DefectData[]
  loading?: boolean
}>()

const emit = defineEmits<{
  defectClick: [defect: DefectData]
}>()

const chartType = ref<'distribution' | 'trend' | 'severity'>('distribution')

// 计算缺陷统计信息
const defectStats = computed<DefectStats>(() => {
  const total = props.data.length
  const critical = props.data.filter(d => d.severity === 'critical').length
  const resolved = props.data.filter(d => d.status === 'resolved').length
  const resolution_rate = total > 0 ? Math.round((resolved / total) * 100) : 0

  return {
    total,
    critical,
    resolved,
    resolution_rate
  }
})

// 缺陷分布图配置
const distributionOption = computed(() => {
  const typeGroups = props.data.reduce((acc, defect) => {
    acc[defect.type] = (acc[defect.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return {
    title: {
      text: '缺陷类型分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      name: '缺陷类型',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 20,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: Object.entries(typeGroups).map(([name, value]) => ({
        name: getDefectTypeText(name),
        value
      }))
    }]
  }
})

// 缺陷趋势图配置
const trendOption = computed(() => {
  // 按日期分组统计
  const dateGroups = props.data.reduce((acc, defect) => {
    const date = new Date(defect.detected_at).toLocaleDateString('zh-CN')
    acc[date] = (acc[date] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const sortedDates = Object.keys(dateGroups).sort((a, b) => 
    new Date(a).getTime() - new Date(b).getTime()
  )

  return {
    title: {
      text: '缺陷发现趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: sortedDates,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '缺陷数量'
    },
    series: [{
      name: '新发现缺陷',
      type: 'line',
      data: sortedDates.map(date => dateGroups[date]),
      smooth: true,
      itemStyle: {
        color: '#F56C6C'
      },
      areaStyle: {
        opacity: 0.3
      }
    }]
  }
})

// 严重程度分析图配置
const severityOption = computed(() => {
  const severityGroups = props.data.reduce((acc, defect) => {
    acc[defect.severity] = (acc[defect.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const severityOrder = ['low', 'medium', 'high', 'critical']
  const colors = ['#67C23A', '#E6A23C', '#F56C6C', '#909399']

  return {
    title: {
      text: '缺陷严重程度分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: severityOrder.map(s => getSeverityText(s))
    },
    yAxis: {
      type: 'value',
      name: '缺陷数量'
    },
    series: [{
      name: '缺陷数量',
      type: 'bar',
      data: severityOrder.map((severity, index) => ({
        value: severityGroups[severity] || 0,
        itemStyle: {
          color: colors[index]
        }
      })),
      barWidth: '60%'
    }]
  }
})

// 当前图表配置
const currentChartOption = computed(() => {
  switch (chartType.value) {
    case 'distribution':
      return distributionOption.value
    case 'trend':
      return trendOption.value
    case 'severity':
      return severityOption.value
    default:
      return distributionOption.value
  }
})

// 处理图表点击事件
const handleChartClick = (params: any) => {
  // 根据图表类型处理点击事件
  if (chartType.value === 'distribution') {
    const defectType = Object.keys(props.data.reduce((acc, defect) => {
      acc[defect.type] = true
      return acc
    }, {} as Record<string, boolean>))[params.dataIndex]
    
    const defect = props.data.find(d => d.type === defectType)
    if (defect) {
      emit('defectClick', defect)
    }
  }
}

// 辅助函数
const getDefectTypeText = (type: string): string => {
  const typeTexts: Record<string, string> = {
    'functional': '功能缺陷',
    'performance': '性能缺陷',
    'security': '安全缺陷',
    'usability': '易用性缺陷',
    'compatibility': '兼容性缺陷'
  }
  return typeTexts[type] || type
}

const getSeverityText = (severity: string): string => {
  const severityTexts: Record<string, string> = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'critical': '严重'
  }
  return severityTexts[severity] || severity
}
</script>

<style scoped>
.defect-analysis-chart {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 400px;
  margin-bottom: 20px;
}

.stats-summary {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.stat-value.critical {
  color: #F56C6C;
}

.stat-label {
  font-size: 14px;
  color: #666;
}
</style>