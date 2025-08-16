<template>
  <div class="coverage-heatmap">
    <el-card>
      <template #header>
        <div class="heatmap-header">
          <span>{{ title }}</span>
          <div class="header-controls">
            <el-select v-model="viewMode" size="small" style="width: 120px;">
              <el-option label="模块视图" value="module" />
              <el-option label="功能视图" value="function" />
              <el-option label="优先级视图" value="priority" />
            </el-select>
            <el-button size="small" @click="refreshData">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <div class="heatmap-container">
        <v-chart 
          :option="heatmapOption" 
          :loading="loading"
          @click="handleCellClick"
        />
      </div>

      <!-- 覆盖率统计 -->
      <div class="coverage-stats">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #67C23A;">
                <el-icon><SuccessFilled /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ coverageStats.high_coverage }}%</div>
                <div class="stat-label">高覆盖率区域</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #E6A23C;">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ coverageStats.medium_coverage }}%</div>
                <div class="stat-label">中等覆盖率区域</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #F56C6C;">
                <el-icon><CircleCloseFilled /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ coverageStats.low_coverage }}%</div>
                <div class="stat-label">低覆盖率区域</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #409EFF;">
                <el-icon><InfoFilled /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ coverageStats.overall }}%</div>
                <div class="stat-label">总体覆盖率</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 覆盖率详情表格 -->
      <div class="coverage-details" v-if="showDetails">
        <el-table :data="coverageDetails" size="small" max-height="300">
          <el-table-column prop="name" label="名称" width="200" />
          <el-table-column prop="coverage" label="覆盖率" width="100">
            <template #default="{ row }">
              <el-progress 
                :percentage="row.coverage" 
                :color="getCoverageColor(row.coverage)"
                :show-text="false"
                style="width: 80px;"
              />
              <span style="margin-left: 10px;">{{ row.coverage }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="covered_cases" label="已覆盖用例" width="120" />
          <el-table-column prop="total_cases" label="总用例数" width="100" />
          <el-table-column prop="missing_areas" label="缺失区域" show-overflow-tooltip />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="text" @click="viewDetails(row)">
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 图例 -->
      <div class="heatmap-legend">
        <span class="legend-title">覆盖率:</span>
        <div class="legend-items">
          <div class="legend-item">
            <div class="legend-color" style="background: #ff4d4f;"></div>
            <span>0-30%</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #ff7a45;"></div>
            <span>30-50%</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #ffa940;"></div>
            <span>50-70%</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #52c41a;"></div>
            <span>70-90%</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #389e0d;"></div>
            <span>90-100%</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, 
  SuccessFilled, 
  WarningFilled, 
  CircleCloseFilled, 
  InfoFilled 
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  HeatmapChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent
])

interface CoverageData {
  name: string
  category: string
  coverage: number
  covered_cases: number
  total_cases: number
  missing_areas: string[]
}

interface CoverageStats {
  overall: number
  high_coverage: number
  medium_coverage: number
  low_coverage: number
}

const props = defineProps<{
  title?: string
  data: CoverageData[]
  loading?: boolean
}>()

const emit = defineEmits<{
  cellClick: [data: CoverageData]
  detailView: [data: CoverageData]
}>()

const viewMode = ref<'module' | 'function' | 'priority'>('module')
const showDetails = ref(false)

// 计算覆盖率统计
const coverageStats = computed<CoverageStats>(() => {
  if (props.data.length === 0) {
    return { overall: 0, high_coverage: 0, medium_coverage: 0, low_coverage: 0 }
  }

  const totalCoverage = props.data.reduce((sum, item) => sum + item.coverage, 0)
  const overall = Math.round(totalCoverage / props.data.length)

  const highCount = props.data.filter(item => item.coverage >= 70).length
  const mediumCount = props.data.filter(item => item.coverage >= 30 && item.coverage < 70).length
  const lowCount = props.data.filter(item => item.coverage < 30).length

  return {
    overall,
    high_coverage: Math.round((highCount / props.data.length) * 100),
    medium_coverage: Math.round((mediumCount / props.data.length) * 100),
    low_coverage: Math.round((lowCount / props.data.length) * 100)
  }
})

// 覆盖率详情数据
const coverageDetails = computed(() => {
  return props.data.map(item => ({
    ...item,
    missing_areas: item.missing_areas.join(', ')
  }))
})

// 热力图数据处理
const heatmapData = computed(() => {
  // 根据视图模式分组数据
  const groupedData = groupDataByViewMode(props.data, viewMode.value)
  
  // 转换为热力图格式 [x, y, value]
  const data: [number, number, number][] = []
  const xAxisData: string[] = []
  const yAxisData: string[] = []

  // 构建坐标轴数据
  const categories = [...new Set(groupedData.map(item => item.category))]
  const names = [...new Set(groupedData.map(item => item.name))]

  categories.forEach((category, categoryIndex) => {
    if (!yAxisData.includes(category)) {
      yAxisData.push(category)
    }
  })

  names.forEach((name, nameIndex) => {
    if (!xAxisData.includes(name)) {
      xAxisData.push(name)
    }
  })

  // 构建热力图数据
  groupedData.forEach(item => {
    const xIndex = xAxisData.indexOf(item.name)
    const yIndex = yAxisData.indexOf(item.category)
    if (xIndex !== -1 && yIndex !== -1) {
      data.push([xIndex, yIndex, item.coverage])
    }
  })

  return {
    data,
    xAxisData,
    yAxisData
  }
})

// 热力图配置
const heatmapOption = computed(() => {
  const { data, xAxisData, yAxisData } = heatmapData.value

  return {
    title: {
      text: `${getViewModeText(viewMode.value)}覆盖率热力图`,
      left: 'center'
    },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [x, y, value] = params.data
        return `${yAxisData[y]} - ${xAxisData[x]}<br/>覆盖率: ${value}%`
      }
    },
    grid: {
      height: '60%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      splitArea: {
        show: true
      },
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#ff4d4f', '#ff7a45', '#ffa940', '#52c41a', '#389e0d']
      }
    },
    series: [{
      name: '覆盖率',
      type: 'heatmap',
      data: data,
      label: {
        show: true,
        formatter: '{c}%'
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})

// 根据视图模式分组数据
const groupDataByViewMode = (data: CoverageData[], mode: string) => {
  // 这里可以根据不同的视图模式对数据进行不同的分组处理
  return data
}

// 处理单元格点击
const handleCellClick = (params: any) => {
  const { data, xAxisData, yAxisData } = heatmapData.value
  const [x, y] = params.data
  
  const item = props.data.find(d => 
    d.name === xAxisData[x] && d.category === yAxisData[y]
  )
  
  if (item) {
    emit('cellClick', item)
  }
}

// 查看详情
const viewDetails = (row: CoverageData) => {
  emit('detailView', row)
}

// 刷新数据
const refreshData = () => {
  // 触发父组件刷新数据
  ElMessage.success('数据已刷新')
}

// 获取覆盖率颜色
const getCoverageColor = (coverage: number) => {
  if (coverage >= 90) return '#389e0d'
  if (coverage >= 70) return '#52c41a'
  if (coverage >= 50) return '#ffa940'
  if (coverage >= 30) return '#ff7a45'
  return '#ff4d4f'
}

// 获取视图模式文本
const getViewModeText = (mode: string) => {
  const modeTexts: Record<string, string> = {
    'module': '模块',
    'function': '功能',
    'priority': '优先级'
  }
  return modeTexts[mode] || mode
}

// 监听视图模式变化
watch(viewMode, () => {
  showDetails.value = false
})

onMounted(() => {
  showDetails.value = true
})
</script>

<style scoped>
.coverage-heatmap {
  width: 100%;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.heatmap-container {
  height: 500px;
  margin-bottom: 20px;
}

.coverage-stats {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.coverage-details {
  margin-bottom: 20px;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.legend-title {
  font-weight: bold;
  color: #333;
}

.legend-items {
  display: flex;
  gap: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}
</style>